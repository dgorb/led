import json
import logging
import os
import threading

from .colors import BLACK, normalize_hex, parse_hex, to_hex
from .effects import (
    EFFECTS,
    FLASHING,
    build_effect_mode,
    fade_loop,
    parse_period,
    rainbow_loop,
    transition,
)

log = logging.getLogger(__name__)

FRAME_TIME = 1 / 60
FADE_TIME = 1.2
DEFAULT_MODE = {"type": "static", "color": "#ff9329"}


class LEDStrip:
    """Owns the hardware. All changes run through one animation thread."""

    def __init__(self, driver, gamma=2.8, state_file=None):
        self._driver = driver
        self._gamma = gamma
        self._state_file = state_file
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._current = BLACK
        self._on = False
        self._mode = dict(DEFAULT_MODE)

    # -- public API -------------------------------------------------------

    def restore(self):
        """Load the last saved state and resume it."""
        saved = self._load()
        with self._lock:
            if saved:
                self._mode = saved["mode"]
                self._on = saved["on"]
            if self._on:
                self._start_mode(fade_in=True)
            else:
                self._apply(BLACK)

    def state(self):
        with self._lock:
            return {
                "on": self._on,
                "mode": dict(self._mode),
                "color": to_hex(self._current),
                "mock": getattr(self._driver, "mock", False),
            }

    def set_color(self, color):
        rgb = parse_hex(color)
        with self._lock:
            self._halt()
            self._mode = {"type": "static", "color": to_hex(rgb)}
            self._on = True
            self._apply(rgb)
            self._save()

    def set_power(self, on):
        with self._lock:
            if bool(on) == self._on:
                return
            self._on = bool(on)
            self._halt()
            if self._on:
                self._start_mode(fade_in=True)
            else:
                self._run(transition(self._current, BLACK, FADE_TIME))
            self._save()

    def set_fade(self, start, end, period):
        mode = {
            "type": "fade",
            "colors": [normalize_hex(start), normalize_hex(end)],
            "period": parse_period(period),
        }
        self._set_mode(mode)

    def set_effect(self, name, rate=None, glitch=None, norway=None):
        self._set_mode(build_effect_mode(name, rate, glitch, norway))

    def set_rainbow(self, period):
        self._set_mode({"type": "rainbow", "period": parse_period(period)})

    def close(self):
        with self._lock:
            self._halt()
            self._driver.close()

    # -- internals --------------------------------------------------------

    def _set_mode(self, mode):
        with self._lock:
            self._halt()
            self._mode = mode
            self._on = True
            self._start_mode()
            self._save()

    def _start_mode(self, fade_in=False):
        mode = self._mode
        if mode["type"] == "static":
            target = parse_hex(mode["color"])
            if fade_in:
                self._run(transition(self._current, target, FADE_TIME))
            else:
                self._apply(target)
        elif mode["type"] == "fade":
            a, b = (parse_hex(c) for c in mode["colors"])
            self._run(self._chain(transition(self._current, a, 0.5), fade_loop(a, b, mode["period"])))
        elif mode["type"] == "effect":
            self._run(EFFECTS[mode["name"]](mode))
        elif mode["type"] == "rainbow":
            self._run(rainbow_loop(mode["period"]))

    @staticmethod
    def _chain(*gens):
        for gen in gens:
            yield from gen

    def _run(self, frames):
        stop = threading.Event()
        self._stop = stop
        self._thread = threading.Thread(target=self._loop, args=(frames, stop), daemon=True)
        self._thread.start()

    def _loop(self, frames, stop):
        for rgb in frames:
            if stop.is_set():
                return
            self._apply(rgb)
            if stop.wait(FRAME_TIME):
                return

    def _halt(self):
        self._stop.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
        self._thread = None

    def _apply(self, rgb):
        self._current = rgb
        self._driver.write([(max(0.0, min(255.0, c)) / 255) ** self._gamma for c in rgb])

    def _save(self):
        if not self._state_file:
            return
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._state_file.with_suffix(".tmp")
            mode = self._mode
            if mode["type"] == "effect" and mode["name"] in FLASHING:
                mode = DEFAULT_MODE  # never resume flashing by surprise after a restart
            tmp.write_text(json.dumps({"on": self._on, "mode": mode}))
            os.replace(tmp, self._state_file)
        except OSError:
            log.exception("Could not save state")

    def _load(self):
        if not self._state_file or not self._state_file.exists():
            return None
        try:
            data = json.loads(self._state_file.read_text())
            if data["mode"]["type"] not in ("static", "fade", "rainbow", "effect"):
                raise ValueError("unknown mode")
            if data["mode"]["type"] == "effect" and data["mode"]["name"] not in EFFECTS:
                raise ValueError("unknown effect")
            return {"on": bool(data["on"]), "mode": data["mode"]}
        except (OSError, ValueError, KeyError, TypeError):
            log.warning("Ignoring unreadable state file %s", self._state_file)
            return None

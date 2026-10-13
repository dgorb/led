import json
import logging
import math
import os
import random
import threading
import time

from .colors import hsv_to_rgb, lerp, normalize_hex, parse_hex, to_hex

log = logging.getLogger(__name__)

FRAME_TIME = 1 / 60
FADE_TIME = 1.2
MIN_PERIOD = 0.5
MAX_PERIOD = 600
BLACK = (0.0, 0.0, 0.0)
DEFAULT_MODE = {"type": "static", "color": "#ff9329"}


def transition(a, b, duration):
    start = time.monotonic()
    while True:
        k = (time.monotonic() - start) / duration
        if k >= 1:
            yield b
            return
        yield lerp(a, b, k)


def fade_loop(a, b, period):
    """Ease back and forth between a and b; `period` is seconds for one way."""
    start = time.monotonic()
    while True:
        phase = ((time.monotonic() - start) / period) % 2
        k = phase if phase <= 1 else 2 - phase
        yield lerp(a, b, (1 - math.cos(math.pi * k)) / 2)


def candle_loop():
    """Warm flame: smoothed random brightness with occasional deeper dips.

    Dimmer also means redder, like a real flame.
    """
    dim, bright = (175.0, 62.0, 8.0), (255.0, 140.0, 35.0)
    rng = random.Random()
    level = target = 0.8
    next_change = 0.0
    last = time.monotonic()
    while True:
        now = time.monotonic()
        dt, last = now - last, now
        if now >= next_change:
            low = 0.45 if rng.random() < 0.1 else 0.65
            target = rng.uniform(low, 1.0)
            next_change = now + rng.uniform(0.15, 0.6)
        level += (target - level) * min(1.0, dt * 4)
        yield lerp(dim, bright, level)


EFFECTS = {
    "candle": lambda mode: candle_loop(),
    "strobe": lambda mode: strobe_loop(mode["rate"]),
    "pigs": lambda mode: pigs_loop(),
}

# Effects that flash hard enough that they should never resume on their own after a restart.
FLASHING = ("strobe", "pigs")

MIN_STROBE_HZ = 1
MAX_STROBE_HZ = 10
DEFAULT_STROBE_HZ = 4


def strobe_loop(rate, duty=0.2):
    """Short white flashes, `rate` per second."""
    white = (255.0, 255.0, 255.0)
    start = time.monotonic()
    while True:
        phase = ((time.monotonic() - start) * rate) % 1
        yield white if phase < duty else BLACK


def pigs_loop():
    """Double red flash, then double blue flash, repeating."""
    red, blue = (255.0, 0.0, 0.0), (0.0, 0.0, 255.0)
    pattern = []
    for color in (red, blue):
        pattern += [(color, 0.10), (BLACK, 0.07)] * 2
    total = sum(d for _, d in pattern)
    start = time.monotonic()
    while True:
        t = (time.monotonic() - start) % total
        for color, duration in pattern:
            if t < duration:
                yield color
                break
            t -= duration
        else:
            yield BLACK


def _strobe_rate(value):
    try:
        rate = float(value)
    except (TypeError, ValueError):
        raise ValueError("rate must be a number")
    if not MIN_STROBE_HZ <= rate <= MAX_STROBE_HZ:
        raise ValueError(f"rate must be between {MIN_STROBE_HZ} and {MAX_STROBE_HZ} flashes per second")
    return rate


def rainbow_loop(period):
    """Cycle through all hues; `period` is seconds per full cycle."""
    start = time.monotonic()
    while True:
        yield hsv_to_rgb((time.monotonic() - start) / period * 360, 1, 1)


def _period(value):
    try:
        period = float(value)
    except (TypeError, ValueError):
        raise ValueError("period must be a number")
    if not MIN_PERIOD <= period <= MAX_PERIOD:
        raise ValueError(f"period must be between {MIN_PERIOD} and {MAX_PERIOD} seconds")
    return period


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
            "period": _period(period),
        }
        self._set_mode(mode)

    def set_effect(self, name, rate=None):
        if name not in EFFECTS:
            raise ValueError(f"unknown effect {name!r}, expected one of: {', '.join(EFFECTS)}")
        mode = {"type": "effect", "name": name}
        if name == "strobe":
            mode["rate"] = _strobe_rate(DEFAULT_STROBE_HZ if rate is None else rate)
        self._set_mode(mode)

    def set_rainbow(self, period):
        self._set_mode({"type": "rainbow", "period": _period(period)})

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

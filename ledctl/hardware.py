import logging
import threading
import time

log = logging.getLogger(__name__)

DEFAULT_PWM_FREQ = 200


class MockDriver:
    """Stand-in used when not running on a Pi (LED_MOCK=1)."""

    mock = True

    def __init__(self, pins):
        self.pins = pins
        self.levels = (0.0,) * len(pins)

    def write(self, levels):
        self.levels = tuple(levels)

    def close(self):
        pass


class PigpioDriver:
    """Drives the strip's R, G, B channels through the pigpio daemon.

    pigpio's PWM resolution is set by its frequency: with the default 5 us
    sample rate, 800 Hz gives only 250 steps and 200 Hz gives 1000. Gamma
    correction squeezes dark colors into the first few steps, so we use a lower
    frequency for more steps.

    Even 1000 steps is coarse for the darkest channels, so a small thread
    dithers: once per PWM cycle it picks the duty just above or below the
    wanted level, carrying the rounding error forward. Updating at the PWM rate
    (not at the animation's 60 fps) keeps the resulting flicker too fast to see.
    """

    mock = False

    def __init__(self, pins, pwm_freq=DEFAULT_PWM_FREQ, threaded=True):
        import pigpio

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError(
                "Cannot connect to pigpiod. Start it with `sudo systemctl enable --now pigpiod`, "
                "or set LED_MOCK=1 to run without hardware."
            )
        self.pins = pins
        self._range = None
        for pin in pins:
            self._pi.set_PWM_frequency(pin, pwm_freq)
            real = self._pi.get_PWM_real_range(pin)
            self._pi.set_PWM_range(pin, real)
            self._range = real if self._range is None else min(self._range, real)
        actual_freq = self._pi.get_PWM_frequency(pins[0])
        log.info("PWM %s Hz, %s steps per channel", actual_freq, self._range)

        self._lock = threading.Lock()
        self._target = [0.0] * len(pins)  # wanted duty, in (fractional) steps
        self._error = [0.0] * len(pins)
        self._duty = [None] * len(pins)  # what pigpio currently has
        self._stop = threading.Event()
        self._interval = 1.0 / max(actual_freq, 1)
        self._thread = None
        if threaded:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def write(self, levels):
        """levels: one brightness per pin, 0.0..1.0 (already gamma corrected)."""
        with self._lock:
            self._target = [max(0.0, min(1.0, level)) * self._range for level in levels]

    def _tick(self):
        """One dithering step. Returns the duty written for each pin."""
        with self._lock:
            target = list(self._target)
        for i, pin in enumerate(self.pins):
            wanted = target[i] + self._error[i]
            duty = max(0, min(self._range, round(wanted)))
            self._error[i] = max(-1.0, min(1.0, wanted - duty))
            if duty != self._duty[i]:
                self._pi.set_PWM_dutycycle(pin, duty)
                self._duty[i] = duty
        return list(self._duty)

    def _run(self):
        failing = False
        next_tick = time.monotonic()
        while not self._stop.is_set():
            try:
                self._tick()
                if failing:
                    log.info("Talking to pigpiod again")
                    failing = False
            except Exception:
                if not failing:
                    log.exception("Lost contact with pigpiod; retrying")
                    failing = True
            next_tick += self._interval
            delay = next_tick - time.monotonic()
            if delay < 0:  # fell behind, do not try to catch up in a burst
                next_tick = time.monotonic()
                delay = 0
            self._stop.wait(delay)

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        for pin in self.pins:
            self._pi.set_PWM_dutycycle(pin, 0)
        self._pi.stop()


def create_driver(pins, mock=False, pwm_freq=DEFAULT_PWM_FREQ):
    if mock:
        log.warning("Running with mock LED driver")
        return MockDriver(pins)
    return PigpioDriver(pins, pwm_freq)

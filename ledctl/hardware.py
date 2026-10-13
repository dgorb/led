import logging

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
    frequency for more steps, and dither (spread the rounding error over
    successive frames) so slow fades through dark colors look smooth.
    """

    mock = False

    def __init__(self, pins, pwm_freq=DEFAULT_PWM_FREQ):
        import pigpio

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError(
                "Cannot connect to pigpiod. Start it with `sudo systemctl enable --now pigpiod`, "
                "or set LED_MOCK=1 to run without hardware."
            )
        self.pins = pins
        self._error = [0.0] * len(pins)
        self._range = None
        for pin in pins:
            self._pi.set_PWM_frequency(pin, pwm_freq)
            real = self._pi.get_PWM_real_range(pin)
            self._pi.set_PWM_range(pin, real)
            self._range = real if self._range is None else min(self._range, real)
        log.info("PWM %s Hz, %s steps per channel", self._pi.get_PWM_frequency(pins[0]), self._range)

    def write(self, levels):
        """levels: one brightness per pin, 0.0..1.0 (already gamma corrected)."""
        for i, (pin, level) in enumerate(zip(self.pins, levels)):
            wanted = level * self._range + self._error[i]
            duty = max(0, min(self._range, round(wanted)))
            self._error[i] = max(-1.0, min(1.0, wanted - duty))
            self._pi.set_PWM_dutycycle(pin, duty)

    def close(self):
        for pin in self.pins:
            self._pi.set_PWM_dutycycle(pin, 0)
        self._pi.stop()


def create_driver(pins, mock=False, pwm_freq=DEFAULT_PWM_FREQ):
    if mock:
        log.warning("Running with mock LED driver")
        return MockDriver(pins)
    return PigpioDriver(pins, pwm_freq)

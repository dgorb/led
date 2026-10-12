import logging

log = logging.getLogger(__name__)

PWM_RANGE = 1000


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
    """Drives the strip's R, G, B channels through the pigpio daemon."""

    mock = False

    def __init__(self, pins):
        import pigpio

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError(
                "Cannot connect to pigpiod. Start it with `sudo systemctl enable --now pigpiod`, "
                "or set LED_MOCK=1 to run without hardware."
            )
        self.pins = pins
        for pin in pins:
            self._pi.set_PWM_range(pin, PWM_RANGE)

    def write(self, levels):
        """levels: one brightness per pin, 0.0..1.0 (already gamma corrected)."""
        for pin, level in zip(self.pins, levels):
            self._pi.set_PWM_dutycycle(pin, round(level * PWM_RANGE))

    def close(self):
        for pin in self.pins:
            self._pi.set_PWM_dutycycle(pin, 0)
        self._pi.stop()


def create_driver(pins, mock=False):
    if mock:
        log.warning("Running with mock LED driver")
        return MockDriver(pins)
    return PigpioDriver(pins)

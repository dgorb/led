import time
from led import LEDStrip

def main():
    led_strip = LEDStrip(0, 0, 0)

    led_strip.shift(
        (255, 231, 230),
        (54, 0, 220),
        1,
        True
    )

    time.sleep(10)
    led_strip.ctr.stop_all()

main()

import time
from led import LEDStrip

def main():
    led_strip = LEDStrip(0, 0, 0)

    led_strip.shift(
        (255, 0, 230),
        (54, 231, 255),
        1,
        True
    )

    time.sleep(5)
    led_strip.ctr.stop_all()
    print(f"Stopped at ({led_strip.r.intensity}, {led_strip.g.intensity}, {led_strip.b.intensity})")

main()

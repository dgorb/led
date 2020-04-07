import argparse
import time

from led import LEDStrip

def main():
    led_strip = LEDStrip(2, 120, 189)
    led_strip.shift(
        (189, 61, 2),
        (2, 189, 46),
        1,
        True
    )
    #led_strip.set_color(152, 189, 2)
    #led_strip.pi.stop()

    time.sleep(5)
    led_strip.off()


main()

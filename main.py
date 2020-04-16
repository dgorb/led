import argparse
import time

from led import LEDStrip

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', help="Set color (RGB), e.g. 100,50,100")
    parser.add_argument('--shift-start', help="Shift from color (RGB), e.g. 100,50,100")
    parser.add_argument('--shift-end', help="Shift to color (RGB), e.g. 140,250,30")
    parser.add_argument('--shift-cont', action='store_true', help="Continuous shifting, otherwise shift once", default=False)
    parser.add_argument('--shift-period', help="Shifting period (seconds)", default=1)

    args = parser.parse_args()

    if args.shift_start and args.shift_end:
        start_color = [int(c) for c in args.shift_start.rstrip().split(',')]
        end_color = [int(c) for c in args.shift_end.rstrip().split(',')]

        led_strip = LEDStrip(*start_color)
        led_strip.shift(start_color, end_color, int(args.shift_period), args.shift_cont)

    elif args.color:
        color = [int(c) for c in args.color.split(',')]
        led_strip = LEDStrip(*color)

main()

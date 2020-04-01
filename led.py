import time
import threading

from colr import Colr
from controller import Controller

class LEDStrip:
    def __init__(self, r, g, b):
        self.ctr = Controller()
        self.r = Pin(self.ctr, 'r', r)
        self.g = Pin(self.ctr, 'g', g)
        self.b = Pin(self.ctr, 'b', b)

    def set_color(self, r, g, b):
        self.r.set_intensity(r)
        self.g.set_intensity(g)
        self.b.set_intensity(b)

    # min/max: e.g. Tuple(255, 255, 255)
    def shift(self, min, max, duration, cont=False):
        min_r = min[0]
        max_r = max[0]
        min_g = min[1]
        max_g = max[1]
        min_b = min[2]
        max_b = max[2]

        self.ctr.add('r', self.r.shift, min_r, max_r, duration, cont)
        self.ctr.add('g', self.g.shift, min_g, max_g, duration, cont)
        self.ctr.add('b', self.b.shift, min_b, max_b, duration, cont)
        self.ctr.add('log', self._print_colors)

        self.ctr.start_all()

    def _print_colors(self):
        # FIXME: mess
        while not (
            self.ctr.get_thread('r').stopped() and
            self.ctr.get_thread('g').stopped() and
            self.ctr.get_thread('b').stopped()):
            print(Colr().rgb(self.r.intensity, self.g.intensity, self.b.intensity, f"R: {self.r.intensity} G: {self.g.intensity} B: {self.b.intensity}"), end="\r", flush=True)
        self.ctr.get_thread('log').stop()

class Pin:
    def __init__(self, ctr, color, intensity):
        self.ctr = ctr
        self.color = color
        self.intensity = intensity

        # Consts
        self.SHIFT_STEP = 1

    def set_intensity(self, intensity):
        self.intensity = intensity

    def full_on(self):
        self.intensity = 255

    def full_off(self):
        self.intensity = 0

    # start & end are color values between 0-255
    # Shift from min to max within duration period
    # If cont=True, go back and forth between min and max colors
    def shift(self, start, end, duration, cont=False):
        self.intensity = start

        if end > start:
            delay = duration / (end - start)
            incresing = True
        else:
            delay = duration / (start - end)
            incresing = False

            temp_start = start
            start = end
            end = temp_start

        while True:
            if start > end:
                temp_start = start
                start = end
                end = temp_start
            if self.intensity <= end and incresing:
                self.intensity += self.SHIFT_STEP
                if self.intensity == end:
                    incresing = False
                    if not cont or self.ctr.get_thread(self.color).stopped():
                        break
            elif self.intensity >= start and not incresing:
                self.intensity -= self.SHIFT_STEP
                if self.intensity == start:
                    incresing = True
                    if not cont or self.ctr.get_thread(self.color).stopped():
                        break

            time.sleep(delay)

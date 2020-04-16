import time
import threading
import pigpio
from colr import Colr
from controller import Controller

RED_PIN = 17
GREEN_PIN = 22
BLUE_PIN = 24

class LEDStrip:
    def __init__(self, r, g, b):
        self.ctr = Controller()
        self.pi = pigpio.pi()
        self.r = Pin(self.pi, RED_PIN, self.ctr, 'r', r)
        self.g = Pin(self.pi, GREEN_PIN, self.ctr, 'g', g)
        self.b = Pin(self.pi, BLUE_PIN, self.ctr, 'b', b)
        self.set_color(r, g, b)

    def set_color(self, r, g, b):
        self.r.set_intensity(r)
        self.g.set_intensity(g)
        self.b.set_intensity(b)

    def off(self):
        self.set_color(0, 0, 0)
        self.ctr.stop_all()

    # min/max: e.g. Tuple(255, 255, 255)
    def shift(self, min, max, duration, cont=False):
        print(f"Shifting between {min} and {max}, period={duration}s")
        min_r = min[0]
        max_r = max[0]
        min_g = min[1]
        max_g = max[1]
        min_b = min[2]
        max_b = max[2]

        self.ctr.add('r', self.r.shift, min_r, max_r, duration, cont)
        self.ctr.add('g', self.g.shift, min_g, max_g, duration, cont)
        self.ctr.add('b', self.b.shift, min_b, max_b, duration, cont)

        self.ctr.start_all()

    def _print_colors(self, verbose=False):
        # FIXME: mess
        while not (
            self.ctr.get_thread('r').stopped() and
            self.ctr.get_thread('g').stopped() and
            self.ctr.get_thread('b').stopped()):

            log_str = '#'
            end_str = ''
            if verbose:
                log_str = f"R: {self.r.intensity} G: {self.g.intensity} B: {self.b.intensity}"
                end_str = '\r'

            print(Colr().rgb(self.r.intensity, self.g.intensity, self.b.intensity, log_str), end=end_str, flush=True)
        self.ctr.get_thread('log').stop()

class Pin:
    def __init__(self, pi, pin, ctr, color, intensity):
        self.pi = pi
        self.pin = pin
        self.ctr = ctr
        self.color = color
        self.intensity = intensity

        # Consts
        self.SHIFT_STEP = 1
        self.GAMMA = 2.8

        self.gamma_correct = _gamma_correction_table(self.GAMMA)

    def set_intensity(self, intensity):
        self.intensity = intensity
        self.pi.set_PWM_dutycycle(self.pin, self.gamma_correct[intensity])

    def full_on(self):
        self.set_intensity(255)

    def full_off(self):
        self.set_intensity(0)

    def get_thread(self):
        return self.ctr.get_thread(self.color)

    # start & end are color values between 0-255
    # Shift from min to max within duration period
    # If cont=True, go back and forth between min and max colors
    def shift(self, start, end, duration, cont=False):
        self.set_intensity(start)

        if end > start:
            delay = duration / (end - start)
            incresing = True
        elif start > end:
            delay = duration / (start - end)
            incresing = False

            temp_start = start
            start = end
            end = temp_start

        while True and not self.ctr.get_thread(self.color).stopped():
            if self.ctr.all_waiting():
                self.ctr.cont_all()

            # Do not change intensity until other pins are done
            if self.ctr.waiting(self.color):
                continue

            # The intensity is already set, so just continue the loo
            # and wait for the other colors to be done shifting
            if start == end:
                self.ctr.get_thread(self.color).wait()
                continue

            if self.intensity <= end and incresing:
                self.set_intensity(self.intensity + self.SHIFT_STEP)
                if self.intensity == end:
                    time.sleep(0.5) # Stay at the max color for a bit
                    incresing = False
                    self.ctr.get_thread(self.color).wait()
                    if not cont:
                        self.ctr.stop(self.color)
                        break

            elif self.intensity >= start and not incresing:
                self.set_intensity(self.intensity - self.SHIFT_STEP)
                if self.intensity == start:
                    time.sleep(0.5) # Stay at the min color for a bit
                    incresing = True
                    self.ctr.get_thread(self.color).wait()
                    if not cont:
                        self.ctr.stop(self.color)
                        break

            time.sleep(delay)

# Generate a table of gamma-corrected colors
def _gamma_correction_table(gamma_factor=2.8):
    max_in = 255
    max_out = 255

    table = []

    for i in range(0, max_in + 1):
        c = ((i / max_in) ** gamma_factor) * max_out + 0.5
        table.append(int(c))

    return table

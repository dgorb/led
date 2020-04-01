# https://randomnerdtutorials.com/electronics-basics-how-do-rgb-leds-work/
# 3 "small LEDS" per LED (RGB)
# can controll brightness of each  "small LED" - get more colors
# PWM signal

# MOSFETS 
# Gate Threshold Voltage = 3.3V (for full brightness, rpi pins are 0 - 3.3V)
# Raspberry Pi turns MOSFET on and off, brightness depends on frequency (?)

# 4 pin used - 3 for colors, 1 for power
# Red pin, brightness 0-255
# Green pin, brightness 0-255
# Blue pin, brightness 0-255
# Power pin

# Use pigpio for controlling pins?


# ASSUMING THE LEDS ARE NOT ADDRESSABLE (SINGLE COLOR FOR THE WHOLE STRIP)
import time
import threading

from colr import Colr

class Pin:
    def __init__(self, color, intensity):
        self.color = color
        self.intensity = intensity
        self.shifting = False
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
        self.shifting = True

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
                    if not cont:
                        self.shifting = False
                        break
            elif self.intensity >= start and not incresing:
                self.intensity -= self.SHIFT_STEP
                if self.intensity == start:
                    incresing = True
                    if not cont:
                        self.shifting = False
                        break
            
            time.sleep(delay)
    
class LEDStrip:
    def __init__(self, r, g, b):
        self.r = Pin('R', r)
        self.g = Pin('G', g)
        self.b = Pin('B', b)

    def set_color(self, r, g, b):
        self.r.set_intensity(r)
        self.g.set_intensity(g)
        self.b.set_intensity(b)

    # min/max: e.g. (255, 255, 255)
    def shift(self, min, max, duration, cont=False):
        min_r = min[0]
        max_r = max[0]
        min_g = min[1]
        max_g = max[1]
        min_b = min[2]
        max_b = max[2]

        r_thread = threading.Thread(target=self.r.shift, args=(min_r, max_r, duration, cont))
        g_thread = threading.Thread(target=self.g.shift, args=(min_g, max_g, duration, cont))
        b_thread = threading.Thread(target=self.b.shift, args=(min_b, max_b, duration, cont))
        log_thread = threading.Thread(target=self._print_colors)

        r_thread.start()
        g_thread.start()
        b_thread.start()
        log_thread.start()

        if not self.r.shifting and not self.g.shifting and not self.b.shifting:
            r_thread.join()
            g_thread.join()
            b_thread.join()
            log_thread.join()
            return

    def _print_colors(self):
        while self.r.shifting or self.g.shifting or self.b.shifting:
            print(Colr().rgb(self.r.intensity, self.g.intensity, self.b.intensity, f"R: {self.r.intensity} G: {self.g.intensity} B: {self.b.intensity}"), end="\r", flush=True)

def main():
    led_strip = LEDStrip(0, 0, 0)

    led_strip.shift(
        (255, 255, 255),
        (0, 0, 0),
        10,
    )

main()
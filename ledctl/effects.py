"""Light effects.

Every effect is a generator that yields (r, g, b) tuples in 0..255, one per
animation frame. LEDStrip pulls from it at its own pace, so effects only
describe how the color changes over time.
"""
import math
import random
import time

from .colors import BLACK, hsv_to_rgb, lerp

MIN_PERIOD = 0.5
MAX_PERIOD = 600

MIN_STROBE_HZ = 1
MAX_STROBE_HZ = 10
DEFAULT_STROBE_HZ = 4

NEON = ((255.0, 0.0, 170.0), (0.0, 230.0, 255.0), (140.0, 40.0, 255.0))

AURORA = ((30.0, 255.0, 110.0), (0.0, 220.0, 190.0), (40.0, 120.0, 255.0), (150.0, 60.0, 255.0))

BACKROOMS = (235.0, 235.0, 150.0)

STORM_BASE = (25.0, 35.0, 75.0)
STORM_FLASH = (215.0, 225.0, 255.0)


def transition(a, b, duration):
    start = time.monotonic()
    while True:
        k = (time.monotonic() - start) / duration
        if k >= 1:
            yield b
            return
        yield lerp(a, b, k)


def fade_loop(a, b, period):
    """Ease back and forth between a and b; `period` is seconds for one way."""
    start = time.monotonic()
    while True:
        phase = ((time.monotonic() - start) / period) % 2
        k = phase if phase <= 1 else 2 - phase
        yield lerp(a, b, (1 - math.cos(math.pi * k)) / 2)


def candle_loop():
    """Warm flame: smoothed random brightness with occasional deeper dips.

    Dimmer also means redder, like a real flame.
    """
    dim, bright = (175.0, 62.0, 8.0), (255.0, 140.0, 35.0)
    rng = random.Random()
    level = target = 0.8
    next_change = 0.0
    last = time.monotonic()
    while True:
        now = time.monotonic()
        dt, last = now - last, now
        if now >= next_change:
            low = 0.45 if rng.random() < 0.1 else 0.65
            target = rng.uniform(low, 1.0)
            next_change = now + rng.uniform(0.15, 0.6)
        level += (target - level) * min(1.0, dt * 4)
        yield lerp(dim, bright, level)


def strobe_loop(rate, duty=0.2):
    """Short white flashes, `rate` per second."""
    white = (255.0, 255.0, 255.0)
    start = time.monotonic()
    while True:
        phase = ((time.monotonic() - start) * rate) % 1
        yield white if phase < duty else BLACK


def cyberpunk_loop(rng=None, glitch=True):
    """Neon base that drifts between magenta, cyan and purple, with random glitches.

    A glitch is a burst of a few very short frames: a different neon color,
    darkness, or a white flash, then back to the base color. With glitch=False
    only the slow color drift remains.
    """
    rng = rng or random.Random()
    now = time.monotonic()
    src, dst = rng.sample(NEON, 2)
    fade_start, fade_len = now, rng.uniform(4, 9)
    next_glitch = now + rng.uniform(0.5, 2.5)
    segments = []  # (until, color) for the glitch burst in progress
    while True:
        now = time.monotonic()
        if now >= fade_start + fade_len:
            src, dst = dst, rng.choice([c for c in NEON if c != dst])
            fade_start, fade_len = now, rng.uniform(4, 9)
        k = min(1.0, (now - fade_start) / fade_len)
        base = lerp(src, dst, k * k * (3 - 2 * k))

        while segments and now >= segments[0][0]:
            segments.pop(0)
        if glitch and not segments and now >= next_glitch:
            t = now
            for _ in range(rng.randint(2, 6)):
                t += rng.uniform(0.02, 0.09)
                segments.append((t, rng.choice((BLACK, (255.0, 255.0, 255.0), rng.choice(NEON)))))
                t += rng.uniform(0.02, 0.06)
                segments.append((t, base))
            next_glitch = t + rng.uniform(0.6, 3.0)
        yield segments[0][1] if segments else base


def aurora_loop(rng=None):
    """Slow northern lights: drifts along green, teal, blue and purple.

    Position and brightness each come from a few sine waves with unrelated
    periods, so the pattern takes ages to repeat and never looks cyclic.
    """
    rng = rng or random.Random()
    p = [rng.uniform(0, math.tau) for _ in range(4)]
    start = time.monotonic()
    last = len(AURORA) - 1
    while True:
        t = time.monotonic() - start
        pos = 0.5 + 0.5 * (0.6 * math.sin(t * 0.11 + p[0]) + 0.4 * math.sin(t * 0.047 + p[1]))
        glow = 0.85 + 0.15 * (0.6 * math.sin(t * 0.31 + p[2]) + 0.4 * math.sin(t * 0.13 + p[3]))
        x = min(max(pos, 0.0), 1.0) * last
        i = min(int(x), last - 1)
        color = lerp(AURORA[i], AURORA[i + 1], x - i)
        yield tuple(c * glow for c in color)


def thunderstorm_loop(rng=None):
    """Dim stormy blue-grey with the occasional lightning strike.

    A strike is one to three quick flashes that each fade out, so the sky
    flickers and then settles back to the base color.
    """
    rng = rng or random.Random()
    start = time.monotonic()
    next_strike = start + rng.uniform(2, 6)
    flashes = []  # (start_time, peak, decay_seconds)
    while True:
        now = time.monotonic()
        if now >= next_strike:
            t = now
            for _ in range(rng.choice((1, 1, 2, 3))):
                flashes.append((t, rng.uniform(0.6, 1.0), rng.uniform(0.08, 0.25)))
                t += rng.uniform(0.06, 0.2)
            next_strike = t + rng.uniform(3, 12)
        flashes = [f for f in flashes if now - f[0] < f[2] * 6]
        level = max((peak * math.exp(-(now - t0) / decay) for t0, peak, decay in flashes if now >= t0), default=0.0)
        breathe = 0.9 + 0.1 * math.sin((now - start) * 0.9)
        base = tuple(c * breathe for c in STORM_BASE)
        yield lerp(base, STORM_FLASH, min(level, 1.0))


def backrooms_loop(rng=None):
    """Harsh, sickly fluorescent light that never quite behaves.

    A constant faint buzz, regular short stutters, and now and then the tube
    dies for a moment and flickers back to life.
    """
    rng = rng or random.Random()
    now = time.monotonic()
    next_stutter = now + rng.uniform(2, 6)
    next_dropout = now + rng.uniform(15, 40)
    segments = []  # (until, brightness 0..1) for the flicker in progress
    while True:
        now = time.monotonic()
        while segments and now >= segments[0][0]:
            segments.pop(0)
        if not segments:
            if now >= next_dropout:
                t = now + rng.uniform(0.15, 0.4)
                segments.append((t, 0.04))
                for _ in range(rng.randint(2, 4)):
                    t += rng.uniform(0.03, 0.08)
                    segments.append((t, rng.uniform(0.5, 0.9)))
                    t += rng.uniform(0.02, 0.07)
                    segments.append((t, rng.uniform(0.05, 0.3)))
                next_dropout = t + rng.uniform(15, 45)
                next_stutter = max(next_stutter, t + 2)
            elif now >= next_stutter:
                t = now
                for _ in range(rng.randint(2, 5)):
                    t += rng.uniform(0.02, 0.07)
                    segments.append((t, rng.uniform(0.35, 0.65)))
                    t += rng.uniform(0.03, 0.09)
                    segments.append((t, 1.0))
                next_stutter = t + rng.uniform(3, 10)
        level = segments[0][1] if segments else 1.0
        buzz = 1.0 - rng.uniform(0, 0.03)
        yield tuple(c * level * buzz for c in BACKROOMS)


def pigs_loop(norway=False):
    """Double red flash, then double blue flash, repeating.

    In Norway mode only the blue flashes remain; the red half of the cycle is dark,
    so the rhythm stays the same.
    """
    red, blue = (255.0, 0.0, 0.0), (0.0, 0.0, 255.0)
    pattern = []
    for color in (BLACK if norway else red, blue):
        pattern += [(color, 0.10), (BLACK, 0.07)] * 2
    total = sum(d for _, d in pattern)
    start = time.monotonic()
    while True:
        t = (time.monotonic() - start) % total
        for color, duration in pattern:
            if t < duration:
                yield color
                break
            t -= duration
        else:
            yield BLACK


def parse_strobe_rate(value):
    try:
        rate = float(value)
    except (TypeError, ValueError):
        raise ValueError("rate must be a number")
    if not MIN_STROBE_HZ <= rate <= MAX_STROBE_HZ:
        raise ValueError(f"rate must be between {MIN_STROBE_HZ} and {MAX_STROBE_HZ} flashes per second")
    return rate


def rainbow_loop(period):
    """Cycle through all hues; `period` is seconds per full cycle."""
    start = time.monotonic()
    while True:
        yield hsv_to_rgb((time.monotonic() - start) / period * 360, 1, 1)


def parse_period(value):
    try:
        period = float(value)
    except (TypeError, ValueError):
        raise ValueError("period must be a number")
    if not MIN_PERIOD <= period <= MAX_PERIOD:
        raise ValueError(f"period must be between {MIN_PERIOD} and {MAX_PERIOD} seconds")
    return period


# Named effects selectable from the UI/API, calmest first. Each takes the saved mode dict.
EFFECTS = {
    "candle": lambda mode: candle_loop(),
    "aurora": lambda mode: aurora_loop(),
    "thunderstorm": lambda mode: thunderstorm_loop(),
    "cyberpunk": lambda mode: cyberpunk_loop(glitch=mode.get("glitch", True)),
    "backrooms": lambda mode: backrooms_loop(),
    "strobe": lambda mode: strobe_loop(mode["rate"]),
    "pigs": lambda mode: pigs_loop(norway=mode.get("norway", False)),
}

# Effects that flash hard enough that they should never resume on their own after a restart.
FLASHING = ("strobe", "pigs")


def build_effect_mode(name, rate=None, glitch=None, norway=None):
    """Validate a request for a named effect and return the mode dict to store."""
    if name not in EFFECTS:
        raise ValueError(f"unknown effect {name!r}, expected one of: {', '.join(EFFECTS)}")
    mode = {"type": "effect", "name": name}
    if name == "strobe":
        mode["rate"] = parse_strobe_rate(DEFAULT_STROBE_HZ if rate is None else rate)
    if name == "cyberpunk":
        if glitch is not None and not isinstance(glitch, bool):
            raise ValueError("glitch must be true or false")
        mode["glitch"] = True if glitch is None else glitch
    if name == "pigs":
        if norway is not None and not isinstance(norway, bool):
            raise ValueError("norway must be true or false")
        mode["norway"] = bool(norway)
    return mode

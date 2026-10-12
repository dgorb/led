import colorsys
import re

_HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def parse_hex(value):
    """'#ff8800' or 'ff8800' -> (255.0, 136.0, 0.0). Raises ValueError."""
    match = _HEX.match(value.strip()) if isinstance(value, str) else None
    if not match:
        raise ValueError(f"invalid color {value!r}, expected #rrggbb")
    h = match.group(1)
    return tuple(float(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def normalize_hex(value):
    return to_hex(parse_hex(value))


def to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def hsv_to_rgb(h, s, v):
    """h in degrees, s and v in 0..1 -> rgb in 0..255."""
    return tuple(c * 255 for c in colorsys.hsv_to_rgb((h % 360) / 360, s, v))


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))

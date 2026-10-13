import time

import pytest

from ledctl import effects as effects_mod
from ledctl import strip as strip_mod
from ledctl.app import create_app
from ledctl.colors import normalize_hex, parse_hex, to_hex
from ledctl.favorites import Favorites
from ledctl.hardware import MockDriver
from ledctl.strip import LEDStrip


@pytest.fixture
def strip(tmp_path, monkeypatch):
    monkeypatch.setattr(strip_mod, "FADE_TIME", 0.1)
    s = LEDStrip(MockDriver((1, 2, 3)), gamma=2.0, state_file=tmp_path / "state.json")
    yield s
    s.close()


@pytest.fixture
def client(strip, tmp_path):
    return create_app(strip, Favorites(tmp_path / "favs.json")).test_client()


def test_hex_roundtrip():
    assert parse_hex("#FF8000") == (255, 128, 0)
    assert to_hex((255, 128, 0)) == "#ff8000"
    assert normalize_hex("00ff00") == "#00ff00"
    for bad in ("#12345", "red", None, "#gggggg"):
        with pytest.raises(ValueError):
            parse_hex(bad)


def test_set_color_applies_gamma(strip):
    strip.set_color("#ff0000")
    assert strip._driver.levels == (1.0, 0.0, 0.0)
    strip.set_color("#808080")
    assert strip._driver.levels[0] == pytest.approx((128 / 255) ** 2)


def test_power_cycle_fades_and_restores(strip):
    strip.set_color("#00ff00")
    strip.set_power(False)
    time.sleep(0.3)
    assert strip._driver.levels == (0, 0, 0)
    assert strip.state()["on"] is False
    strip.set_power(True)
    time.sleep(0.3)
    assert strip._driver.levels == (0, 1.0, 0)


def test_rainbow_runs_and_stops(strip):
    strip.set_rainbow(2)
    time.sleep(0.2)
    assert strip.state()["mode"]["type"] == "rainbow"
    strip.set_color("#000000")
    assert strip._thread is None


def test_state_persists(strip, tmp_path):
    strip.set_fade("#ff0000", "#0000ff", 3)
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
    other.restore()
    assert other.state()["mode"]["type"] == "fade"
    other.close()


def test_candle_effect_stays_in_range_and_persists(strip, tmp_path):
    strip.set_effect("candle")
    seen = []
    for _ in range(20):
        time.sleep(0.03)
        seen.append(strip._current)
    assert all(0 <= c <= 255 for rgb in seen for c in rgb)
    assert len({round(r) for r, _, _ in seen}) > 1  # it actually flickers
    assert strip.state()["mode"] == {"type": "effect", "name": "candle"}
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
    other.restore()
    assert other.state()["mode"]["name"] == "candle"
    other.close()


def test_effect_api_validation(client):
    assert client.post("/api/effect", json={"name": "nope"}).status_code == 400
    assert client.post("/api/effect", json={"name": "candle"}).get_json()["mode"]["name"] == "candle"


def test_strobe_flashes_and_is_not_restored(strip, tmp_path):
    strip.set_effect("strobe", 10)
    seen = set()
    for _ in range(40):
        time.sleep(0.02)
        seen.add(strip._current)
    assert (255.0, 255.0, 255.0) in seen and (0.0, 0.0, 0.0) in seen
    assert strip.state()["mode"] == {"type": "effect", "name": "strobe", "rate": 10.0}
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
    other.restore()
    assert other.state()["mode"]["type"] == "static"
    other.close()


def test_pigs_alternates_red_and_blue_and_is_not_restored(strip, tmp_path):
    strip.set_effect("pigs")
    seen = set()
    for _ in range(60):
        time.sleep(0.02)
        seen.add(strip._current)
    assert {(255.0, 0.0, 0.0), (0.0, 0.0, 255.0), (0.0, 0.0, 0.0)} <= seen
    assert strip.state()["mode"] == {"type": "effect", "name": "pigs", "norway": False}
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
    other.restore()
    assert other.state()["mode"]["type"] == "static"
    other.close()


def test_cyberpunk_glitches_around_a_neon_base(strip, monkeypatch):
    import random
    from types import SimpleNamespace

    clock = [0.0]

    def fake_monotonic():
        clock[0] += 1 / 60
        return clock[0]

    monkeypatch.setattr(effects_mod, "time", SimpleNamespace(monotonic=fake_monotonic, sleep=time.sleep))
    frames = []
    gen = effects_mod.cyberpunk_loop(random.Random(1))
    for _ in range(60 * 30):  # 30 simulated seconds
        frames.append(next(gen))
    assert all(0 <= c <= 255 for rgb in frames for c in rgb)
    jumps = [max(abs(a - b) for a, b in zip(f1, f2)) for f1, f2 in zip(frames, frames[1:])]
    assert max(jumps) > 100  # glitches are abrupt
    calm = sum(1 for j in jumps if j < 5)
    assert calm > len(jumps) * 0.7  # but most of the time it is steady


def test_pigs_norway_mode_is_blue_only(monkeypatch):
    def colors(norway):
        frames = _simulate(monkeypatch, lambda: effects_mod.pigs_loop(norway=norway), 5)
        return set(frames)

    assert (255.0, 0.0, 0.0) in colors(False)
    norway = colors(True)
    assert norway == {(0.0, 0.0, 255.0), (0.0, 0.0, 0.0)}


def test_pigs_norway_option_through_the_api(client):
    mode = client.post("/api/effect", json={"name": "pigs", "norway": True}).get_json()["mode"]
    assert mode == {"type": "effect", "name": "pigs", "norway": True}
    assert client.post("/api/effect", json={"name": "pigs"}).get_json()["mode"]["norway"] is False
    assert client.post("/api/effect", json={"name": "pigs", "norway": 1}).status_code == 400


def test_cyberpunk_without_glitches_never_jumps(monkeypatch):
    import random

    frames = _simulate(monkeypatch, lambda: effects_mod.cyberpunk_loop(random.Random(1), glitch=False), 120)
    jumps = [max(abs(a - b) for a, b in zip(f1, f2)) for f1, f2 in zip(frames, frames[1:])]
    assert max(jumps) < 5
    assert len({tuple(round(c / 20) for c in f) for f in frames}) > 5  # but the color still drifts


def test_cyberpunk_glitch_option_through_the_api(client, strip):
    mode = client.post("/api/effect", json={"name": "cyberpunk", "glitch": False}).get_json()["mode"]
    assert mode == {"type": "effect", "name": "cyberpunk", "glitch": False}
    assert client.post("/api/effect", json={"name": "cyberpunk"}).get_json()["mode"]["glitch"] is True
    assert client.post("/api/effect", json={"name": "cyberpunk", "glitch": "no"}).status_code == 400
    # persisted: a restart keeps the choice
    client.post("/api/effect", json={"name": "cyberpunk", "glitch": False})
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=strip._state_file)
    other.restore()
    assert other.state()["mode"]["glitch"] is False
    other.close()


def test_cyberpunk_is_selectable_and_resumes(strip, tmp_path):
    strip.set_effect("cyberpunk")
    other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
    other.restore()
    assert other.state()["mode"] == {"type": "effect", "name": "cyberpunk", "glitch": True}
    other.close()


def _simulate(monkeypatch, gen_factory, seconds):
    from types import SimpleNamespace

    clock = [0.0]

    def fake_monotonic():
        clock[0] += 1 / 60
        return clock[0]

    monkeypatch.setattr(effects_mod, "time", SimpleNamespace(monotonic=fake_monotonic, sleep=time.sleep))
    gen = gen_factory()
    return [next(gen) for _ in range(int(seconds * 60))]


def test_aurora_is_smooth_colorful_and_in_range(monkeypatch):
    import random

    frames = _simulate(monkeypatch, lambda: effects_mod.aurora_loop(random.Random(3)), 600)
    assert all(0 <= c <= 255 for rgb in frames for c in rgb)
    jumps = [max(abs(a - b) for a, b in zip(f1, f2)) for f1, f2 in zip(frames, frames[1:])]
    assert max(jumps) < 3  # no sudden changes
    greens = [g for _, g, _ in frames]
    blues = [b for _, _, b in frames]
    assert max(greens) - min(greens) > 50 and max(blues) - min(blues) > 100  # it really drifts
    assert min(sum(f) for f in frames) > 100  # never goes dark


def test_thunderstorm_is_dim_with_rare_bright_flashes(monkeypatch):
    import random

    frames = _simulate(monkeypatch, lambda: effects_mod.thunderstorm_loop(random.Random(5)), 300)
    assert all(0 <= c <= 255 for rgb in frames for c in rgb)
    brightness = sorted(sum(f) for f in frames)
    assert brightness[len(brightness) // 2] < 180  # normally dim
    assert brightness[-1] > 450  # lightning is bright
    bright = sum(1 for b in brightness if b > 300)
    assert 0 < bright < len(frames) * 0.1  # but rare


def test_new_effects_selectable_and_resume(strip, tmp_path):
    for name in ("aurora", "thunderstorm"):
        strip.set_effect(name)
        other = LEDStrip(MockDriver((1, 2, 3)), state_file=tmp_path / "state.json")
        other.restore()
        assert other.state()["mode"] == {"type": "effect", "name": name}
        other.close()


class FakePi:
    connected = True

    def __init__(self):
        self.freq = {}
        self.range = {}
        self.duty = []

    def set_PWM_frequency(self, pin, hz):
        self.freq[pin] = hz

    def get_PWM_frequency(self, pin):
        return self.freq[pin]

    def get_PWM_real_range(self, pin):
        return 1000 if self.freq[pin] == 200 else 250

    def set_PWM_range(self, pin, r):
        self.range[pin] = r

    def set_PWM_dutycycle(self, pin, duty):
        self.duty.append((pin, duty))

    def stop(self):
        pass


@pytest.fixture
def fake_pigpio(monkeypatch):
    import sys
    from types import SimpleNamespace

    pi = FakePi()
    monkeypatch.setitem(sys.modules, "pigpio", SimpleNamespace(pi=lambda: pi))
    return pi


def test_pwm_uses_the_real_resolution(fake_pigpio):
    from ledctl.hardware import PigpioDriver

    PigpioDriver((17, 22, 24), pwm_freq=200)
    assert fake_pigpio.freq == {17: 200, 22: 200, 24: 200}
    assert fake_pigpio.range == {17: 1000, 22: 1000, 24: 1000}


def test_dithering_makes_dark_levels_smooth(fake_pigpio):
    from ledctl.hardware import PigpioDriver

    driver = PigpioDriver((17,), pwm_freq=200)
    fake_pigpio.duty.clear()
    for _ in range(1000):
        driver.write([0.0017])  # 1.7 steps: dark storm red after gamma
    duties = [d for _, d in fake_pigpio.duty]
    assert set(duties) == {1, 2}
    assert sum(duties) / len(duties) == pytest.approx(1.7, abs=0.01)


def test_dithering_never_leaves_range(fake_pigpio):
    from ledctl.hardware import PigpioDriver

    driver = PigpioDriver((17,), pwm_freq=200)
    fake_pigpio.duty.clear()
    for level in (0.0, 1.0, 0.0004, 0.9996, 1.0):
        for _ in range(20):
            driver.write([level])
    assert all(0 <= d <= 1000 for _, d in fake_pigpio.duty)


def test_strobe_rate_is_limited(client):
    assert client.post("/api/effect", json={"name": "strobe", "rate": 30}).status_code == 400
    assert client.post("/api/effect", json={"name": "strobe", "rate": "x"}).status_code == 400
    assert client.post("/api/effect", json={"name": "strobe"}).get_json()["mode"]["rate"] == 4


def test_fade_same_colors_does_not_crash(strip):
    strip.set_fade("#123456", "#123456", 1)
    time.sleep(0.1)


def test_api_validation(client):
    assert client.post("/api/color", json={"color": "nope"}).status_code == 400
    assert client.post("/api/color", data="x").status_code == 400
    assert client.post("/api/power", json={"on": "false"}).status_code == 400
    assert client.post("/api/fade", json={"start": "#000000", "end": "#ffffff", "period": 0}).status_code == 400
    assert client.post("/api/color", json={"color": "#ff00aa"}).get_json()["color"] == "#ff00aa"


def test_favorites_api(client):
    assert client.get("/api/favorites").get_json() == []
    client.post("/api/favorites", json={"color": "#FF00AA"})
    client.post("/api/favorites", json={"color": "#ff00aa"})
    assert client.get("/api/favorites").get_json() == ["#ff00aa"]
    assert client.delete("/api/favorites/ff00aa").get_json() == []


def test_serves_ui(client):
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_state_reports_mock(client):
    assert client.get("/api/state").get_json()["mock"] is True

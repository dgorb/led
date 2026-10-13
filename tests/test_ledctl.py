import time

import pytest

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

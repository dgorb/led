import logging

from flask import Flask, jsonify, request, send_from_directory

from . import config
from .favorites import Favorites
from .hardware import create_driver
from .strip import LEDStrip


def create_app(strip, favorites):
    app = Flask(__name__, static_folder=None)

    @app.errorhandler(ValueError)
    def bad_request(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(Exception)
    def server_error(err):
        app.logger.exception("Unhandled error")
        return jsonify(error="internal error"), 500

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object body")
        return data

    def field(data, name):
        if name not in data:
            raise ValueError(f"missing field '{name}'")
        return data[name]

    @app.get("/api/state")
    def get_state():
        return jsonify(strip.state())

    @app.post("/api/color")
    def set_color():
        strip.set_color(field(body(), "color"))
        return jsonify(strip.state())

    @app.post("/api/power")
    def set_power():
        on = field(body(), "on")
        if not isinstance(on, bool):
            raise ValueError("'on' must be a boolean")
        strip.set_power(on)
        return jsonify(strip.state())

    @app.post("/api/fade")
    def set_fade():
        data = body()
        strip.set_fade(field(data, "start"), field(data, "end"), field(data, "period"))
        return jsonify(strip.state())

    @app.post("/api/effect")
    def set_effect():
        strip.set_effect(field(data := body(), "name"), data)
        return jsonify(strip.state())

    @app.post("/api/rainbow")
    def set_rainbow():
        strip.set_rainbow(field(body(), "period"))
        return jsonify(strip.state())

    @app.get("/api/favorites")
    def list_favorites():
        return jsonify(favorites.list())

    @app.post("/api/favorites")
    def add_favorite():
        return jsonify(favorites.add(field(body(), "color"))), 201

    @app.delete("/api/favorites/<color>")
    def remove_favorite(color):
        return jsonify(favorites.remove(color))

    @app.get("/")
    def index():
        return send_from_directory(config.ROOT / "web", "index.html")

    @app.get("/<path:path>")
    def static_files(path):
        return send_from_directory(config.ROOT / "web", path)

    return app


def main():
    logging.basicConfig(level=logging.INFO)
    driver = create_driver(config.PINS, mock=config.MOCK, pwm_freq=config.PWM_FREQ)
    strip = LEDStrip(driver, gamma=config.GAMMA, state_file=config.DATA_DIR / "state.json")
    strip.restore()
    app = create_app(strip, Favorites(config.DATA_DIR / "favorites.json"))
    try:
        app.run(host=config.HOST, port=config.PORT, threaded=True)
    finally:
        strip.close()

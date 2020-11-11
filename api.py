import os
import flask

from flask import request, make_response, send_from_directory, jsonify
from led import LEDStrip

from favorites import store_favorite, read_favorites

app = flask.Flask(__name__, static_folder='ui/build')
app.config["DEBUG"] = True

led_strip = LEDStrip(0, 0, 0)


# Serve React
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route('/turn-off', methods=['POST'])
def turn_off():
    led_strip.off(fade_out=True)

    return make_response(f"LED strip turned off!", 200)

@app.route('/turn-on', methods=['POST'])
def turn_on():
    color = request.args.get('color')
    led_strip.on(*[int(c) for c in color.split(',')], fade_in=True)

    return make_response(f"LED strip turned on!", 200)

@app.route('/set-color', methods=['POST'])
def set_color():
    color = request.args.get('color')
    led_strip.set_color(*[int(c) for c in color.split(',')])

    return make_response(f"Setting color to {color}", 200)

@app.route('/shift', methods=['POST'])
def shift():
    start = request.args.get('start')
    end = request.args.get('end')
    period = request.args.get('period')
    cont = request.args.get('cont')

    start_color = [int(c) for c in start.split(',')]
    end_color = [int(c) for c in end.split(',')]
    period = int(period)
    cont = bool(cont)

    led_strip.ctr.stop_all()
    led_strip.shift(start_color, end_color, period, cont)

    return make_response(f"Shifting between {start} and {end} with period of {period}s", 200)

@app.route('/get-color', methods=['GET'])
def get_color():
    color = led_strip.get_color()
    return make_response(jsonify(color), 200)

@app.route('/favorite', methods=['POST'])
def favorite():
    color = request.args.get('color')

    try:
        store_favorite(color)
        return make_response("Saved favorite", 200)
    except Exception as e:
        return make_response(f"Server error: {e}", 500)

@app.route('/favorites', methods=['GET'])
def favorites():
    return make_response(jsonify(read_favorites()))

@app.errorhandler(Exception)
def all_exception_handler(error):
    print(error)
    return 'Error', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

import flask

from flask import request, make_response
from led import LEDStrip

app = flask.Flask(__name__)
app.config["DEBUG"] = True

led_strip = LEDStrip(0, 0, 0)


@app.route('/', methods=['GET'])
def home():
    return "Hello"

@app.route('/turn-off', methods=['POST'])
def turn_off():
    led_strip.off()

    return make_response(f"LED strip turned off!", 200)

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

@app.errorhandler(Exception)
def all_exception_handler(error):
    print(error)
    return 'Error', 500

if __name__ == '__main__':
    app.run()

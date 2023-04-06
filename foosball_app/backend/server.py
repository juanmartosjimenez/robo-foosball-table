import queue
from typing import Optional

from flask import Flask, jsonify

from other.events import FlaskAppEvent

app = Flask(__name__)
app.queue_to_flask: Optional[queue.Queue] = None
app.queue_from_flask: Optional[queue.Queue] = None


@app.route('/')
def index():
    return 'Hello, world!'


@app.route('/power_on')
def power_on():
    app.queue_from_flask.put_nowait((FlaskAppEvent.POWER_ON, ))

@app.route('/start')
def start():
    app.queue_from_flask.put_nowait((FlaskAppEvent.START,))
    return 'Start Button Clicked'


@app.route('/reset')
def reset():
    app.queue_from_flask.put_nowait((FlaskAppEvent.STOP, ))
    return 'Reset Button Clicked'


@app.route('/coordinates')
def coordinates():
    return jsonify({'x': 1, 'y': 2})


if __name__ == '__main__':
    app.run(debug=False)

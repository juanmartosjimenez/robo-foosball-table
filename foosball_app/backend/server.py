import queue
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import os

from other.events import FlaskAppEvent

import json

app = Flask(__name__)
app.queue_to_flask: Optional[queue.Queue] = None
app.queue_from_flask: Optional[queue.Queue] = None
PATH_TO_CORNERS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"camera", "data", 'corners.json')
BALL_POSITIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"camera", "data", 'ball_positions.txt')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def calc_board_dim():
    with open(PATH_TO_CORNERS) as f:
        data = json.load(f)

    length = data[2][1] - data[0][1]
    width = data[2][0] - data[0][0]

    return length, width


def calculate_coord(length, width, source_point):
    x = (source_point[0] / width) * 700
    y = (source_point[1] / length) * 350

    tgt_point = [x, y]

    return tgt_point


def get_ball_coords():
    if not os.path.exists(BALL_POSITIONS):
        return None

    with open(BALL_POSITIONS, 'r') as f:
        line = f.readline().strip()
        values = line.split(",")
        first_two_values = [float(values[0]), float(values[1])]
    return first_two_values


@app.route('/')
@cross_origin()
def index():
    return 'Hello, world!'


@app.route('/api/power_on')
@cross_origin()
def power_on():
    app.queue_from_flask.put_nowait((FlaskAppEvent.POWER_ON,))


@app.route('/api/start')
@cross_origin()
def start():
    app.queue_from_flask.put_nowait((FlaskAppEvent.START,))
    return 'Start Button Clicked'


@app.route('/api/reset')
@cross_origin()
def reset():
    app.queue_from_flask.put_nowait((FlaskAppEvent.STOP,))
    return 'Reset Button Clicked'


@app.route('/api/coordinates')
@cross_origin()
def coordinates():
    # Represents the length and width of the pixels in the camera
    length, width = calc_board_dim()
    # Convert pixels to ball 
    source_point = get_ball_coords()
    # Calculate the target point
    if source_point:
        target_coord = calculate_coord(length, width, source_point)
        # Read in those coords
        # pass to frontend
        return jsonify({'x': round(target_coord[0]), 'y': round(target_coord[1])})
    else:
        return jsonify({'x': 0, 'y': 0})


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

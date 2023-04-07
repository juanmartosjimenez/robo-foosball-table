import queue
from typing import Optional

from flask import Flask, jsonify

from other.events import FlaskAppEvent

import json




app = Flask(__name__)
app.queue_to_flask: Optional[queue.Queue] = None
app.queue_from_flask: Optional[queue.Queue] = None

def calc_board_dim():
    with open('corners.json') as f: 
        data = json.load(f) 

    board_size = data['board_size']
    length = board_size[2][1] - board_size[0][1]
    width = board_size[2][0] - board_size[0][0]

    return length, width

def calculate_coord(length, width, source_point):
    x = (source_point[0] / length) * 700
    y = (source_point[1] / width) * 350

    tgt_point = [x, y]

    return tgt_point

def get_ball_coords():
    with open('file.txt', 'r') as f:
        line = f.readline().strip()
        values = line.split()
        first_two_values = [float(values[0]), float(values[1])]
    return first_two_values

@app.route('/')
def index():
    return 'Hello, world!'


@app.route('/api/power_on')
def power_on():
    app.queue_from_flask.put_nowait((FlaskAppEvent.POWER_ON,))


@app.route('/api/start')
def start():
    app.queue_from_flask.put_nowait((FlaskAppEvent.START,))
    return 'Start Button Clicked'


@app.route('/api/reset')
def reset():
    app.queue_from_flask.put_nowait((FlaskAppEvent.STOP,))
    return 'Reset Button Clicked'


@app.route('/api/coordinates')
def coordinates():
    #Represents the length and width of the pixels in the camera 
    length, width = calc_board_dim()
    # Convert pixels to ball 
    source_point = get_ball_coords()
    # Calculate the target point
    target_coord = calculate_coord(length, width, source_point)
    # Read in those coords 
    #pass to frontend 
    return jsonify({'x': target_coord[0], 'y': target_coord[1]})


if __name__ == '__main__':
    app.run(debug=False)

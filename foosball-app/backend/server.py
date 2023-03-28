from flask import Flask, jsonify


app = Flask(__name__)


@app.route('/')
def index():

    return 'Hello, world!'

@app.route('/start')
def start():
    return 'Start Button Clicked'

@app.route('/reset')
def reset():
    return 'Reset Button Clicked'


@app.route('/coordinates')
def coordinates():
    return jsonify({'x': 1, 'y': 2})


if __name__ == '__main__':
    app.run()

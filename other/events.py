from enum import Enum


class FrontendEvent(Enum):
    """Events"""
    CURRENT_BALL_POS = 1
    PREDICTED_BALL_POS = 2
    ERROR = 3
    ENCODER_VALS = 4
    FPS = 5
    START = 6
    STOP = 7
    POWER_ON = 8
    HOME_M1 = 9
    HOME_M2 = 10
    MOVE_TO_START_POS = 11
    TEST_LATENCY = 12



class MotorEvent(Enum):
    """Events"""
    MOVE_TO_POS = 1
    STRIKE = 2
    HOME_M1 = 3
    HOME_M2 = 4
    STOP = 5
    ENCODER_VALS = 6
    MOVE_TO_START_POS = 7
    ERROR = 8
    TEST_STRIKE = 9


class CameraEvent(Enum):
    """Events"""
    START_BALL_TRACKING = 1
    CURRENT_BALL_POS = 2
    PREDICTED_BALL_POS = 3
    ERROR = 4
    FPS = 5
    STRIKE = 6
    TEST_STRIKE = 7


class LinearMotorEvent(Enum):
    """Events"""
    MOVE_TO_POS = 1
    HOME = 3
    MOVE_TO_DEFAULT = 4


class RotationalMotorEvent(Enum):
    """Events"""
    MOVE_TO_POS = 1
    STRIKE = 2
    HOME = 3
    MOVE_TO_DEFAULT = 5
    TEST_STRIKE = 6

class FlaskAppEvent(Enum):
    START = 1
    STOP = 2
    ERROR = 3
    POWER_ON = 4


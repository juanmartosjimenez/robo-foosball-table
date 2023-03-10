from enum import Enum


class FrontendEvent(Enum):
    """Events"""
    CURRENT_BALL_POS = 1
    PREDICTED_BALL_POS = 2
    ERROR = 3
    ENCODER_VALS = 4


class MotorEvent(Enum):
    """Events"""
    MOVE_TO_MM_M1 = 1
    STRIKE = 2
    HOME_M1 = 3
    HOME_M2 = 4
    STOP = 5
    ENCODER_VALS = 6
    MOVE_TO_START_POS = 7


class CameraEvent(Enum):
    """Events"""
    START_BALL_TRACKING = 1
    CURRENT_BALL_POS = 2
    PREDICTED_BALL_POS = 3


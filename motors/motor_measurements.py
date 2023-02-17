import pydantic

"""
File stores a bunch of hardcoded values related to the motors.
"""

measurements = {"ENC_M2_360_ROTATION": 145,
                "ENC_M2_DEFAULT": 135,
                "ENC_M2_STRIKE": 110,
                "ENC_M1_DEFAULT": 667}


class MotorMeasurements(pydantic.BaseModel):
    """Class to hold measurements of the motors."""
    # M2 encoder position for a 360-degree rotation of the shaft.
    enc_m2_360_rotation: int = measurements["ENC_M2_360_ROTATION"]
    # M2 encoder position for the strike position should be back from the default position to gain momentum.
    enc_m2_strike: int = measurements["ENC_M2_STRIKE"]
    # M2 default encoder position such that players are facing down.
    enc_m2_default: int = measurements["ENC_M2_DEFAULT"]
    # M1 default encoder position such that goalie is centered with goal.
    enc_m1_default: int = measurements["ENC_M1_DEFAULT"]

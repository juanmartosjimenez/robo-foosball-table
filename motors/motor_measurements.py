import pydantic

"""
File stores a bunch of hardcoded values related to the motors.
"""

measurements = {"ENC_M2_360_ROTATION": 145,
                "ENC_M2_DEFAULT": 135,
                "ENC_M2_STRIKE": 110,
                "ENC_M1_DEFAULT": 667,
                "MM_TO_ENC_M1": 13,
                "M1_ENCODER_LIMIT": 1600,
                "M2_ENCODER_LIMIT": 2000}


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
    # M1 conversion unit from mm to encoder position.
    m1_mm_to_enc: float = measurements["MM_TO_ENC_M1"]
    m1_encoder_limit: int = measurements["M1_ENCODER_LIMIT"]
    m2_encoder_limit: int = measurements["M2_ENCODER_LIMIT"]

import pydantic

"""
File stores a bunch of hardcoded values related to the cameras and aruco markers.
"""

measurements = {"MM_ARUCO_PADDING": 10,
                "ID_ARUCO_TOP_RIGHT": 1,
                "ID_ARUCO_TOP_LEFT": 2,
                "ID_ARUCO_BOTTOM_RIGHT": 3,
                "ID_ARUCO_BOTTOM_LEFT": 4,
                "MM_ARUCO_LENGTH": 49.3,
                "MM_PLAYING_FIELD_LENGTH": 1170,
                "MM_PLAYING_FIELD_WIDTH": 630}


class CameraMeasurements(pydantic.BaseModel):
    """Class to hold camera and aruco values."""
    mm_aruco_padding: int = measurements["MM_ARUCO_PADDING"]
    id_aruco_top_right: int = measurements["ID_ARUCO_TOP_RIGHT"]
    id_aruco_top_left: int = measurements["ID_ARUCO_TOP_LEFT"]
    id_aruco_bottom_right: int = measurements["ID_ARUCO_BOTTOM_RIGHT"]
    id_aruco_bottom_left: int = measurements["ID_ARUCO_BOTTOM_LEFT"]
    mm_aruco_length: float= measurements["MM_ARUCO_LENGTH"]
    mm_playing_field_length: float= measurements["MM_PLAYING_FIELD_LENGTH"]
    mm_playing_field_width: float= measurements["MM_PLAYING_FIELD_WIDTH"]

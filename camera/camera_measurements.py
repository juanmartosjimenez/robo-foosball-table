import pydantic

"""
File stores a bunch of hardcoded values related to the cameras and aruco markers.
"""

measurements = {"MM_ARUCO_PADDING": 10,
                "ID_ARUCO_TOP_RIGHT": 5,
                "ID_ARUCO_TOP_LEFT": 3,
                "ID_ARUCO_BOTTOM_RIGHT": 2,
                "ID_ARUCO_BOTTOM_LEFT": 4,
                "ID_ARUCO_PLAYING_FIELD_BOTTOM": 1,
                "ID_ARUCO_PLAYING_FIELD_TOP": 6,
                "MM_ARUCO_LENGTH": 68.5,
                "MM_PLAYING_FIELD_LENGTH": 1170,
                "MM_PLAYING_FIELD_WIDTH": 630,
                "MM_Y_CORNER_TO_CORNER": 1187,
                "MM_X_CORNER_TO_CORNER": 609,
                "MM_PLAYING_FIELD_TO_ARUCO": 59}


class CameraMeasurements(pydantic.BaseModel):
    """Class to hold camera and aruco values."""
    mm_aruco_padding: int = measurements["MM_ARUCO_PADDING"]
    id_aruco_top_right: int = measurements["ID_ARUCO_TOP_RIGHT"]
    id_aruco_top_left: int = measurements["ID_ARUCO_TOP_LEFT"]
    id_aruco_bottom_right: int = measurements["ID_ARUCO_BOTTOM_RIGHT"]
    id_aruco_bottom_left: int = measurements["ID_ARUCO_BOTTOM_LEFT"]
    id_aruco_playing_field_top: int = measurements["ID_ARUCO_PLAYING_FIELD_TOP"]
    id_aruco_playing_field_bottom: int = measurements["ID_ARUCO_PLAYING_FIELD_BOTTOM"]
    mm_aruco_length: float = measurements["MM_ARUCO_LENGTH"]
    mm_playing_field_length: float = measurements["MM_PLAYING_FIELD_LENGTH"]
    mm_playing_field_width: float = measurements["MM_PLAYING_FIELD_WIDTH"]
    mm_y_corner_to_corner: float = measurements["MM_Y_CORNER_TO_CORNER"]
    mm_x_corner_to_corner: float = measurements["MM_X_CORNER_TO_CORNER"]
    mm_playing_field_to_aruco: float = measurements["MM_PLAYING_FIELD_TO_ARUCO"]

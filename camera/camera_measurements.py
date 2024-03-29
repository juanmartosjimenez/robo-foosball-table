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
                "MM_PLAYING_FIELD_X": 1170,
                "MM_PLAYING_FIELD_Y": 631,
                "CAMERA_RESOLUTION_Y": 540,
                "CAMERA_RESOLUTION_X": 960,
                "STRIKE_ZONE_PIXELS": 50,
                "CAMERA_FPS": 60,
                "Y_PERSPECTIVE_COMPENSATION": 20}


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
    mm_playing_field_y: float = measurements["MM_PLAYING_FIELD_Y"]
    mm_playing_field_x: float = measurements["MM_PLAYING_FIELD_X"]
    camera_resolution_x: int = measurements["CAMERA_RESOLUTION_X"]
    camera_resolution_y: int = measurements["CAMERA_RESOLUTION_Y"]
    camera_fps: int = measurements["CAMERA_FPS"]
    y_perspective_compensation: int = measurements["Y_PERSPECTIVE_COMPENSATION"]
    strike_zone_pixels: int = measurements["STRIKE_ZONE_PIXELS"]



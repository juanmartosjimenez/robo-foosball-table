import time

import cv2 as cv
import pyrealsense2 as rs
import numpy as np
from camera.utilities import get_screenshot, start_pipe


def generate_markers():
    """
    Generate four aruco markers and save them to disk. One for each corner of the foosball table.
    :return:
    """
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    for ii in range(4):
        image_marker = cv.aruco.generateImageMarker(aruco_dict, ii + 1, 700)
        cv.imwrite("Marker{}.png".format(ii + 1), image_marker)


def draw_markers(ids, corners, realsense_screenshot):
    # verify *at least* one ArUco marker was detected
    # if len(corners) > 0:
    cv.aruco.drawDetectedMarkers(realsense_screenshot, corners, ids)
    cv.imshow("Image", realsense_screenshot)
    cv.waitKey(0)


def pose_estimation(ids, corners, realsense_screenshot):
    """
    Use solvePnP to estimate the pose of the camera relative to the markers.
    :return:
    """
    pipe = start_pipe()
    intrinsics = pipe.get_active_profile().get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    camera_matrix = np.array([[intrinsics.fx, 0, intrinsics.ppx], [0, intrinsics.fy, intrinsics.ppy], [0, 0, 1]])
    # Squares are 49.3mm x 49.3mm
    objpoints = np.array([[0, 0, 0], [0, 49.3, 0], [49.3, 49.3, 0], [49.3, 0, 0]], dtype=np.float32)

    vecs = {}
    for ii in range(len(corners)):
        print(corners[ii])
        retval, rvec, tvec = cv.solvePnP(objpoints, corners[ii], camera_matrix, None)
        vecs[ids[ii][0]] = (rvec, tvec)
        cv.drawFrameAxes(realsense_screenshot, camera_matrix, None, rvec, tvec, 50, thickness=2)
    cv.imshow("Image", realsense_screenshot)
    cv.waitKey(0)

    # Top right 1
    # Top left 2
    # Bottom right 3
    # Bottom left 4
    print(np.linalg.norm(vecs[4][1] - vecs[3][1]))
    pass


# aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_1000)
def detect_markers():
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    aruco_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aruco_dict, aruco_params)

    realsense_screenshot = get_screenshot()
    gray = cv.cvtColor(realsense_screenshot, cv.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(realsense_screenshot)
    tmp_corners = np.copy(corners)
    top_right = 0
    top_left = 0
    bottom_right = 0
    bottom_left = 0

    for ii, id in enumerate(ids):
        if ids[ii] == 4:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 1, axis=1)
            bottom_left = tmp_corners[ii][:, 0]
        elif ids[ii] == 2:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 2, axis=1)
            top_left = tmp_corners[ii][0]
        elif ids[ii] == 1:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 3, axis=1)
            top_right = tmp_corners[ii][0]
        elif ids[ii] == 3:
            bottom_right = tmp_corners[ii][:,0]

    x_diff = (bottom_right - bottom_left)[0,0]
    y_diff = (bottom_left-top_left)[0,1]

    # Have to take into account the white padding surrounding the marker
    x_length_mm = 1170
    y_length_mm = 630

    x_length_mm += 20
    y_length_mm -= 20

    pixel_to_mm_x = x_length_mm / x_diff
    pixel_to_mm_y = y_length_mm / y_diff
    print(pixel_to_mm_y, pixel_to_mm_x)




if __name__ == '__main__':
    detect_markers()

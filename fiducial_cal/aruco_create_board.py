import time

import cv2 as cv
import pyrealsense2 as rs
from numpy import size
import matplotlib.pyplot as plt
import matplotlib as mpl
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


# aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_1000)
def detect_markers():
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    aruco_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aruco_dict, aruco_params)

    realsense_screenshot = get_screenshot()
    gray = cv.cvtColor(realsense_screenshot, cv.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(realsense_screenshot)
    # verify *at least* one ArUco marker was detected
    if len(corners) > 0:
        cv.aruco.drawDetectedMarkers(realsense_screenshot, corners, ids)

    pipe = start_pipe()
    intrinsics = pipe.get_active_profile().get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    camera_matrix = np.array([[intrinsics.fx, 0, intrinsics.ppx], [0, intrinsics.fy, intrinsics.ppy], [0, 0, 1]])
    # Squares are 49.3mm x 49.3mm
    objpoints = np.array([[0, 0, 0], [0, 49.3, 0], [49.3, 49.3, 0], [49.3, 0, 0]], dtype=np.float32)

    for ii in range(len(corners)):

        retval, rvecs, tvecs = cv.solvePnP(objpoints, corners[ii], camera_matrix, None)
        cv.drawFrameAxes(realsense_screenshot, camera_matrix, None, rvecs, tvecs, 50, thickness=2)
    cv.imshow("Image", realsense_screenshot)
    cv.waitKey(0)


    #if rejected:
    #    cv.aruco.drawDetectedMarkers(realsense_screenshot, rejected, borderColor=(0, 0, 255))
    #    cv.imshow("Image", realsense_screenshot)


if __name__ == '__main__':
    detect_markers()

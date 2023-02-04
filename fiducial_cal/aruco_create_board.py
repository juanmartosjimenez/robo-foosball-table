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
        cv.imshow("Image", realsense_screenshot)
        #cv.waitKey(0)

    pipe = start_pipe()
    intrinsics = pipe.get_active_profile().get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    extrinsics = pipe.get_active_profile().get_stream(rs.stream.color).as_video_stream_profile().get_extrinsics_to(to=pipe.get_active_profile().get_stream(rs.stream.color))
    print(intrinsics.ppx)
    print(intrinsics.ppy)
    print(intrinsics.fx)
    print(intrinsics.fy)
    print(intrinsics.width)
    print(intrinsics.height)
    print(extrinsics)

    for ii in range(len(corners)):
        print("Marker {}: {}".format(ids[ii], corners[ii]))
        print("Marker {}: {}".format(ids[ii], cv.solvePnP(corners[ii], 0.05, None)))


    #if rejected:
    #    cv.aruco.drawDetectedMarkers(realsense_screenshot, rejected, borderColor=(0, 0, 255))
    #    cv.imshow("Image", realsense_screenshot)




if __name__ == '__main__':
    detect_markers()

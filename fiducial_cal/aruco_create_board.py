import time

import cv2 as cv
from numpy import size
import matplotlib.pyplot as plt
import matplotlib as mpl
from camera.utilities import get_screenshot


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
    print(corners, ids, rejected)
    # verify *at least* one ArUco marker was detected
    if len(corners) > 0:
        cv.aruco.drawDetectedMarkers(realsense_screenshot, corners, ids)
        cv.imshow("Image", realsense_screenshot)
        cv.waitKey(0)

    if rejected:
        cv.aruco.drawDetectedMarkers(realsense_screenshot, rejected, borderColor=(0, 0, 255))
        cv.imshow("Image", realsense_screenshot)
        cv.waitKey(0)



if __name__ == '__main__':
    detect_markers()

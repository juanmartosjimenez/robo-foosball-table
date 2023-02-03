import cv2 as cv
from numpy import size
import matplotlib.pyplot as plt
import matplotlib as mpl


def generate_marker():
    """
    Generate four aruco markers and save them to disk. One for each corner of the foosball table.
    :return:
    """
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    for ii in range(4):
        image_marker = cv.aruco.generateImageMarker(aruco_dict, ii + 1, 700)
        cv.imwrite("Marker{}.png".format(ii + 1), image_marker)


# aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_1000)
def main():
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    print(aruco_dict)
    # Dimensions in cm
    marker_length = 0.04
    marker_separation = 0.01
    aruco_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aruco_dict, aruco_params)
    board = cv.aruco.GridBoard(
        size(5, 7), marker_length, marker_separation, aruco_dict)
    cv.imwrite("Marker.png", board)


if __name__ == '__main__':
    generate_marker()

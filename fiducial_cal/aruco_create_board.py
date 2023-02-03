import cv2 as cv
from numpy import size


#aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_1000)
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
    main()
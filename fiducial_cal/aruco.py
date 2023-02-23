
import numpy as np
import cv2

import pathlib


def calibrate_aruco(dirpath, image_format, marker_length, marker_separation):
    '''Apply camera calibration using aruco.
    The dimensions are in cm.
    '''
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
    arucoParams = cv2.aruco.DetectorParameters()
    board = cv2.aruco.GridBoard(
        (5, 7), marker_length, marker_separation, aruco_dict)

    counter, corners_list, id_list = [], [], []
    img_dir = pathlib.Path(dirpath)
    first = 0
    
    # Find the ArUco markers inside each image
    for img in img_dir.glob(f'*.{image_format}'):
        image = cv2.imread(str(img))
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(
            img_gray,
            aruco_dict,
            parameters=arucoParams
        )
        
        if first == 0:
            corners_list = corners
            id_list = ids
        else:
            corners_list = np.vstack((corners_list, corners))
            id_list = np.vstack((id_list, ids))
        first = first + 1
        counter.append(len(ids))

    counter = np.array(counter)
    # Actual calibration
    ret, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraAruco(
        corners_list,
        id_list,
        counter,
        board,
        img_gray.shape,
        None,
        None
    )

    return [ret, mtx, dist, rvecs, tvecs]

    

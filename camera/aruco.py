import cv2 as cv
import numpy as np

from camera.camera_measurements import CameraMeasurements

camera_measurements = CameraMeasurements()


def generate_markers():
    """
    Generate four aruco markers and save them to disk. One for each corner of the foosball table.
    :return:
    """
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    for ii in range(6):
        image_marker = cv.aruco.generateImageMarker(aruco_dict, ii + 1, 260)
        cv.imwrite(r"ArUcoTags/Marker{}.png".format(ii + 1), image_marker)


def draw_markers(ids, corners, rgb_frame):
    # verify *at least* one ArUco marker was detected
    # if len(corners) > 0:
    cv.aruco.drawDetectedMarkers(rgb_frame, corners, ids)
    cv.imshow("Image", rgb_frame)
    cv.waitKey(0)


def pose_estimation(ids, corners, rgb_frame, intrinsics):
    """
    Use solvePnP to estimate the pose of the camera relative to the markers.
    :return:
    """
    camera_matrix = np.array([[intrinsics.fx, 0, intrinsics.ppx], [0, intrinsics.fy, intrinsics.ppy], [0, 0, 1]])
    objpoints = np.array([[0, 0, 0], [0, camera_measurements.mm_aruco_length, 0],
                          [camera_measurements.mm_aruco_length, camera_measurements.mm_aruco_length, 0],
                          [camera_measurements.mm_aruco_length, 0, 0]], dtype=np.float32)

    vecs = {}
    for ii in range(len(corners)):
        print(corners[ii])
        retval, rvec, tvec = cv.solvePnP(objpoints, corners[ii], camera_matrix, None)
        vecs[ids[ii][0]] = (rvec, tvec)
        cv.drawFrameAxes(rgb_frame, camera_matrix, None, rvec, tvec, 50, thickness=2)
    cv.imshow("Image", rgb_frame)
    cv.waitKey(0)

    # Top right 1
    # Top left 2
    # Bottom right 3
    # Bottom left 4
    print(np.linalg.norm(vecs[camera_measurements.id_aruco_bottom_right][1] - vecs[camera_measurements.id_aruco_bottom_left][1]))


def detect_markers(rgb_frame: np.array) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Get ArUco dictionary
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    aruco_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aruco_dict, aruco_params)

    # Convert to grayscale
    gray = cv.cvtColor(rgb_frame, cv.COLOR_BGR2GRAY)

    # Detect markers
    corners, ids, rejected = detector.detectMarkers(rgb_frame)
    # refactor corners area to so that it is easier to use
    tmp_corners = np.copy(corners)

    stack = [camera_measurements.id_aruco_playing_field_top, camera_measurements.id_aruco_playing_field_bottom, camera_measurements.id_aruco_bottom_left, camera_measurements.id_aruco_bottom_right, camera_measurements.id_aruco_top_right, camera_measurements.id_aruco_top_left]
    for ii, id in enumerate(ids):
        if ids[ii] == camera_measurements.id_aruco_bottom_left:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 1, axis=1)
            stack.remove(camera_measurements.id_aruco_bottom_left)
        elif ids[ii] == camera_measurements.id_aruco_top_left:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 3, axis=1)
            stack.remove(camera_measurements.id_aruco_top_left)
        elif ids[ii] == camera_measurements.id_aruco_top_right:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 3, axis=1)
            stack.remove(camera_measurements.id_aruco_top_right)
        elif ids[ii] == camera_measurements.id_aruco_bottom_right:
            tmp_corners[ii] = np.roll(tmp_corners[ii], 2, axis=1)
            stack.remove(camera_measurements.id_aruco_bottom_right)
        elif ids[ii] == camera_measurements.id_aruco_playing_field_top:
            stack.remove(camera_measurements.id_aruco_playing_field_top)
        elif ids[ii] == camera_measurements.id_aruco_playing_field_bottom:
            stack.remove(camera_measurements.id_aruco_playing_field_bottom)

    if stack:
        raise ValueError("Missing ArUco markers: {}".format(stack))

    corners = tmp_corners
    return corners, ids, rejected


def get_pixel_to_mm(corners, ids):
    top_right = None
    playing_field_bottom = None
    bottom_right = None
    bottom_left = None
    for ii, id in enumerate(ids):
        if ids[ii] == camera_measurements.id_aruco_bottom_left:
            bottom_left = corners[ii][:, 0]
        elif ids[ii] == camera_measurements.id_aruco_top_left:
            playing_field = corners[ii][0]
        elif ids[ii] == camera_measurements.id_aruco_top_right:
            top_right = corners[ii][0]
        elif ids[ii] == camera_measurements.id_aruco_bottom_right:
            bottom_right = corners[ii][:, 0]

    # Calculate the number of pixels from the corners of the ArUco markers.
    x_diff = (bottom_right - bottom_left)[0, 0]
    y_diff = (bottom_right - top_right)[0, 1]
    # Have to take into account the white padding surrounding the marker
    x_length_mm = camera_measurements.mm_x_corner_to_corner
    y_length_mm = camera_measurements.mm_y_corner_to_corner
    # x_length_mm -= camera_measurements.mm_aruco_padding*2
    # y_length_mm += camera_measurements.mm_aruco_padding*2
    pixel_to_mm_x = x_length_mm / x_diff
    pixel_to_mm_y = y_length_mm / y_diff
    print("Pixel to mm x: {}".format(pixel_to_mm_x))
    print("Pixel to mm y: {}".format(pixel_to_mm_y))
    return pixel_to_mm_x, pixel_to_mm_y


if __name__ == "__main__":
    generate_markers()

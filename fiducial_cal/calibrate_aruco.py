from aruco import calibrate_aruco
from utils import load_coefficients, save_coefficients
import cv2




# Parameters
IMAGES_DIR = 'path_to_images'
IMAGES_FORMAT = '.jpg'
# Dimensions in cm
MARKER_LENGTH = 3
MARKER_SEPARATION = 0.25

# Calibrate
ret, mtx, dist, rvecs, tvecs = calibrate_aruco(
    IMAGES_DIR,
    IMAGES_FORMAT,
    MARKER_LENGTH,
    MARKER_SEPARATION
)
# Save coefficients into a file
save_coefficients(mtx, dist, "calibration_aruco.yml")

# Load coefficients
mtx, dist = load_coefficients('calibration_aruco.yml')
original = cv2.imread('image.jpg')
dst = cv2.undistort(img, mtx, dist, None, None)
cv2.imwrite('undist.jpg', dst)

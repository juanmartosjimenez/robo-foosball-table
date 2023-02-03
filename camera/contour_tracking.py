import cv2
import time
import numpy as np
import pyrealsense2 as rs
from utilities import start_pipe, rgb_to_hsv, get_hsv_range
import imutils

"""
Tracks a specific color object in the camera view using HSV color space and contour detection.
"""

pipe = start_pipe()

def start_stream():
    start_time = time.time()
    count = 0
    while True:
        if time.time() - start_time > 1:
            start_time = time.time()
            print("FPS: ", count)
            count = 0
        count += 1
        frames = pipe.wait_for_frames()
        rs_frame = frames.get_color_frame()
        if not rs_frame:
            continue

        bgr_frame = np.asanyarray(rs_frame.get_data())
        bgr_frame = cv2.GaussianBlur(bgr_frame, (5, 5), 0)
        # cv2.imshow("Color frame", color_image)
        hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
        # Thresholding
        lower_hsv, higher_hsv = get_hsv_range((235, 100, 48))
        mask = cv2.inRange(hsv, (100, 0, 69), (199, 31, 255))
        #mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours
        circles = cv2.HoughCircles(mask.copy(), cv2.HOUGH_GRADIENT, 1, 450, param1=300, param2=20, minRadius=20, maxRadius=30)
        # Draw detected circles
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                # Change the parameters to select the circle that is needed in the frame
                # Here I am selecting only the circles above 300 px in the x axis
                if i[0] > 300:
                    # print('Circle center - {} , {} -- Radius {}'.format(i[0],i[1],i[2]))
                    # Draw circle around the ball
                    cv2.circle(bgr_frame, (i[0], i[1]), i[2], (0, 255, 0), 2)
                    r = i[2]

        # Display the result
        cv2.imshow("Mask", mask)
        cv2.imshow("Frame", bgr_frame)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break



start_stream()
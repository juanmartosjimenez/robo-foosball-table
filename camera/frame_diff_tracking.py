import cv2
import time
import numpy as np
import pyrealsense2 as rs
from utilities import get_hsv_range, start_pipe
import imutils

"""
Tracks objects using the difference in between a "standard" frame and the current frame.
Any differences that exceed a certain threshold are highlighted using contours.
"""

pipe = start_pipe()


def get_calibration_frame():
    """
    Gets standard calibration frame with no obstacles on table.
    :return:
    """
    while True:
        frames = pipe.wait_for_frames()
        if frames:
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            color_image = np.asanyarray(color_frame.get_data())
            color_image = cv2.GaussianBlur(color_image, (5, 5), 0)
            return color_image


def start_stream():
    start_time = time.time()
    fps_count = 0
    cal_frame = get_calibration_frame()
    input("Press enter to start tracking")
    # cv2.imshow("Calibration frame", cal_frame)

    while True:
        if time.time() - start_time > 1:
            start_time = time.time()
            print("FPS: ", fps_count)
            fps_count = 0
        fps_count += 1
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = np.asanyarray(color_frame.get_data())
        color_image = cv2.GaussianBlur(color_image, (5, 5), 0)
        diff = cv2.absdiff(cal_frame, color_image)
        cv2.imshow("Diff", diff)
        # cv2.imshow("Color frame", color_image)
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        # Thresholding
        lower_hsv, higher_hsv = get_hsv_range((235, 100, 48))
        mask = cv2.inRange(hsv, lower_hsv, higher_hsv)
        # mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        if not cnts:
            cv2.imshow("Frame", color_image)
            key = cv2.waitKey(1)
            continue

        # Find the largest contour
        c = max(cnts, key=cv2.contourArea)

        # Find the center of the ball
        M = cv2.moments(c)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0

        # Draw the ball
        cv2.drawContours(color_image, [c], -1, (0, 255, 0), 2)
        cv2.circle(color_image, (cX, cY), 5, (255, 0, 0), -1)

        # Display the result
        cv2.imshow("Mask", mask)
        cv2.imshow("Frame", color_image)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break


start_stream()

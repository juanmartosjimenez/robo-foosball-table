import cv2
import time
import numpy as np
import pyrealsense2 as rs

"""
Tracks a specific color object in the camera view using HSV color space and contour detection.
"""

# Initialize Camera Intel Realsense
config = rs.config()
config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 60)


def rgb_to_hsv(rgb):
    rgb = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv[0][0]

def start_stream():
    pipe = rs.pipeline()
    profile = pipe.start(config)
    start_time = time.time()
    total_frames = 0
    count = 0
    target_object_rgb = rgb_to_hsv((235, 100, 48))
    lower_hsv = np.array((target_object_rgb[0] - 40, target_object_rgb[1] - 40, target_object_rgb[2] - 20))
    higher_hsv = np.array((target_object_rgb[0] + 40, target_object_rgb[1] + 40, target_object_rgb[2] + 20))
    print(lower_hsv, higher_hsv)
    while True:
        if time.time() - start_time > 1:
            start_time = time.time()
            print("FPS: ", count)
            count = 0
        count += 1
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        if total_frames < 100:
            total_frames += 1
            continue

        color_image = np.asanyarray(color_frame.get_data())
        color_image = cv2.GaussianBlur(color_image, (5, 5), 0)
        # cv2.imshow("Color frame", color_image)
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        # Thresholding
        mask = cv2.inRange(hsv, lower_hsv, higher_hsv)
        #mask = cv2.erode(mask, None, iterations=2)
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
        cv2.imshow("Frame", color_image)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break

start_stream()
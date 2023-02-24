import math
import multiprocessing
import queue
import time
from collections import deque
from typing import Optional

import cv2
import imutils
import numpy as np
from camera.aruco import detect_markers, get_pixel_to_mm, draw_markers
import pyrealsense2 as rs

from camera.camera_measurements import CameraMeasurements
from other.events import CameraEvent


class CameraManager:
    """
    Class to interface with the camera
    """

    def __init__(self):
        # Start the camera pipe
        self.pipe: Optional[rs.pipeline] = None
        self.__start_pipe()
        self.camera_measurements = CameraMeasurements()
        # Detect aruco markers
        rgb_frame = self.read_color_frame()
        # Detect aruco markers
        self.corners, self.ids, self.rejected = detect_markers(rgb_frame)
        # Calculate ratio of pixels to mm
        self.pixel_to_mm_x, self.pixel_to_mm_y = get_pixel_to_mm(self.corners, self.ids)

    def draw_aruco_markers(self):
        # Draw the aruco markers
        rgb_frame = self.read_color_frame()
        corners, ids, rejected = detect_markers(rgb_frame)
        draw_markers(ids, corners, rgb_frame)
        cv2.imshow("aruco", rgb_frame)
        cv2.waitKey(1)

    def event_loop(self, queue_to_camera: multiprocessing.Queue, queue_from_camera: multiprocessing.Queue):
        self.queue_to_camera = queue_to_camera
        self.queue_from_camera = queue_from_camera
        while True:
            time.sleep(0.01)
            try:
                data = queue_to_camera.get_nowait()
                event = data[0]
                if event == CameraEvent.START_BALL_TRACKING:
                    queue_from_camera.put(("message", "Ball tracking started"))
                    self.start_ball_tracking()
                else:
                    raise ValueError(f"Unknown event {str(event)}")
            except queue.Empty:
                pass

    def rgb_to_hsv(self, rgb):
        rgb = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        return hsv[0][0]
    def get_hsv_range(self, rgb: tuple) -> tuple[np.ndarray, np.ndarray]:
        target_object_rgb = self.rgb_to_hsv(rgb)
        lower_hsv = np.array((target_object_rgb[0] - 50, target_object_rgb[1] - 50, target_object_rgb[2] - 50))
        higher_hsv = np.array((target_object_rgb[0] + 50, target_object_rgb[1] + 50, target_object_rgb[2] + 50))
        return lower_hsv, higher_hsv
    def start_ball_tracking(self):
        # Returns an array of a given length containing the most recent center points,
        # or "None" if there are less stored points than the given number
        def lastPts(num):
            lastPts = []
            if num > len(pts):
                return None
            else:
                for i in range(num):
                    lastPts.append(pts[len(pts) - (1 + (num - i))])
                return lastPts

        # Define the lower and upper HSV boundaries of the foosball and initialize
        # the list of center points
        greenLower, greenUpper = self.get_hsv_range((235, 100, 48))
        pts = deque(maxlen=64)
        draw = True

        # Initialize variables and loop to continuously get and process video
        endX = 150
        frameNum = 0
        while True:
            frameNum += 1

            # Get the RealSense frame to be processed by OpenCV
            frame = self.read_color_frame()

            # Resize and blur the frame, then convert to HSV
            # Why do we resize the frame?
            # frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Construct color mask, then erode and dilate to clean up extraneous
            # contours
            mask = cv2.inRange(hsv, greenLower, greenUpper)
            # mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # Find all contours in the mask and initialize the center
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            if not cnts:
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1)
                continue

            # Find the largest contour
            c = max(cnts, key=cv2.contourArea)

            # Find the center of the ball
            M = cv2.moments(c)
            if M["m00"] != 0:
                cY = int(M["m10"] / M["m00"])
                cX = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0
            self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS, {"pixel": (cX, cY), "mm": self.convert_pixels_to_mm_playing_field(cX, cY)}))
            self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (cX, cY), "mm": self.convert_pixels_to_mm_playing_field(cX, cY)})) #TODO Delete

            # Draw the ball
            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cX, cY), 5, (255, 0, 0), -1)

            # Display the result
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1)
            continue

            # Update the list of centers, removing the oldest one every 3 frames if
            # there are more than 10 stored
            if center:
                pts.appendleft(center)
            if frameNum == 3:
                if len(pts) > 10:
                    pts.pop()
                frameNum = 0

            # Calculate the average change in x per change in y in order to predict
            # the ball's path
            last10Pts = lastPts(10)
            if last10Pts:
                xAvg = 0
                yAvg = 0
                last10Pts = lastPts(10)
                for i in range(9):
                    xAvg += (last10Pts[i][1] - last10Pts[i + 1][1])
                    yAvg = yAvg + (last10Pts[i][0] - last10Pts[i + 1][0])

                if yAvg > 0:
                    xAvg = xAvg / yAvg
                else:
                    xAvg = 0
                endX = pts[-1][1] + (xAvg * (600 - pts[-1][0]))
                # self.queue_from_camera.put(("goalie_ball_pos", self.convert_pixels_to_mm(endX, 0)[0])) TODO uncomment
            # Display the current frame
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

    def __start_pipe(self):
        """
        Starts realsense pipeline and returns it. When a pipe is started, it takes a few frames to for the camera to adjust
        to lighting conditions. Wait until 40 frames have been captured before returning the pipe.
        :return:
        """
        config = rs.config()
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 60)
        pipe = rs.pipeline()
        pipe.start(config)
        total_frames = 0
        while True:
            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            if total_frames < 40:
                total_frames += 1
                continue
            else:
                break
        self.pipe = pipe

    def read_color_frame(self) -> np.ndarray:
        """
        Wait until color frame is available and return it.
        :param pipe:
        :return:
        """
        while True:
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            else:
                return np.asanyarray(color_frame.get_data())

    def get_intrinsics(self):
        return self.pipe.get_active_profile().get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

    def convert_pixels_to_mm(self, x, y):
        # Do 540 - x so pixel 0, 0 is on the bottom right.
        out = round((540 - x) / self.pixel_to_mm_x, 2), round(y / self.pixel_to_mm_y, 2)
        return out

    def convert_pixels_to_mm_playing_field(self, x, y):
        # Get mm coords relative to the foosball table boundaries.
        # Assume that aruco marker is perfectly aligned with corners of the table. TODO fix this assumption, place
        # aruco marker in the middle of the table and use this value to calculate offset.
        bottom_left_x = 0
        bottom_right_y = 0
        for ii, id in enumerate(self.ids):
            if id[0] == self.camera_measurements.id_aruco_bottom_left:
                # Get corner pixel value
                bottom_left_x = self.corners[ii][:, 0][0][0]
            if id[0] == self.camera_measurements.id_aruco_bottom_right:
                bottom_right_y = self.corners[ii][:, 0][0][1]

        out = round((540 - x - bottom_left_x) / self.pixel_to_mm_x, 2), round((y - bottom_right_y) / self.pixel_to_mm_y, 2)
        return out

if __name__ == "__main__":
    camera_manager = CameraManager()
    camera_manager.draw_aruco_markers()

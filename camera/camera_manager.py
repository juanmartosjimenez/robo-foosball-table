import multiprocessing
import queue
from collections import deque
from typing import Optional

import cv2
import imutils
import numpy as np
from aruco import detect_markers, get_pixel_to_mm
import pyrealsense2 as rs

from camera.ball_tracking_with_trajectory import ball_tracking


class CameraManager:
    """
    Class to interface with the camera
    """

    def __init__(self):
        # Start the camera pipe
        self.pipe: Optional[rs.pipeline] = None
        self.__start_pipe()
        # Detect aruco markers
        rgb_frame = self.read_color_frame()
        # Detect aruco markers
        self.corners, self.ids, self.rejected = detect_markers(rgb_frame)
        # Calculate ratio of pixels to mm
        self.pixel_to_mm_x, self.pixel_to_mm_y = get_pixel_to_mm(self.corners, self.ids)

    def event_loop(self, queue_to_camera: multiprocessing.Queue, queue_from_camera: multiprocessing.Queue):
        while True:
            try:
                data = queue_to_camera.get_nowait()
                event = data[0]
                if event == 'start_ball_tracking':
                    self.start_ball_tracking()
                    queue_from_camera.put(("message", "Ball tracking started"))
                else:
                    print("Unknown event: " + event)
            except queue.Empty:
                pass


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
        greenLower = (0, 90, 160)
        greenUpper = (200, 167, 255)
        pts = deque(maxlen=64)

        # Initialize variables and loop to continuously get and process video
        endX = 150
        frameNum = 0
        while True:
            frameNum += 1

            # Get the RealSense frame to be processed by OpenCV
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            frame = np.asanyarray(color_frame.get_data())

            # Resize and blur the frame, then convert to HSV
            # Why do we resize the frame?
            # frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Construct color mask, then erode and dilate to clean up extraneous
            # contours
            mask = cv2.inRange(hsv, greenLower, greenUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # Find all contours in the mask and initialize the center
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None

            # Initialize the best contour to none, then search for the best one
            bestContour = None
            if len(cnts) > 0:
                bestContour = cnts[0]
                foundContour = False

                # Remove all contours not in area of interest
                for c in cnts:
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    if center[0] > 160 and center[0] < 500 and center[1] > 40 and center[1] < 300:
                        if cv2.contourArea(bestContour) < cv2.contourArea(c):
                            foundContour = True
                            bestContour = c

                # If found a contour in the area of interest, find and set the center
                if foundContour:
                    c = bestContour
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    self.queue_from_camera.put(("ball_pos", self.convert_pixels_to_mm(center[0], center[1])))
                else:
                    center = None

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
                self.queue_from_camera.put(("goalie_ball_pos", self.convert_pixels_to_mm(endX,0)[0]))

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
        return x / self.pixel_to_mm_x, y / self.pixel_to_mm_y

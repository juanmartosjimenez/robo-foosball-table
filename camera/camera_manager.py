import json
import multiprocessing
import os
import queue
import time
from collections import deque
from typing import Optional
from math import sqrt

import cv2
import imutils
import numpy as np
from camera.aruco import detect_markers, get_pixel_to_mm, draw_markers, pose_estimation
import pyrealsense2 as rs

from camera.camera_measurements import CameraMeasurements
from other.events import CameraEvent


class CameraManager:
    """
    Class to interface with the camera
    """

    def __init__(self, stop_flag: multiprocessing.Event = None, queue_to_camera: multiprocessing.Queue = None,
                 queue_from_camera: multiprocessing.Queue = None):
        self.pixel_bottom_left_corner, self.pixel_top_left_corner, self.pixel_top_right_corner, self.pixel_bottom_right_corner = (None, None, None, None)
        self.corners, self.ids, self.rejected = (None, None, None)
        self.pixel_to_mm_x, self.pixel_to_mm_y = (None, None)


        # Start the camera pipe
        self.pipe: Optional[rs.pipeline] = None
        # Load camera measurements
        self.camera_measurements = CameraMeasurements()
        # Start the Realsense camera pipe
        self.__start_pipe()
        # Read an RGB frame from the camera
        self.rgb_frame = self.read_color_frame()
        # Detect the field corners
        self.detect_field_corners()
        # Calculate the pixel to mm ratio
        self.calculate_pixel_to_mm()
        self.stop_flag: multiprocessing.Event = stop_flag
        self.queue_to_camera: Optional[multiprocessing.Queue] = queue_to_camera
        self.queue_from_camera: Optional[multiprocessing.Queue] = queue_from_camera

    def draw_aruco_markers(self):
        # Draw the aruco markers
        draw_markers(self.ids, self.corners, self.rgb_frame)
        cv2.imshow("aruco", self.rgb_frame)
        cv2.waitKey(1)

    def event_loop(self):
        while True:
            if self.stop_flag.is_set():
                try:  # Try to close the pipe
                    self.pipe.stop()
                except:
                    pass
                return
            try:
                data = self.queue_to_camera.get_nowait()
                event = data[0]
                if event == CameraEvent.START_BALL_TRACKING:
                    self.queue_from_camera.put(("message", "Ball tracking started"))
                    self.start_ball_tracking()
                else:
                    raise ValueError(f"Unknown camera_manager event {str(data)}")
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
        # -----Constants-----
        # If algo predicts that it will take this many frames or less for ball to
        #   cross goal line, send move command to predicted position, else send
        #   current position
        sendMoveFrameThresh = 60

        # The maximum size that a contour can be to considered a ball by algo
        maxContourSize = 1000

        # The number of frames before the ball is predicted to pass the goalie
        #   that the kick command will be sent (0 means command will be sent right
        #   when ball reaches goalie)
        kickFrameDelay = 10

        # Define the lower and upper HSV boundaries of the foosball and initialize
        # the list of center points
        color_mask_lower = (0, 91, 170)
        color_mask_upper = (2, 174, 255)
        pts = deque(maxlen=10)

        # Initialize variables and loop to continuously get and process video
        end_y = 250
        frame_count = 0
        start_time = time.time()
        last_pos_sent = 250
        frame_num = 0
        x_speed = 0
        last_x = 0
        ball_reset = True
        # Detect aruco markers
        self.corners, self.ids, self.rejected = detect_markers(self.rgb_frame)
        # Calculate ratio of pixels to mm
        self.pixel_to_mm_x, self.pixel_to_mm_y = get_pixel_to_mm(
            self.corners, self.ids)
        while True:
            if self.stop_flag.is_set():
                return
            if time.time() - start_time > 1:
                self.queue_from_camera.put((CameraEvent.FPS, frame_count))
                frame_count = 0
                start_time = time.time()

            frame_count += 1
            frame_num += 1

            # Get the RealSense frame to be processed by OpenCV
            frame = self.read_color_frame()
            # color_frame = frames.get_color_frame()
            # frame = np.asanyarray(color_frame.get_data())

            # Resize and blur the frame, then convert to HSV
            # frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Construct color mask, then erode and dilate to clean up extraneous
            # contours
            mask = cv2.inRange(hsv, color_mask_lower, color_mask_upper)
            mask = cv2.dilate(mask, None, iterations=2)

            # Find all contours in the mask and initialize the center
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            cv2.line(frame, (140, 55), (800, 55), (0, 0, 255), 1)
            cv2.line(frame, (140, 55), (140, 450), (0, 0, 255), 1)
            cv2.line(frame, (140, 450), (800, 450), (0, 0, 255), 1)
            cv2.line(frame, (800, 450), (800, 55), (0, 0, 255), 1)

            # Initialize the best contour to none, then search for the best one
            contoursInAOI = []
            bestCenter = None
            if len(cnts) > 0:
                bestContour = None
                # Remove all contours not in area of interest
                for c in cnts:
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    if center[0] > 140 and center[0] < 800 and center[1] > 55 and center[1] < 450 and cv2.contourArea(
                            c) < maxContourSize:
                        contoursInAOI.append(c)
                        if bestContour is None or cv2.contourArea(bestContour) <= cv2.contourArea(c):
                            bestContour = c
                            bestCenter = center

                cv2.drawContours(frame, contoursInAOI, -1, (255, 0, 0), 10)
                cv2.drawContours(frame, cnts, -1, (0, 255, 0), 3)

            # Update the list of centers, removing the oldest one every 10 frames if
            # there is more than 1 stored.
            if bestCenter:
                # TODO delete this not using the predicted trajectory for now.
                self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS, {"pixel": (bestCenter[1], bestCenter[0]),
                                                                           "mm": self.convert_pixels_to_mm_playing_field(
                                                                               bestCenter[1], bestCenter[0])}))
                last_x = bestCenter[0]
                # self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (bestCenter[1], bestCenter[0]),
                # "mm": self.convert_pixels_to_mm_playing_field(
                # bestCenter[1], bestCenter[0])}))
                if len(pts) < 2 or sqrt(((bestCenter[0] - pts[-1][0]) ** 2) + ((bestCenter[1] - pts[-1][1])) ** 2) > 7:
                    pts.appendleft(bestCenter)
            if frame_num == 10:
                if len(pts) > 2:
                    pts.pop()
                frame_num = 0

            # Visually connect all the stored center points with lines
            for i in range(1, len(pts)):
                thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

            # Calculate the average change in x per change in y in order to predict
            # the ball's path
            xAvg = 0
            yAvg = 0
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    yAvg += (pts[i][1] - pts[i + 1][1])
                    xAvg += (pts[i][0] - pts[i + 1][0])

                x_speed = xAvg / (len(pts) - 1)

                if bestCenter:
                    cv2.arrowedLine(frame, (bestCenter[0], bestCenter[1]),
                                    (round(bestCenter[0] + xAvg), round(bestCenter[1] + yAvg)), (255, 0, 0), 5)

                if xAvg > 0:
                    yAvg = yAvg / xAvg
                else:
                    yAvg = 0
                end_y = pts[-1][1] + (yAvg * (800 - pts[-1][0]))
                # self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (end_y, 540), "mm": self.convert_pixels_to_mm_playing_field(end_y, 540)}))

            # Draw a circle where the ball is expected to cross the goal line
            cv2.circle(frame, (800, max(min(round(end_y), 450), 55)), 10, (255, 0, 0), -1)

            # Logic to choose what move command to send.
            # If the calculated x component of speed implies that ball will
            #   cross goal line within the next 60 frames, send the predicted
            #   y position, else send the current y position
            if bestCenter:
                posToSend = last_pos_sent
                if bestCenter[0] + (xAvg * sendMoveFrameThresh) >= 800:
                    posToSend = max(min(round(end_y), 450), 55) if abs(
                        last_pos_sent - max(min(round(end_y), 450), 55)) >= 10 else last_pos_sent
                else:
                    posToSend = bestCenter[1] if abs(last_pos_sent - bestCenter[1]) >= 10 else last_pos_sent
                cv2.circle(frame, (800, posToSend), 10, (255, 0, 0), -1)
                if posToSend != last_pos_sent:
                    pass
                    # TODO uncomment
                    # self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS, {"pixel": (posToSend, 540),
                    # "mm": self.convert_pixels_to_mm_playing_field(
                    # posToSend, 540)}))

            # Logic to send kick command
            if last_x + (kickFrameDelay * x_speed) >= 800 and ball_reset:
                # TODO: Replace with sending kick event
                self.queue_from_camera.put((CameraEvent.STRIKE, None))
                print("Kick")
                ball_reset = False

            # Detect when ball is reset to allow kick command to be sent again
            if bestCenter and bestCenter[0] < 200:
                ball_reset = True

            # Display the current frame
            cv2.imshow("Frame", frame)
            cv2.imshow("Mask", mask)
            key = cv2.waitKey(1) & 0xFF

    def __start_pipe(self):
        """
        Starts realsense pipeline and returns it. When a pipe is started, it takes a few frames to for the camera to adjust
        to lighting conditions. Wait until 40 frames have been captured before returning the pipe.
        :return:
        """
        config = rs.config()
        config.enable_stream(rs.stream.color, self.camera_measurements.camera_resolution_y,
                             self.camera_measurements.camera_resolution_x, rs.format.bgr8,
                             self.camera_measurements.camera_fps)
        pipe = rs.pipeline()
        pipe.start(config)
        total_frames = 0
        while True:
            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            if total_frames < 60:
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

    def pose_estimation(self):
        pose_estimation(self.ids, self.corners, self.get_intrinsics(), self.rgb_frame)

    def convert_pixels_to_mm_playing_field(self, x, y):
        # Get mm coords relative to the foosball table boundaries.

        # Get aruco padding in pixels
        pixel_aruco_padding = self.camera_measurements.mm_aruco_padding / self.pixel_to_mm_x
        y_perspective_compensation = self.camera_measurements.y_perspective_compensation / self.pixel_to_mm_y

        # Gets corner of table pixel value.
        playing_field_bottom_y = 0
        playing_field_bottom_x = 0
        for ii, id in enumerate(self.ids):
            if id[0] == self.camera_measurements.id_aruco_bottom_right:
                playing_field_bottom_y = self.corners[ii][:, 0][0][1] + pixel_aruco_padding + y_perspective_compensation
            if id[0] == self.camera_measurements.id_aruco_playing_field_bottom:
                # Have to add the white padding behind the aruco marker.
                playing_field_bottom_x = self.corners[ii][:, 0][0][0] + pixel_aruco_padding

        # cv2.circle(self.rgb_frame, (int(playing_field_bottom_x), int(playing_field_bottom_y)), 10, (255, 0, 0), -1)
        # show frame

        # print(playing_field_bottom_x)
        # Camera 0 pixel is at the top right so subtract camera resolution to get bottom right point.
        out = round((self.camera_measurements.camera_resolution_x - x - (
                self.camera_measurements.camera_resolution_x - playing_field_bottom_x)) / self.pixel_to_mm_x,
                    2), round((y - playing_field_bottom_y) / self.pixel_to_mm_y, 2)
        return out

    def detect_field_corners(self):
        frame = self.read_color_frame()
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        color_mask_lower = (26, 70, 116)
        color_mask_upper = (76, 255, 255)

        # Construct color mask, then erode and dilate to clean up extraneous
        # contours
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.inRange(hsv, color_mask_lower, color_mask_upper)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
        # cv2.imshow('Mask', mask)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        good_contours = []
        for ii, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 10000:
                cv2.fillPoly(mask, pts=[contour], color=(0, 0, 0))
                continue
            else:
                good_contours.append(contour)
        if len(good_contours) != 1:
            print("Failed to detect contours using last saved values")
            if os.path.exists("corners.json"):
                with open("corners.json", "r") as f:
                    box = json.load(f)
            else:
                return None
        else:
            c = good_contours[0]
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = box.astype(int)
            with open("corners.json", "w") as f:
                json.dump(box.tolist(), f)

        cv2.drawContours(frame, [box], 0, (0, 255, 0), 1)
        # Blue
        cv2.circle(frame, (box[0][0], box[0][1]), 10, (255, 0, 0), -1)
        # Red
        cv2.circle(frame, (box[1][0], box[1][1]), 10, (0, 0, 255), -1)
        # Green
        cv2.circle(frame, (box[2][0], box[2][1]), 10, (0, 255, 0), -1)
        # Purple
        cv2.circle(frame, (box[3][0], box[3][1]), 10, (221, 160, 221), -1)

        self.pixel_bottom_left_corner = (box[0][1], box[0][0])
        self.pixel_top_left_corner = (box[1][1], box[1][0])
        self.pixel_top_right_corner = (box[2][1], box[2][0])
        self.pixel_bottom_right_corner = (box[3][1], box[3][0])

        # Draw the contours on the original image
        #cv2.drawContours(frame, good_contours, -1, (0, 255, 0), 3)
        # cv2.imshow('Frame', frame)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def calculate_pixel_to_mm(self):
        self.pixel_to_mm_y = self.camera_measurements.mm_playing_field_y / (
                self.pixel_bottom_right_corner[1] - self.pixel_bottom_left_corner[1])
        self.pixel_to_mm_x = self.camera_measurements.mm_playing_field_x / (
                self.pixel_bottom_left_corner[0] - self.pixel_top_left_corner[0])


if __name__ == "__main__":
    camera_manager = CameraManager()
    camera_manager.detect_field_corners()

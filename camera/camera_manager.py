import json
import multiprocessing
import os
import queue
import time
from collections import deque
from typing import Optional, Iterable
from math import sqrt

import cv2
import imutils
import numpy as np
from camera.aruco import detect_markers, get_pixel_to_mm, draw_markers, pose_estimation
from other.prediction_model import calculate_end_pos
import pyrealsense2 as rs

from camera.camera_measurements import CameraMeasurements
from other.events import CameraEvent
from camera.ball_prediction import BallPrediction

# DATA FILES
CORNERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/corners.json")
GOALIE_X_POS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/goalie_x_pos.json")


class CameraManager:
    """
    Class to interface with the camera
    """

    def __init__(self, stop_flag: multiprocessing.Event = None, queue_to_camera: multiprocessing.Queue = None,
                 queue_from_camera: multiprocessing.Queue = None):
        self.pixel_bottom_left_corner: Optional[tuple] = None
        self.pixel_top_left_corner: Optional[tuple] = None
        self.pixel_top_right_corner: Optional[tuple] = None
        self.pixel_bottom_right_corner: Optional[tuple] = None
        self.corners, self.ids, self.rejected = (None, None, None)
        self.pixel_to_mm_x, self.pixel_to_mm_y = (None, None)
        self.goalie_x_pixel_position = None

        # Start the camera pipe
        self.pipe: Optional[rs.pipeline] = None
        # Load camera measurements
        self.camera_measurements = CameraMeasurements()
        # Start the Realsense camera pipe
        self.__start_pipe()
        # Read an RGB frame from the camera
        self.rgb_frame = self.read_color_frame()
        # Detect the field corners
        self.__detect_field_corners()
        self.__detect_goalie()
        # Calculate the pixel to mm ratio
        self.__calculate_pixel_to_mm()
        self.stop_flag: multiprocessing.Event = stop_flag
        self.queue_to_camera: Optional[multiprocessing.Queue] = queue_to_camera
        self.queue_from_camera: Optional[multiprocessing.Queue] = queue_from_camera
        playing_fields_x_pixels = self.pixel_top_right_corner[0] - self.pixel_top_left_corner[0]
        playing_fields_y_pixels = self.pixel_bottom_left_corner[1] - self.pixel_top_left_corner[1]
        self.ball_prediction = BallPrediction(playing_fields_x_pixels, playing_fields_y_pixels, self.camera_measurements.camera_fps, self.queue_from_camera, self.goalie_x_pixel_position, self.pixel_top_left_corner, 15)

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

    def draw_predicted_path(self, frame, pred):
        if pred is None:
            return
        elif isinstance(pred, (list, np.ndarray)):
            for ii, p in enumerate(pred):
                if ii == len(pred) - 1:
                    cv2.putText(frame, f"Point {str(ii + 1)} {str(p)}", p, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    break
                cv2.line(frame, p, pred[ii + 1], (0, 0, 255), 2)
                cv2.putText(frame, f"Point {str(ii+1)} {str(p)}", p, cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255, 255, 0), 1)

            cv2.circle(frame, (pred[0][0], pred[0][1]), 10, (0, 255, 255), -1)
            cv2.circle(frame, (pred[-1][0], pred[-1][1]), 10, (0, 255, 255), -1)
        else:
            cv2.circle(frame, (self.goalie_x_pixel_position, pred), 10, (0, 255, 0), -1)
            cv2.putText(frame, "Prediction", (self.goalie_x_pixel_position, pred), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 0, 0), 1)

    def start_ball_tracking(self):
        # Define the lower and upper HSV boundaries of the foosball and initialize
        # the list of center points
        mask1_lower = (0, 167, 118)
        mask1_upper = (10, 255, 255)
        mask2_lower = (160, 142, 134)
        mask2_upper = (255, 255, 255)

        pts = deque(maxlen=10)

        # Initialize variables and loop to continuously get and process video
        fps = 0
        fps_time = time.time()
        # Detect aruco markers
        # self.corners, self.ids, self.rejected = (None, None, None)
        old_pred = None
        # Calculate ratio of pixels to mm
        while True:
            if self.stop_flag.is_set():
                return
            # Get the RealSense frame to be processed by OpenCV
            frame = self.read_color_frame()
            fps += 1
            processing_time = time.time()
            if time.time() - fps_time > 1:
                self.queue_from_camera.put((CameraEvent.FPS, fps))
                fps = 0
                fps_time = time.time()

            # Get the region of interest, and only look for contours there in order to minimize computing necessity
            region_of_interest_mask = np.zeros(frame.shape, dtype=np.uint8)
            roi_corners = np.array([self.pixel_bottom_left_corner, self.pixel_top_left_corner,
                                    self.pixel_top_right_corner, self.pixel_bottom_right_corner])
            cv2.fillPoly(region_of_interest_mask, [roi_corners], (255, 255, 255))
            region_of_interest_frame = cv2.bitwise_and(frame, region_of_interest_mask)

            # Resize and blur the frame, then convert to HSV
            blurred = cv2.GaussianBlur(region_of_interest_frame, (5, 5), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Construct color mask, then erode and dilate to clean up extraneous
            # contours
            mask1 = cv2.inRange(hsv, mask1_lower, mask1_upper)
            mask2 = cv2.inRange(hsv, mask2_lower, mask2_upper)
            mask = cv2.bitwise_or(mask1, mask2)
            # cv2.imshow("region of interest", mask.copy())
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=2)

            # Find all contours in the mask and initialize the center

            cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            cv2.line(frame, self.pixel_bottom_left_corner, self.pixel_top_left_corner, (0, 0, 255), 1)
            cv2.putText(frame, "Bottom Left", self.pixel_bottom_left_corner, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.line(frame, self.pixel_top_left_corner, self.pixel_top_right_corner, (0, 0, 255), 1)
            cv2.putText(frame, "Top Left", self.pixel_top_left_corner, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.line(frame, self.pixel_top_right_corner, self.pixel_bottom_right_corner, (0, 0, 255), 1)
            cv2.putText(frame, "Top Right", self.pixel_top_right_corner, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.line(frame, self.pixel_bottom_right_corner, self.pixel_bottom_left_corner, (0, 0, 255), 1)
            cv2.putText(frame, "Bottom Right", self.pixel_bottom_right_corner, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)


            # Draw the goalie line
            cv2.line(frame, (self.goalie_x_pixel_position, self.pixel_top_right_corner[1]), (self.goalie_x_pixel_position, self.pixel_bottom_right_corner[1]), (0, 0, 255), 3)

            # Initialize the best contour to none, then search for the best one
            if len(cnts) == 1:
                best_contour = cnts[0]
                center, radius = cv2.minEnclosingCircle(best_contour)
                center = tuple(map(int, center))
                radius = int(radius)
                cv2.circle(frame, center, radius, (0, 0, 255), 2)
                M = cv2.moments(best_contour)
                ball_center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                self.ball_prediction.add_new(ball_center[0], ball_center[1])

                # Send the current ball position to the frontend.
                self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS, {"pixel": (ball_center[0], ball_center[1]),
                                                                           "mm": self.convert_pixels_to_mm_playing_field(
                                                                               ball_center[0], ball_center[1])}))
                # Draw the y ball position on the goalie line.
                cv2.circle(frame, (self.goalie_x_pixel_position, ball_center[1]), 10, (255, 0, 0), -1)
                cv2.putText(frame, "Actual", (self.goalie_x_pixel_position, ball_center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            else:
                self.ball_prediction.add_new_empty()

            pred = self.ball_prediction.get_predicted()
            if pred is not None:
                old_pred = pred
            self.draw_predicted_path(frame, old_pred)
            # Calculate the predicted ball position
            # end_y = calculate_end_pos(pts, self.camera_measurements.camera_fps, radius, self.pixel_top_left_corner[1], self.pixel_bottom_left_corner[1], self.goalie_x_pixel_position)
            #if end_y is not None:
                #self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (self.goalie_x_pixel_position, end_y), "mm": self.convert_pixels_to_mm_playing_field(self.goalie_x_pixel_position, end_y)}))

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
        config.enable_stream(rs.stream.color, self.camera_measurements.camera_resolution_x,
                             self.camera_measurements.camera_resolution_y, rs.format.bgr8,
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

    def convert_pixels_to_mm_playing_field(self, x_pixel, y_pixel):
        # TODO motors should not take these in the wrong order
        x_mm = round((self.camera_measurements.camera_resolution_x - x_pixel - (
                    self.camera_measurements.camera_resolution_x - self.pixel_bottom_right_corner[0]))/self.pixel_to_mm_x, 2)
        y_mm = round((self.camera_measurements.camera_resolution_y - y_pixel - (
                    self.camera_measurements.camera_resolution_y - self.pixel_bottom_right_corner[1]))/self.pixel_to_mm_y, 2)
        return y_mm, x_mm

    def __detect_goalie(self):
        frame = self.read_color_frame()
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        color_mask_lower = (78, 187, 161)
        color_mask_upper = (102, 255, 255)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.inRange(hsv, color_mask_lower, color_mask_upper)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) != 1:
            print("Failed to detect goalie using last saved values.")
            if os.path.exists(GOALIE_X_POS_FILE):
                with open(GOALIE_X_POS_FILE, "r") as f:
                    goalie_x_pos_file = json.load(f)
                    goalie_x_pos = goalie_x_pos_file["goalie_x_pixel_position"]
                    self.goalie_x_pixel_position = goalie_x_pos
            else:
                return None
        else:
            goalie_contour = contours[0]
            M = cv2.moments(goalie_contour)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            with open(GOALIE_X_POS_FILE, "w") as f:
                json.dump({"goalie_x_pixel_position": cX}, f)
            self.goalie_x_pixel_position = cX

    def __detect_field_corners(self):
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
            if os.path.exists(CORNERS_FILE):
                with open(CORNERS_FILE, "r") as f:
                    box = json.load(f)
                    box = np.array(box)
            else:
                return None
        else:
            c = good_contours[0]
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = box.astype(int)
            with open(CORNERS_FILE, "w") as f:
                json.dump(box.tolist(), f)

        cv2.drawContours(frame, [box], 0, (0, 255, 0), 1)
        # Blue
        cv2.circle(frame, box[0], 10, (255, 0, 0), -1)
        # Red
        cv2.circle(frame, box[1], 10, (0, 0, 255), -1)
        # Green
        cv2.circle(frame, box[2], 10, (0, 255, 0), -1)
        # Purple
        cv2.circle(frame, box[3], 10, (221, 160, 221), -1)

        # Label the different box vertices.

        # Sort based on y coordinate
        box = sorted(box, key=lambda x: x[1])

        # Upper values
        top_vertices = box[:2]
        bottom_vertices = box[2:]

        # Sort based on x coordinate.
        if top_vertices[0][0] > top_vertices[1][0]:
            self.pixel_top_left_corner = top_vertices[1]
            self.pixel_top_right_corner = top_vertices[0]
        else:
            self.pixel_top_left_corner = top_vertices[0]
            self.pixel_top_right_corner = top_vertices[1]

        if bottom_vertices[0][0] > bottom_vertices[1][0]:
            self.pixel_bottom_left_corner = bottom_vertices[1]
            self.pixel_bottom_right_corner = bottom_vertices[0]
        else:
            self.pixel_bottom_left_corner = bottom_vertices[0]
            self.pixel_bottom_right_corner = bottom_vertices[1]

        # Draw the contours on the original image
        #cv2.drawContours(frame, [box], -1, (0, 255, 0), 3)
        #cv2.imshow('Frame', frame)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def __calculate_pixel_to_mm(self):
        self.pixel_to_mm_x = (self.pixel_bottom_right_corner[0] - self.pixel_bottom_left_corner[
            0]) / self.camera_measurements.mm_playing_field_x
        self.pixel_to_mm_y = (self.pixel_bottom_right_corner[1] - self.pixel_top_right_corner[
            1]) / self.camera_measurements.mm_playing_field_y
        print("Pixel to mm x: ", self.pixel_to_mm_x)
        print("Pixel to mm y: ", self.pixel_to_mm_y)


if __name__ == "__main__":
    camera_manager = CameraManager()

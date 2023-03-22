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
        self.camera_measurements = CameraMeasurements()
        self.__start_pipe()
        # Detect aruco markers
        rgb_frame = self.read_color_frame()
        # Detect aruco markers
        self.corners, self.ids, self.rejected = detect_markers(rgb_frame)
        # Calculate ratio of pixels to mm
        self.pixel_to_mm_x, self.pixel_to_mm_y, self.playing_field_pixel_to_mm_x, self.playing_field_pixel_to_mm_y = get_pixel_to_mm(
            self.corners, self.ids)

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
<<<<<<< HEAD
        # Define the lower and upper HSV boundaries of the foosball and initialize
        # the list of center points
        #colorMaskLower = (0, 62, 123)
        #colorMaskUpper = (15, 253, 255)
        colorMaskLower = (0, 91, 170)
        colorMaskUpper = (2, 174, 255)
        pts = deque(maxlen=10)
    
=======
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

>>>>>>> juanmartosjimenez/closingloop
        # Initialize variables and loop to continuously get and process video
        endX = 150
        frameNum = 0
        while True:
            frameNum += 1
    
            # Get the RealSense frame to be processed by OpenCV
            frame = self.read_color_frame()
            #color_frame = frames.get_color_frame()
            #frame = np.asanyarray(color_frame.get_data())
    
            # Resize and blur the frame, then convert to HSV
<<<<<<< HEAD
            #frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
=======
            # Why do we resize the frame?
            # frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)
>>>>>>> juanmartosjimenez/closingloop
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    
            # Construct color mask, then erode and dilate to clean up extraneous
            # contours
<<<<<<< HEAD
            mask = cv2.inRange(hsv, colorMaskLower, colorMaskUpper)
=======
            mask = cv2.inRange(hsv, greenLower, greenUpper)
            # mask = cv2.erode(mask, None, iterations=2)
>>>>>>> juanmartosjimenez/closingloop
            mask = cv2.dilate(mask, None, iterations=2)
    
            # Find all contours in the mask and initialize the center
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
<<<<<<< HEAD
            cnts = imutils.grab_contours(cnts)
    
            cv2.line(frame, (120, 55), (800, 55), (0, 0, 255), 1)
            cv2.line(frame, (120, 55), (120, 450), (0, 0, 255), 1)
            cv2.line(frame, (120, 450), (800, 450), (0, 0, 255), 1)
            cv2.line(frame, (800, 450), (800, 55), (0, 0, 255), 1)
    
            # Initialize the best contour to none, then search for the best one
            contoursInAOI = []
            foundContour = False
            bestCenter = None
            if len(cnts) > 0:
                bestContour = None
                # Remove all contours not in area of interest
                for c in cnts:
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    if center[0] > 120 and center[0] < 800 and center[1] > 55 and center[1] < 450 and cv2.contourArea(c) < 550:
                        foundContour = True
                        #print(cv2.contourArea(c))
                        contoursInAOI.append(c)
                        if bestContour is None or cv2.contourArea(bestContour) <= cv2.contourArea(c):
                            bestContour = c
                            bestCenter = center
                
                cv2.drawContours(frame, contoursInAOI, -1, (255, 0, 0), 10)
                cv2.drawContours(frame, cnts, -1, (0, 255, 0), 3)
            # If found a contour in the area of interest, find and set the center
            if bestCenter:
                print(bestCenter)
            else:
                print("No Ball Found")
    
            # Update the list of centers, removing the oldest one every 3 frames if
            # there are more than 10 stored.
            if bestCenter:
                self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS, {"pixel": (center[0], center[1]), "mm": self.convert_pixels_to_mm_playing_field(center[0], center[1])}))
                if len(pts) < 2 or abs(bestCenter[0] - pts[-1][0]) > 3 or abs(bestCenter[1] - pts[-1][1]) > 3:
                    pts.appendleft(bestCenter)
=======

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
            self.queue_from_camera.put((CameraEvent.CURRENT_BALL_POS,
                                        {"pixel": (cX, cY), "mm": self.convert_pixels_to_mm_playing_field(cX, cY)}))
            self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (cX, cY),
                                                                         "mm": self.convert_pixels_to_mm_playing_field(
                                                                             cX, cY)}))  # TODO Delete

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
>>>>>>> juanmartosjimenez/closingloop
            if frameNum == 3:
                if len(pts) > 2:
                    pts.pop()
                frameNum = 0
<<<<<<< HEAD
    
            # Visually connect all the stored center points with lines
            for i in range(1, len(pts)):
                thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
    
=======

>>>>>>> juanmartosjimenez/closingloop
            # Calculate the average change in x per change in y in order to predict
            # the ball's path
            if len(pts) > 1:
                xAvg = 0
                yAvg = 0
<<<<<<< HEAD
                for i in range(len(pts) - 1):
                    yAvg += (pts[i][1] - pts[i + 1][1])
                    xAvg += (pts[i][0] - pts[i + 1][0])
    
                if bestCenter:
                    cv2.arrowedLine(frame, (bestCenter[0], bestCenter[1]), (round(bestCenter[0] + xAvg), round(bestCenter[1] + yAvg)), (255, 0, 0), 5)
    
                if xAvg > 0:
                    yAvg = yAvg / xAvg
                else:
                    yAvg = 0
                endY = pts[-1][1] + (yAvg * (800 - pts[-1][0]))
                
                self.queue_from_camera.put((CameraEvent.PREDICTED_BALL_POS, {"pixel": (endY, 540), "mm": self.convert_pixels_to_mm_playing_field(endY, 540)}))
    
            # Draw a circle where the ball is expected to cross the goal line
            cv2.circle(frame, (800, max(min(round(endY), 450), 55)), 10, (255, 0, 0), -1)

            # Display the current frame
            cv2.imshow("Frame", frame)
            cv2.imshow("Mask", mask)
=======
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
>>>>>>> juanmartosjimenez/closingloop
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

    def convert_pixels_to_mm_playing_field(self, x, y):
        # Get mm coords relative to the foosball table boundaries.
        # Assume that aruco marker is perfectly aligned with corners of the table. TODO fix this assumption, place
        # aruco marker in the middle of the table and use this value to calculate offset.

        # Get aruco padding in pixels
        pixel_aruco_padding = self.camera_measurements.mm_aruco_padding / self.playing_field_pixel_to_mm_x

        # Gets corner of table pixel value.
        bottom_left_x = 0
        bottom_right_y = 0
        playing_field_bottom_x = 0
        for ii, id in enumerate(self.ids):
            if id[0] == self.camera_measurements.id_aruco_bottom_left:
                # Get corner pixel value
                bottom_left_x = self.corners[ii][:, 0][0][0]
            if id[0] == self.camera_measurements.id_aruco_bottom_right:
                bottom_right_y = self.corners[ii][:, 0][0][1]
            if id[0] == self.camera_measurements.id_aruco_playing_field_bottom:
                # Have to add the white padding behind the aruco marker.
                playing_field_bottom_x = self.corners[ii][:, 0][0][0] + pixel_aruco_padding

        # print(playing_field_bottom_x)
        # Camera 0 pixel is at the top right so subtract camera resolution to get bottom right point.
        out = round((self.camera_measurements.camera_resolution_x - x - (self.camera_measurements.camera_resolution_x - playing_field_bottom_x)) / self.playing_field_pixel_to_mm_x,
                    2), round((y - bottom_right_y) / self.playing_field_pixel_to_mm_y, 2)
        return out


if __name__ == "__main__":
    camera_manager = CameraManager()
    camera_manager.draw_aruco_markers()

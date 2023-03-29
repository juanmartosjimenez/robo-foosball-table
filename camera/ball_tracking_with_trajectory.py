import pyrealsense2 as rs
import cv2
from collections import deque
import numpy as np
import imutils
from math import sqrt


def ball_tracking(pipe: rs.pipeline, draw: bool = False):
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
    kickFrameDelay = 5
    
    # Define the lower and upper HSV boundaries of the foosball and initialize
    # the list of center points
    colorMaskLower = (0, 90, 177)
    colorMaskUpper = (210, 195, 255)
    pts = deque(maxlen=10)

    # Initialize variables and loop to continuously get and process video
    endY = 250
    lastPosSent = 250
    frameNum = 0
    xSpeed = 0
    lastX = 0
    ballReset = True
    while True:
        frameNum += 1

        # Get the RealSense frame to be processed by OpenCV
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        frame = np.asanyarray(color_frame.get_data())

        # Resize and blur the frame, then convert to HSV
        #frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Construct color mask, then erode and dilate to clean up extraneous
        # contours
        mask = cv2.inRange(hsv, colorMaskLower, colorMaskUpper)
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
                if center[0] > 140 and center[0] < 800 and center[1] > 55 and center[1] < 450 and cv2.contourArea(c) < maxContourSize:
                    contoursInAOI.append(c)
                    if bestContour is None or cv2.contourArea(bestContour) <= cv2.contourArea(c):
                        bestContour = c
                        bestCenter = center
            
            cv2.drawContours(frame, contoursInAOI, -1, (255, 0, 0), 10)
            cv2.drawContours(frame, cnts, -1, (0, 255, 0), 3)
        """
        else:
            print("No Contours Found")

        # If found a contour in the area of interest, find and set the center
        if foundContour:
            print(bestCenter)
        else:
            print("No Ball Found")
        """

        # Update the list of centers, removing the oldest one every 10 frames if
        # there is more than 1 stored.
        if bestCenter:
            lastX = bestCenter[0]
            if len(pts) < 2 or sqrt(((bestCenter[0] - pts[-1][0]) ** 2) + ((bestCenter[1] - pts[-1][1])) ** 2) > 7:
                pts.appendleft(bestCenter)
        if frameNum == 10:
            if len(pts) > 2:
                pts.pop()
            frameNum = 0

        # Visually connect all the stored center points with lines
        for i in range(1, len(pts)):
            thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
            if draw:
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

        # Calculate the average change in x per change in y in order to predict
        # the ball's path
        xAvg = 0
        yAvg = 0
        if len(pts) > 1:
            for i in range(len(pts) - 1):
                yAvg += (pts[i][1] - pts[i + 1][1])
                xAvg += (pts[i][0] - pts[i + 1][0])
            
            xSpeed = xAvg / (len(pts) - 1)

            if bestCenter:
                cv2.arrowedLine(frame, (bestCenter[0], bestCenter[1]), (round(bestCenter[0] + xAvg), round(bestCenter[1] + yAvg)), (255, 0, 0), 5)

            if xAvg > 0:
                yAvg = yAvg / xAvg
            else:
                yAvg = 0
            endY = pts[-1][1] + (yAvg * (800 - pts[-1][0]))
            
        # Logic to choose what move command to send.
        # If the calculated x component of speed implies that ball will
        #   cross goal line within the next 60 frames, send the predicted
        #   y position, else send the current y position
        if bestCenter:
            posToSend = lastPosSent
            if bestCenter[0] + (xSpeed * sendMoveFrameThresh) >= 800:
                posToSend = max(min(round(endY), 450), 55) if abs(lastPosSent - max(min(round(endY), 450), 55)) >= 10 else lastPosSent
                #cv2.circle(frame, (800, max(min(round(endY), 450), 55)), 10, (255, 0, 0), -1)
            else:
                posToSend = bestCenter[1] if abs(lastPosSent - bestCenter[1]) >= 10 else lastPosSent
                #cv2.circle(frame, (800, bestCenter[1]), 10, (255, 0, 0), -1)
            cv2.circle(frame, (800, posToSend), 10, (255, 0, 0), -1)
            
        # Logic to send kick command
        if lastX + (kickFrameDelay * xSpeed) >= 800 and ballReset:
            print("Kick")
            ballReset = False
            
        # Detect when ball is reset to allow kick command to be sent again
        if bestCenter and bestCenter[0] < 200:
            ballReset = True
            
        cv2.imshow("Frame", frame)
        cv2.imshow("Mask", mask)
        key = cv2.waitKey(1) & 0xFF

if __name__ == "__main__":
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)

    # Start streaming
    pipeline.start(config)

    try:
        ball_tracking(pipeline, draw=True)
    finally:
        pipeline.stop()

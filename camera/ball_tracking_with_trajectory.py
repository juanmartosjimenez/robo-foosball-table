import pyrealsense2 as rs
import cv2
from collections import deque
import numpy as np
import imutils
import time

# Initialize the realsense camera to ensure video is 60 fps
print("initializing realsense")
config = rs.config()
config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 60)
pipe = rs.pipeline()
profile = pipe.start(config)
print("success")

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

# Define the lower and upper HSV boundaries of the the foosball and initialize
# the list of center points
greenLower = (0, 90, 160)
greenUpper = (200, 167, 255)
pts = deque(maxlen=64)
    
# Wait for camera to warm up
time.sleep(2.0)

# Initialize variables and loop to continuously get and process video 
endX = 150
frameNum = 0
while True:
    frameNum += 1
    
    # Get the RealSense frame to be processed by OpenCV
    frames = pipe.wait_for_frames()
    color_frame = frames.get_color_frame()
    frame = np.asanyarray(color_frame.get_data())
    
    # Resize and blur the frame, then convert to HSV
    frame = imutils.resize(frame, width=600)
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
        
            # Draw the circle and centroid on the frame, then update the list
            # of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
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
    
    # Visually connect all the stored center points with lines
    for i in range(1, len(pts)):
        thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
    
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
        
    # Draw a circle where the ball is expected to cross the goal line    
    cv2.circle(frame, (590, max(min(round(endX), 590), 10)), 10, (255, 0, 0), -1)
        
    # Display the current frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

cv2.destroyAllWindows()
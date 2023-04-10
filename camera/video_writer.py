import cv2
import numpy as np


class VideoWriter:
    def __init__(self):
        # Default resolutions of the frame are obtained.The default resolutions are system dependent.
        # We convert the resolutions from float to integer.
        frame_width = 960
        frame_height = 540

        # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
        self.out = cv2.VideoWriter('outpy.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 23,
                                   (frame_width, frame_height))
        self.ii = 0

    def add_frame(self, frame):
        self.ii += 1

        self.out.write(frame)

    def close(self):
        self.out.release()

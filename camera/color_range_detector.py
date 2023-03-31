#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USAGE: You need to specify a filter and "only one" image source
#
# (python) range-detector --filter RGB --image /path/to/image.png
# or
# (python) range-detector --filter HSV --webcam

import cv2
import argparse
from operator import xor
import pyrealsense2 as rs
import numpy as np


def callback(value):
    pass


def setup_trackbars(range_filter):
    cv2.namedWindow("Trackbars", 0)

    for ii in range(2):
        for i in ["MIN", "MAX"]:
            v = 0 if i == "MIN" else 255

            for j in range_filter:
                cv2.createTrackbar("%s_%s_%s" % (str(ii),j, i), "Trackbars", v, 255, callback)


def get_trackbar_values(range_filter):
    values = []

    for ii in range(2):
        for i in ["MIN", "MAX"]:
            for j in range_filter:
                v = cv2.getTrackbarPos("%s_%s_%s" % (str(ii), j, i), "Trackbars")
                values.append(v)

    return values


def main():
    range_filter = "HSV"

    print("initializing realsense")
    config = rs.config()
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 60)
    pipe = rs.pipeline()
    profile = pipe.start(config)
    print("success")
    setup_trackbars(range_filter)

    while True:
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        bgr_frame = np.asanyarray(color_frame.get_data())
        frame_to_thresh = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)

        v1_min, v2_min, v3_min, v1_max, v2_max, v3_max , mask2_v1_min, mask2_v2_min, mask2_v3_min, mask2_v1_max, mask2_v2_max, mask2_v3_max = get_trackbar_values(range_filter)

        thresh = cv2.inRange(frame_to_thresh, (v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))
        thresh2 = cv2.inRange(frame_to_thresh, (mask2_v1_min, mask2_v2_min, mask2_v3_min), (mask2_v1_max, mask2_v2_max, mask2_v3_max))
        thresh = cv2.bitwise_or(thresh, thresh2)

        #if args['preview']:
            #preview = cv2.bitwise_and(image, image, mask=thresh)
            #cv2.imshow("Preview", preview)
        cv2.imshow("Original", bgr_frame)
        cv2.imshow("Thresh", thresh)

        if cv2.waitKey(1) & 0xFF is ord('q'):
            break


if __name__ == '__main__':
    main()
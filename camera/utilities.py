import cv2
import time
import numpy as np
import pyrealsense2 as rs


def rgb_to_hsv(rgb):
    rgb = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv[0][0]


def get_hsv_range(rgb: tuple):
    target_object_rgb = rgb_to_hsv(rgb)
    lower_hsv = np.array((target_object_rgb[0] - 40, target_object_rgb[1] - 40, target_object_rgb[2] - 20))
    higher_hsv = np.array((target_object_rgb[0] + 40, target_object_rgb[1] + 40, target_object_rgb[2] + 20))
    return lower_hsv, higher_hsv


def start_pipe():
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
    return pipe


def read_color_frame(pipe):
    """
    Wait until color frame is available and return it.
    :param pipe:
    :return:
    """
    while True:
        frames = pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        else:
            return np.asanyarray(color_frame.get_data())


def get_screenshot():
    pipe = start_pipe()
    color_frame = read_color_frame(pipe)
    pipe.stop()
    return color_frame

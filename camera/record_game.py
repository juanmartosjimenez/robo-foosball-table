import os
from multiprocessing import Queue
from camera.camera_measurements import CameraMeasurements


class RecordGame:
    def __init__(self, x_pixels, y_pixels, rate, playing_field_top_left):
        # Camera measurements
        self.camera_measurements = CameraMeasurements()
        # Total number of x pixels in the playing field.
        self.x_pixels = x_pixels
        # Total number of y pixels in the playing field.
        self.y_pixels = y_pixels
        # Rate at which new ball positions are added. Should be 60fps.
        self.rate = rate
        # Playing field top left pixel.
        self.playing_field_top_left = playing_field_top_left

        self.playing_field_top = self.playing_field_top_left[1]
        self.playing_field_bottom = self.playing_field_top_left[1] + self.y_pixels
        self.score = {"blue": 0, "black": 0}

        self.filename = None

    def __convert_to_playing_field_pixel(self, x_pixel, y_pixel):
        """
        Converts the pixel position of the ball to the pixel position of the ball relative to the playing field.
        :param x_pixel:
        :param y_pixel:
        :return:
        """
        x_pixel = x_pixel - self.playing_field_top_left[0]
        y_pixel = y_pixel - self.playing_field_top_left[1]
        return x_pixel, y_pixel

    def ball_writer(self, x_pixel, y_pixel, rate):
        # Writes current ball position to file.
        if x_pixel is None or y_pixel is None:
            return
        x_pixel, y_pixel = self.__convert_to_playing_field_pixel(x_pixel, y_pixel)
        filename = os.path.join(os.path.dirname(__file__), "data/game_" + str(self.score["blue"]) + "_" + str(self.score["black"]) + ".csv")
        with open(filename, "a+") as f:
            f.write(f"{str(x_pixel)},{str(y_pixel)},{rate}\n")

    def add_new(self, x_pixel, y_pixel, rate):
        self.ball_writer(x_pixel, y_pixel, rate)

    def goal_scored(self, team):
        if team == "blue":
            self.score["blue"] += 1
        elif team == "black":
            self.score["black"] += 1

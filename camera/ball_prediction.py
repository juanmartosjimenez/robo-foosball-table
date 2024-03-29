import os
import time
from multiprocessing import Queue
from typing import Optional, Tuple

import numpy as np

from camera.camera_measurements import CameraMeasurements
from other.events import CameraEvent

BALL_POSITION_FILE = os.path.join(os.path.dirname(__file__), "data/ball_positions.txt")


class BallPrediction:
    def __init__(self, x_pixels, y_pixels, rate, queue_from_camera: Queue, target_x_pixel, playing_field_top_left,
                 ball_radius):
        # Camera measurements
        self.camera_measurements = CameraMeasurements()
        # Total number of x pixels in the playing field.
        self.x_pixels = x_pixels
        # Total number of y pixels in the playing field.
        self.y_pixels = y_pixels
        # Rate at which new ball positions are added. Should be 60fps.
        self.rate = rate
        # Damping factor. Rate at which the ball slows down.
        self.damping = 0.85
        # Threshold speed. Speed at which prediction of ball is no longer taking into account but rather the current
        # ball position.
        self.threshold = 70
        # Restitution factor. Rate at which the ball bounces off the walls.
        self.restitution = 0.75        # Buffer to store current ball pixels.
        self.buffer = []
        # Predicted ball pixels.
        self.predicted_buffer = []
        # Queue used to send out
        self.queue_from_camera = queue_from_camera
        # X range threshold. Number of pixels apart from goalie for predicted path to be taken into account.
        self.x_range_threshold = self.camera_measurements.strike_zone_pixels
        # Playing field top left pixel.
        self.playing_field_top_left = playing_field_top_left

        self.playing_field_top = self.playing_field_top_left[1]
        self.playing_field_bottom = self.playing_field_top_left[1] + self.y_pixels

        # Target x pixel position. Position of the goalie bar.
        self.target_x_pixel = target_x_pixel
        # Ball radius in pixels.
        self.ball_radius = ball_radius
        # Time step in seconds.
        self.time_step = 0.2
        self.predicted_path = None

        if os.path.exists(BALL_POSITION_FILE):
            os.remove(BALL_POSITION_FILE)

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

    def ball_writer(self, x_pixel, y_pixel):
        # Writes current ball position to file.
        if x_pixel is None or y_pixel is None:
            return
        x_pixel, y_pixel = self.__convert_to_playing_field_pixel(x_pixel, y_pixel)
        with open(BALL_POSITION_FILE, "w") as f:
            f.write(f"{str(x_pixel)},{str(y_pixel)}\n")

    def add_new_empty(self):
        self.buffer.insert(0, None)
        # Remove old ball positions.
        if len(self.buffer) > 60:
            self.buffer = self.buffer[:20]

    def add_new(self, x_pixel, y_pixel):
        self.buffer.insert(0, (x_pixel, y_pixel))
        # Remove old ball positions.
        if len(self.buffer) > 60:
            self.buffer = self.buffer[:20]
        # Write ball position to file
        self.ball_writer(x_pixel, y_pixel)

    def _predict(self) -> Optional[Tuple]:
        """
        Predicts the ball position based on the current ball position and the previous ball position.
        :return: Y pixel position of the predicted ball position.
        """
        self.predicted_path = None
        # If more than two points are in the buffer, predict the ball position.
        if len(self.buffer) >= 2:
            curr_pos = self.buffer[0]
            prev_pos = self.buffer[1]

            # If the current position is None, the ball was not detected during this frame.
            if curr_pos is None:
                return None

            # If the ball is behind the target position then move to position and strike.
            if curr_pos[0] > self.target_x_pixel:
                return (curr_pos[1],)

            # The ball was not detected during the previous frame. So move to the current position.
            if prev_pos is None:
                return (curr_pos[1],)

            # If the ball is within the x range threshold, use the current ball position instead of predicting
            # trajectory.
            if self.target_x_pixel - curr_pos[0] < self.x_range_threshold:
                self.queue_from_camera.put_nowait((CameraEvent.QUICK_STRIKE, None))
                return (curr_pos[1],)

            # If change in position is less than the ball radius then ball is stationary and no change in position is
            # needed.
            if abs(curr_pos[0] - prev_pos[0]) < 2:
                # print("Ball is stationary")
                return None

            # print("Curr pos: ", curr_pos)
            # print("Prev pos: ", prev_pos)
            # Calculate the speed of the ball.
            x_speed = (curr_pos[0] - prev_pos[0]) / (1 / self.rate)
            y_speed = (curr_pos[1] - prev_pos[1]) / (1 / self.rate)

            # If x speed is negative then ball is going the wrong way.
            if x_speed < 0:
                return None

            predicted_trajectory = []
            x_pixel = curr_pos[0]
            y_pixel = curr_pos[1]
            predicted_trajectory.append((x_pixel, y_pixel))
            iterations = 0
            total_elapsed_time = 0
            x_prime = x_pixel
            y_prime = y_pixel
            # If the speed is less than the threshold, use the current ball position instead of predicting trajectory.
            while x_speed > self.threshold and x_prime != self.target_x_pixel:
                iterations += 1
                elapsed_time = 0
                x_speed = x_speed * self.damping
                y_speed = y_speed * self.damping
                while elapsed_time != self.time_step:
                    remaining_time = self.time_step - elapsed_time
                    # Calculate the next position of the ball after the time step.
                    x_prime = x_pixel + x_speed * remaining_time
                    y_prime = y_pixel + y_speed * remaining_time

                    # If the ball hits the top or bottom wall, bounce off the wall.
                    if y_prime <= self.playing_field_top or y_prime >= self.playing_field_bottom:
                        # Get the time step at which the ball hits the wall which is less than the default time step.
                        if y_prime >= self.playing_field_bottom:
                            # print("HIT BOTTOM WALL")
                            time_step_prime = abs((y_pixel - self.playing_field_bottom) / y_speed)
                            y_prime = self.playing_field_bottom - 1
                        elif y_prime <= self.playing_field_top:
                            # print("HIT TOP WALL")
                            time_step_prime = abs((self.playing_field_top - y_pixel) / y_speed)
                            y_prime = self.playing_field_top + 1
                        else:
                            raise ValueError("Ball is not hitting the top or bottom wall.")

                        # Calculate the next position of the ball after the time step.
                        x_prime = x_pixel + x_speed * time_step_prime

                        # If x position is past the target position, then find time to reach target position.
                        if x_prime >= self.target_x_pixel:
                            time_step_prime = abs((self.target_x_pixel - x_pixel) / x_speed)
                            y_prime = y_pixel + y_speed * time_step_prime
                            x_prime = self.target_x_pixel
                            predicted_trajectory.append((round(x_prime), round(y_prime)))
                            elapsed_time += time_step_prime
                            # print("BALL HIT TARGET", x_prime, y_prime, elapsed_time)
                            # Break because the ball has reached the target position.
                            break
                        else:
                            predicted_trajectory.append((round(x_prime), round(y_prime)))
                            elapsed_time += time_step_prime
                            # There is surely a more physics way of doing this but this works.
                            # Update the Y speed of the ball after bouncing off the wall.
                            # TODO test this. Multiplying by 1.3 because the ball bounces off the wall in a non linear
                            # way.
                            y_speed = -y_speed * self.restitution * 0.5
                            # Update the X speed of the ball after bouncing off the wall.
                            x_speed = x_speed * self.restitution
                            # print("BALL HIT WALL AND DOES NOT HIT TARGET", x_prime, y_prime, elapsed_time)
                    else:
                        if x_prime >= self.target_x_pixel:
                            time_step_prime = abs((self.target_x_pixel - x_pixel) / x_speed)
                            y_prime = y_pixel + y_speed * time_step_prime
                            x_prime = self.target_x_pixel
                            predicted_trajectory.append((round(x_prime), round(y_prime)))
                            elapsed_time += time_step_prime
                            # print("BALL DOES NOT HIT WALL AND DOES HIT TARGET", x_prime, y_prime, elapsed_time)
                            break
                        else:
                            predicted_trajectory.append((round(x_prime), round(y_prime)))
                            elapsed_time += remaining_time
                            # print("BALL DOES NOT HIT WALL AND DOES NOT HIT TARGET", x_prime, y_prime, elapsed_time)
                    x_pixel = x_prime
                    y_pixel = y_prime

                total_elapsed_time += elapsed_time
                # For X axis don't do bounce prediction assuming that it's going to hit a player or the goal before it
                # hits the wall.

                # Update the position of the ball for next iteration.
                x_pixel = x_prime
                y_pixel = y_prime

            # Elapsed time until ball was moving below the threshold or until it hit the target position.
            if x_prime == self.target_x_pixel and total_elapsed_time < 0.6:
                #if 0.15 < total_elapsed_time < 0.30:
                #    self.queue_from_camera.put_nowait((CameraEvent.STRIKE, None))
                if 0 < total_elapsed_time < 0.15 and abs(curr_pos[0] - self.target_x_pixel) < 800:

                    self.queue_from_camera.put_nowait((CameraEvent.QUICK_STRIKE, None))
                return y_prime, predicted_trajectory
            else:
                return None

        # If only one point is in the buffer, use the current ball position if it is within the x range threshold.
        elif len(self.buffer) == 1:
            if self.buffer[0] is None:
                return None
            return (self.buffer[0][1],)
        else:
            return None

    def get_predicted(self, rate):
        if rate > 40:
            self.rate = rate
        out = self._predict()
        out_val = None
        if out is None:
            # Determine whether to send the current ball position.
            ii = 1
            curr_ball_pos = self.buffer[0]
            if curr_ball_pos is None:
                return None
            buffer_len = len(self.predicted_buffer)
            tmp_out_val = None
            # Get last not None value sent to the motors.
            while True:
                if ii < 60 and buffer_len > ii:
                    if self.predicted_buffer[ii] is not None:
                        tmp_out_val = self.predicted_buffer[ii]
                        break
                else:
                    break
                ii += 1

            if tmp_out_val is None or abs(tmp_out_val - curr_ball_pos[1]) > self.ball_radius*2:
                out_val = round(curr_ball_pos[1])
                self.predicted_buffer.insert(0, out_val)
            else:
                self.predicted_buffer.insert(0, None)

        else:
            out_val = round(out[0])
            self.predicted_buffer.insert(0, out[0])
            if len(out) == 2:
                self.predicted_path = out[1]

        if len(self.predicted_buffer) > 100:
            self.predicted_buffer = self.predicted_buffer[:50]
        return out_val

    def get_path(self) -> Optional[Tuple]:
        return self.predicted_path


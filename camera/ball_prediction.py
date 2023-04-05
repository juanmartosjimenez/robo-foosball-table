import os

from camera.camera_measurements import CameraMeasurements
from other.events import CameraEvent

BALL_POSITION_FILE = os.path.join(os.path.dirname(__file__), "data/ball_positions.txt")


class BallPrediction:
    def __init__(self, x_pixels, y_pixels, rate, queue_from_camera, target_x_pixel, playing_field_bottom_right,
                 ball_radius):
        # Total number of x pixels in the playing field.
        self.x_pixels = x_pixels
        # Total number of y pixels in the playing field.
        self.y_pixels = y_pixels
        # Rate at which new ball positions are added. Should be 60fps.
        self.rate = rate
        # Damping factor. Rate at which the ball slows down.
        self.damping = 0.9
        # Threshold speed. Speed at which prediction of ball is no longer taking into account but rather the current
        # ball position.
        self.threshold = 100
        # Restitution factor. Rate at which the ball bounces off the walls.
        self.restitution = 0.5
        # Buffer to store current ball pixels.
        self.buffer = []
        # Predicted ball pixels.
        self.predicted = []
        # Queue used to send out
        self.queue_from_camera = queue_from_camera
        # X range threshold. Number of pixels apart from goalie for predicted path to be taken into account.
        self.x_range_threshold = 40
        # Camera measurements
        self.camera_measurements = CameraMeasurements()
        # Playing field bottom right pixel.
        self.playing_field_bottom_right = playing_field_bottom_right
        # Target x pixel position. Position of the goalie bar.
        self.target_x_pixel = self.__convert_to_playing_field_pixel(target_x_pixel, 0)[0]
        # Ball radius in pixels.
        self.ball_radius = ball_radius

    def __convert_to_playing_field_pixel(self, x_pixel, y_pixel):
        """
        Converts the pixel position of the ball to the pixel position of the ball relative to the playing field.
        :param x_pixel:
        :param y_pixel:
        :return:
        """
        x_pixel = round((self.camera_measurements.camera_resolution_x - x_pixel - (
                self.camera_measurements.camera_resolution_x - self.playing_field_bottom_right[0])))
        y_pixel = round((self.camera_measurements.camera_resolution_y - y_pixel - (
                self.camera_measurements.camera_resolution_y - self.playing_field_bottom_right[1])))
        return x_pixel, y_pixel

    def ball_writer(self, x_pixel, y_pixel):
        # Writes current ball position to file.
        with open(BALL_POSITION_FILE, "a+") as f:
            f.write(f"{str(x_pixel)},{str(y_pixel)}")

    def add_new(self, x_pixel, y_pixel):
        x_pixel, y_pixel = self.__convert_to_playing_field_pixel(x_pixel, y_pixel)
        self.ball_writer(x_pixel, y_pixel)
        self.buffer.insert(0, (x_pixel, y_pixel))
        # Remove old ball positions.
        if len(self.buffer) > 60:
            self.buffer = self.buffer[:20]

    def _predict(self):
        """
        Predicts the ball position based on the current ball position and the previous ball position.
        :return: Y pixel position of the predicted ball position.
        """
        # If more than two points are in the buffer, predict the ball position.
        if len(self.buffer) >= 2:
            curr_pos = self.buffer[0]
            prev_pos = self.buffer[1]

            # If the current position is None, the ball was not detected during this frame.
            if curr_pos is None:
                return None

            # The ball was not detected during the previous frame. So move to the current position.
            if prev_pos is None:
                return self.buffer[1]

            # If change in position is less than the ball radius then ball is stationary and no change in position is
            # needed.
            if abs(curr_pos[0] - prev_pos[0]) < self.ball_radius * 2:
                return None

            # If the ball is behind the target position then move to position and strike.
            # TODO make the ball strike.
            if curr_pos[0] < self.target_x_pixel:
                return self.buffer[1]

            # If the ball is within the x range threshold, use the current ball position instead of predicting
            # trajectory.
            if curr_pos[0] - self.target_x_pixel < self.x_range_threshold:
                return self.buffer[1]

            # Calculate the speed of the ball.
            speed = ((curr_pos[0] - prev_pos[0]) ** 2 + (curr_pos[1] - prev_pos[1]) ** 2) ** 0.5
            x_speed = (curr_pos[0] - prev_pos[0]) / speed
            y_speed = (curr_pos[1] - prev_pos[1]) / speed

            # If x speed is negative then ball is going the wrong way.
            if x_speed < 0:
                return None

            # Calculate the next position of the ball after the time step.
            time_step = 0.1 # 0.1 seconds

            x_pixel = curr_pos[0]
            y_pixel = curr_pos[1]
            iterations = 0
            total_elapsed_time = 0
            x_prime = x_pixel
            y_prime = y_pixel
            # If the speed is less than the threshold, use the current ball position instead of predicting trajectory.
            while x_speed > self.threshold or x_prime!=self.target_x_pixel:
                iterations += 1
                elapsed_time = 0
                while elapsed_time != time_step:
                    remaining_time = time_step - elapsed_time
                    # Calculate the next position of the ball after the time step.
                    x_prime = x_pixel + x_speed * remaining_time * self.damping
                    y_prime = y_pixel + y_speed * remaining_time * self.damping

                    # If the ball hits the top or bottom wall, bounce off the wall.
                    if y_prime < 0 or y_prime > self.y_pixels:
                        # Get the time step at which the ball hits the wall which is less than the default time step.
                        if y_prime > self.y_pixels:
                            time_step_prime = (self.y_pixels - y_pixel) / (y_speed * self.damping)
                        else:
                            time_step_prime = y_pixel / (y_speed * self.damping)

                        # Calculate the next position of the ball after the time step.
                        y_prime = y_pixel + y_speed * time_step_prime * self.damping
                        x_prime = x_pixel + x_speed * time_step_prime * self.damping

                        # If x position is past the target position, then find time to reach target position.
                        if x_prime >= self.target_x_pixel:
                            time_step_prime = (self.target_x_pixel - x_pixel) / (x_speed * self.damping)
                            y_prime = y_pixel + y_speed * time_step_prime * self.damping
                            x_prime = self.target_x_pixel
                            elapsed_time += time_step_prime
                            break
                        else:
                            elapsed_time += time_step_prime
                            # There is surely a more physics way of doing this but this works.
                            # Update the Y speed of the ball after bouncing off the wall.
                            y_speed = -y_speed * self.restitution
                            # Update the X speed of the ball after bouncing off the wall.
                            x_speed = x_speed * self.restitution
                    else:
                        if x_prime >= self.target_x_pixel:
                            time_step_prime = (self.target_x_pixel - x_pixel) / (x_speed * self.damping)
                            y_prime = y_pixel + y_speed * time_step_prime * self.damping
                            x_prime = self.target_x_pixel
                            elapsed_time += time_step_prime
                            break
                        else:
                            elapsed_time += remaining_time

                total_elapsed_time += elapsed_time
                # For X axis don't do bounce prediction assuming that it's going to hit a player or the goal before it
                # hits the wall.

                # Reduce the speed of the ball by the damping factor.
                x_speed = x_speed * self.damping
                y_speed = y_speed * self.damping
                # Update the position of the ball for next iteration.
                x_pixel = x_prime
                y_pixel = y_prime

            # Elapsed time until ball was moving below the threshold or until it hit the target position.
            if x_prime == self.target_x_pixel:
                print("Ball predicted to reach target position.")
                self.predicted.append(y_prime)
                return y_prime
            else:
                print("Ball predicted to move below threshold.")
                return None

        # If only one point is in the buffer, use the current ball position if it is within the x range threshold.
        elif len(self.buffer) == 1:
            return self.buffer[0][1]
        else:
            return None

    def get_predicted(self):
        out = self._predict()
        self.predicted.append(out)

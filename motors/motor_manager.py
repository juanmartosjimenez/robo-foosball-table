import queue
import time
import sys

from motors.roboclaw import Roboclaw
import serial.tools.list_ports
from motors.motor_measurements import MotorMeasurements
from other.events import MotorEvent


class MotorManager:
    def __init__(self, serial_port: str = "COM5"):
        # Since only one roboclaw is being used, default address is 0x80.
        self.address = 0x80
        # Initialize roboclaw object.
        self.roboclaw: Roboclaw = Roboclaw(serial_port, 38400)
        self.roboclaw.Open()
        """
        Shouldn't be necessary once the second limit switch is installed.
        Actually, this value is coded into the firmware, so when moving to position can never move past that position.
        There is still an associated risk with move_forward_m1 that will move the motor past the limit.
        :return:
        """
        self.right_limit = 1600
        # Initialize motor measurements.
        self.measurements = MotorMeasurements()

    def event_loop(self, queue_to_motors, queue_from_motors):
        """
        Event loop for the motor manager.
        :return:
        """
        start_time = time.time()
        while True:
            time.sleep(0.01)
            try:
                data = queue_to_motors.get_nowait()
                event = data[0]
                if event == MotorEvent.HOME_M1:
                    self.home_m1()
                elif event == MotorEvent.HOME_M2:
                    self.home_m2()
                elif event == MotorEvent.MOVE_TO_MM_M1:
                    self.move_center_goalie(data[1])
                elif event == MotorEvent.STOP:
                    self.stop()
                elif event == MotorEvent.ENCODER_VALS:
                    encoder_val = self.read_encoders()
                    queue_from_motors.put_nowait((MotorEvent.ENCODER_VALS, {"encoders": encoder_val,
                                                                    "mm_m1": self._encoder_to_mm_m1(encoder_val[0]),
                                                                    "degrees_m2": self._encoder_to_degrees_m2(
                                                                        encoder_val[0])}))
                elif event == MotorEvent.STRIKE:
                    self.strike()
                elif event == MotorEvent.MOVE_TO_START_POS:
                    self.move_to_default_pos_m2()
                    self.move_to_default_pos_m1()
                else:
                    raise ValueError("Unknown motor_manager event: " + data)
            except queue.Empty:
                if time.time() - start_time > 1:
                    # Every 1 seconds, read the encoders.
                    queue_to_motors.put_nowait((MotorEvent.ENCODER_VALS, None))
                    start_time = time.time()
                pass

    def stop_m1(self):
        """
        Stops motor 1.
        :return:
        """
        self.roboclaw.ForwardM1(self.address, 0)

    def stop_m2(self):
        """
        Stops motor 2.
        :return:
        """
        self.roboclaw.ForwardM2(self.address, 0)

    def stop(self):
        """
        Stops both motors.
        :return:
        """
        self.stop_m2()
        self.stop_m1()

    def home_m1(self):
        """
        Moves motor 1 to the left limit until limit switch is triggered.
        Firmware is set to reset encoder to 0 when limit switch is triggered.
        :return:
        """
        self.roboclaw.BackwardM1(self.address, 30)
        while True:
            time.sleep(0.4)
            if self.roboclaw.ReadSpeedM1(self.address)[1] == 0:
                self.stop()
                self.roboclaw.SetEncM1(self.address, 0)
                break

        # This line is not necessary because the encoder is reset to 0 when the motor triggers the limit switch.
        # self.roboclaw.SetEncM1(self.address, 0)

    def home_m2(self):
        """
        Sets the encoder position of motor 2 to 0.
        :return:
        """
        self.roboclaw.SetEncM2(self.address, 0)

    @staticmethod
    def read_serial_ports():
        """
        Reads connected serial ports, useful to identify what port the roboclaw is connected to.
        :return:
        """
        return [comport.device for comport in serial.tools.list_ports.comports()]

    def read_encoders(self):
        """
        Returns the encoder positions for both motors.
        :return:
        """
        return self.roboclaw.ReadEncM1(self.address)[1], self.roboclaw.ReadEncM2(self.address)[1]

    def read_encoder_counters(self):
        """
        Reads the encoder counters for both motors.
        :return:
        """
        return self.roboclaw.ReadEncoderCounters(self.address)

    def move_forward_m1(self, speed=30):
        """
        Moves motor 1 forward at the given speed.
        :param speed:
        :return:
        """
        self.roboclaw.ForwardM1(self.address, speed)

    def move_backward_m2(self, speed=30):
        """
        Moves motor 2 backward at the given speed.
        :param speed:
        :return:
        """
        self.roboclaw.BackwardM2(self.address, speed)

    def move_forward_m2(self, speed=30):
        """
        Moves motor 2 forward at the given speed.
        :param speed:
        :return:
        """
        self.roboclaw.ForwardM2(self.address, speed)

    def move_backward_m1(self, speed=30):
        """
        Moves motor 1 backward at the given speed.
        :param speed:
        :return:
        """
        self.roboclaw.BackwardM1(self.address, speed)

    def move_to_pos_m1(self, pos):
        """
        Moves motor 1 to the given encoder position.
        :param pos:
        :return:
        """
        # if pos > self.right_limit:
        # raise ValueError("Position out of range")
        if pos < 0: pos = 0
        self.roboclaw.SpeedAccelDeccelPositionM1(self.address, 24000, 4000, 24000, pos, 1)

    def move_to_default_pos_m1(self):
        """
        Move to default position which is center of goal.
        :return:
        """
        self.move_to_pos_m1(self.measurements.enc_m1_default)

    def move_to_pos_m2(self, pos, accell=16000, speed=2000, deccell=16000):
        """
        Moves motor 2 to the given encoder position.
        :param pos:
        :return:
        """
        self.roboclaw.SpeedAccelDeccelPositionM2(self.address, accell, speed, deccell, pos, 1)

    def move_to_default_pos_m2(self):
        """
        Move to default position which is player facing directly down.
        Default pos is 145 instead of 0 because can't move negative encoder values.
        :return:
        """
        self.move_to_pos_m2(self.measurements.enc_m2_default)

    def strike(self):
        """
        Strike the ball with the m2 motor.
        :return:
        """

        # Gets the shortest distance to move player to strike start position and moves there.
        curr_pos = self.read_encoders()[1]
        nearest_0 = curr_pos % self.measurements.enc_m2_360_rotation
        if nearest_0 > self.measurements.enc_m2_360_rotation / 2:
            nearest_0 = self.measurements.enc_m2_360_rotation - nearest_0
        else:
            nearest_0 = -nearest_0
        # self.move_to_pos_m2(nearest_0 + self.measurements.enc_m2_strike, accell=32000, speed=4000, deccell=32000)
        self.move_backward_m2(35)

        # Moves the player to strike end position.
        while True:
            # Don't wait for motors to reach exactly the strike start position because it will be too slow.
            if nearest_0 + self.measurements.enc_m2_strike - 10 <= self.roboclaw.ReadEncM2(self.address)[
                1] <= nearest_0 + self.measurements.enc_m2_strike:
                break
        self.move_forward_m2(120)
        time.sleep(0.09)
        # Moves the player back to start position.
        self.move_to_default_pos_m2()

    def _mm_to_encoder_m1(self, mm: float) -> int:
        """
        Converts inches to encoder position.
        :param mm:
        :return:
        """
        return int(mm * self.measurements.m1_mm_to_enc)

    def _encoder_to_mm_m1(self, encoder: int) -> float:
        """
        Converts encoder position to inches.
        :param encoder:
        :return:
        """
        return round(encoder / self.measurements.m1_mm_to_enc, 2)

    def _encoder_to_degrees_m2(self, encoder: int) -> float:
        """
        Converts encoder position to degrees.
        :param encoder:
        :return:
        """
        return round(encoder % self.measurements.enc_m2_360_rotation, 2)

    def move_to_mm_m1(self, mm):
        """
        Moves the player the given number of mm.
        :param mm:
        :return:
        """
        self.move_to_pos_m1(self._mm_to_encoder_m1(mm))

    def move_center_goalie(self, mm):
        """
        Moves the goalie to the center of the goal.
        :return:
        """
        # mm_space_to_encoder_0_position = 25
        # mm_distance_to_golie = 264
        # Ideally this is a measurable value but there is some uncertainty with the ball playing field pixels.
        mm_distance_to_goalie_2 = 315
        mm_distance_to_goalie_1 = 95
        mm_distance_to_goalie_3 = 535
        mm_goalie_2_movement = self._mm_to_encoder_m1(mm-mm_distance_to_goalie_2)
        mm_goalie_1_movement = self._mm_to_encoder_m1(mm-mm_distance_to_goalie_1)
        mm_goalie_3_movement = self._mm_to_encoder_m1(mm-mm_distance_to_goalie_3)
        if 0 < mm_goalie_2_movement < self.measurements.m1_encoder_limit:
            self.move_to_pos_m1(mm_goalie_2_movement)
        elif mm_goalie_2_movement < 0:
            self.move_to_pos_m1(mm_goalie_1_movement)
        elif mm_goalie_2_movement > self.measurements.m1_encoder_limit:
            self.move_to_pos_m1(mm_goalie_3_movement)


if __name__ == "__main__":
    print(MotorManager.read_serial_ports())
import time

from roboclaw import Roboclaw
import serial.tools.list_ports
from motor_measurements import MotorMeasurements


class HardwareManager:
    def __init__(self, serial_port="COM5"):
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
                break

        # This line is not necessary because the encoder is reset to 0 when the motor triggers the limit switch.
        # self.roboclaw.SetEncM1(self.address, 0)

    def home_m2(self):
        """
        Sets the encoder position of motor 2 to 0.
        :return:
        """
        self.roboclaw.SetEncM2(self.address, 0)

    def read_serial_ports(self):
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
        if pos > self.right_limit:
            raise ValueError("Position out of range")
        self.roboclaw.SpeedAccelDeccelPositionM1(self.address, 16000, 2000, 16000, pos, 1)

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

    def strike_m2(self):
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
        #self.move_to_pos_m2(nearest_0 + self.measurements.enc_m2_strike, accell=32000, speed=4000, deccell=32000)
        self.move_backward_m2(35)

        # Moves the player to strike end position.
        while True:
            # Don't wait for motors to reach exactly the strike start position because it will be too slow.
            if nearest_0 + self.measurements.enc_m2_strike -10 <= self.roboclaw.ReadEncM2(self.address)[1] <= nearest_0 + self.measurements.enc_m2_strike:
                break
        self.move_forward_m2(120)
        time.sleep(0.09)
        # Moves the player back to start position.
        self.move_to_default_pos_m2()


if __name__ == "__main__":
    hardware_manager = HardwareManager()
    hardware_manager.home_m1()

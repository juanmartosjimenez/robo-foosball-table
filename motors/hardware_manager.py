import time

from roboclaw import Roboclaw
import serial.tools.list_ports


class HardwareManager:
    def __init__(self, serial_port="COM5"):
        self.address = 0x80
        self.roboclaw: Roboclaw = Roboclaw(serial_port, 38400)
        self.roboclaw.Open()
        self._right_limit = 1614

    @property
    def right_limit(self):
        if self._right_limit is None:
            raise ValueError("Right limit not set")
        return self._right_limit

    @right_limit.setter
    def right_limit(self, value):
        self._right_limit = value
        print("Right limit set to", value)

    def stop(self):
        self.roboclaw.ForwardM1(self.address, 0)
        self.roboclaw.ForwardM2(self.address, 0)

    def home_m1(self):
        self.roboclaw.BackwardM1(self.address, 30)
        while True:
            time.sleep(0.4)
            if self.roboclaw.ReadSpeedM1(self.address)[1] == 0:
                self.stop()
                break
        self.roboclaw.SetEncM1(self.address, 0)

    def home_m2(self):
        self.roboclaw.SetEncM2(self.address, 0)

    def read_serial_ports(self):
        return [comport.device for comport in serial.tools.list_ports.comports()]

    def get_encoder_pos(self):
        return self.roboclaw.ReadEncM1(self.address)[1], self.roboclaw.ReadEncM2(self.address)[1]

    def read_encoder_counters(self):
        return self.roboclaw.ReadEncoderCounters(self.address)

    def set_right_rom_m1(self):
        self.right_limit = self.roboclaw.ReadEncM1(self.address)[1]

    def move_forward_m1(self, speed=30):
        self.roboclaw.ForwardM1(self.address, speed)

    def move_backward_m1(self, speed=30):
        self.roboclaw.BackwardM1(self.address, speed)

    def move_to_pos_m1(self, pos):
        if pos > self.right_limit:
            raise ValueError("Position out of range")
        self.roboclaw.SpeedAccelDeccelPositionM1(self.address, 16000, 2000, 16000, pos, 1)

    def move_to_default_pos_m1(self):
        self.move_to_pos_m1(667)

    def move_to_pos_m2(self, pos):
        print("here")
        self.roboclaw.SpeedAccelDeccelPositionM2(self.address, 16000, 2000, 16000, pos, 1)

    def move_to_default_pos_m2(self):
        self.move_to_pos_m2(0)

    def strike_m2(self):
        curr_pos = self.get_encoder_pos()[1]
        nearest_pos = curr_pos % 145
        if nearest_pos > 72:
            nearest_pos = 145 - nearest_pos
        else:
            nearest_pos = -nearest_pos
        self.move_to_pos_m2(nearest_pos+120)

        while True:
            if self.roboclaw.ReadEncM2(self.address)[1] == nearest_pos+120:
                break
        self.roboclaw.ForwardM2(self.address, 80)
        time.sleep(0.1)
        curr_pos = self.get_encoder_pos()[1]
        nearest_pos = curr_pos % 145
        if nearest_pos > 72:
            nearest_pos = 145 - nearest_pos
        else:
            nearest_pos = -nearest_pos
        self.move_to_pos_m2(curr_pos + nearest_pos)



if __name__ == "__main__":
    hardware_manager = HardwareManager()
    print(hardware_manager.get_encoder_pos())
    hardware_manager.home_m1()
    print(hardware_manager.get_encoder_pos())
    print(hardware_manager.read_encoder_counters())

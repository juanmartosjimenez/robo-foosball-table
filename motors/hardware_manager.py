from roboclaw import Roboclaw
import time
from measurements import measurements


class HardwareManager():
    def __init__(self):
        self.address = 0x80
        self.roboclaw: Roboclaw = Roboclaw("/dev/ttyACM0", 38400)
        self.roboclaw.Open()
        print("Succesfully connected to Roboclaw")

    def get_current_pos(self):
        return self.roboclaw.ReadEncM1(self.address)[1], self.roboclaw.ReadEncM2(self.address)[1]


if __name__ == "__main__":
    hardware_manager = HardwareManager()
    print(hardware_manager.get_current_pos())

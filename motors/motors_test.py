import sys
import serial.tools.list_ports
print([comport.device for comport in serial.tools.list_ports.comports()])
exit()
from roboclaw_3 import Roboclaw

roboclaw = Roboclaw("COM5", 38400)

print(roboclaw.Open())
roboclaw.ForwardM2(0x80, 63)







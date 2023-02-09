import serial.tools.list_ports
from roboclaw_3 import Roboclaw

ADDRESS = 0x80
#print([comport.device for comport in serial.tools.list_ports.comports()])
roboclaw = Roboclaw("COM5", 38400)

print(roboclaw.Open())
print(roboclaw.GetConfig(ADDRESS))







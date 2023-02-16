import sys
sys.insert(1, '/home/teddy/repositories/roboclaw/robo-foosball-table/camera/ball_tracking_with_trajectory')
import './coordinates_motors'

def main():
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    while(notEmpty(queue)):
        stopAtLateralAddress(roboclaw, queue.pop())
        kickMotion(roboclaw)




from roboclaw import Roboclaw
import time
from coordinates_motors import readEncoderM1,readEncoderM2,stopM1,stopM2

ADDRESS = 0x80
SPEED = 40

def playerBalancer(roboclaw, pos):
    if (pos < 500 and pos > 0):
        bottomPlayerHit(roboclaw, pos*3)
    elif pos >= 500 and pos < 1000:
        middlePlayerHit(roboclaw, (pos-500) * 3)
    elif pos >= 1000 and pos < 1500:
        topPlayerHit(roboclaw, (pos-1000) * 3)
    else:
        raise Exception("Invalid position")


def bottomPlayerHit(roboclaw, pos):
    print("Bottom Player", pos, " Encoder Value: ", readEncoderM1(roboclaw)[1])
    if readEncoderM1(roboclaw)[1] < pos:
        roboclaw.ForwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] >= pos:
                stopM1(roboclaw)
                break
    if readEncoderM1(roboclaw)[1] > pos:
        roboclaw.BackwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] <= pos:
                stopM1(roboclaw)
                break

def middlePlayerHit(roboclaw, pos):
    print("Middle Player:", pos, " Encoder Value: ", readEncoderM1(roboclaw)[1])
    if readEncoderM1(roboclaw)[1] < pos:
        roboclaw.ForwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] >= pos:
                stopM1(roboclaw)
                break
    if readEncoderM1(roboclaw)[1] > pos:
        roboclaw.BackwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] <= pos:
                stopM1(roboclaw)
                break

def topPlayerHit(roboclaw, pos):
    print("Top Player:", pos, " Encoder Value: ", readEncoderM1(roboclaw)[1])
    if readEncoderM1(roboclaw)[1] < pos:
        roboclaw.ForwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] >= pos:
                stopM1(roboclaw)
                break
    if readEncoderM1(roboclaw)[1] > pos:
        roboclaw.BackwardM1(ADDRESS, SPEED)
        while (True):
            if readEncoderM1(roboclaw)[1] <= pos:
                stopM1(roboclaw)
                break

def main():
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    playerBalancer(roboclaw, 950)


if __name__ == "__main__":
    main()


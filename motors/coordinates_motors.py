from roboclaw import Roboclaw
import time

ADDRESS = 0x80

# takes roboclaw object
# stops motor 1
def stopM1(roboclaw):
    roboclaw.ForwardM1(ADDRESS, 0)


# takes roboclaw object
# stops motor 2
def stopM2(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 0)


# takes roboclaw object
# returns encoder tuple for motor 1
def readEncoderM1(roboclaw):
    encoderM1 = roboclaw.ReadEncM1(ADDRESS)
    return encoderM1


# takes roboclaw obejct
# returns encoder tuple for motor 2
def readEncoderM2(roboclaw):
    encoderM2 = roboclaw.ReadEncM2(ADDRESS)
    return encoderM2


# takes roboclaw object
# makes a kicking motion and returns to rotational zero position
def kickMotion(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 30)
    time.sleep(0.1)
    stopM2(roboclaw)
    roboclaw.BackwardM2(ADDRESS, 20)
    while (True):
        if readEncoderM2(roboclaw)[1] < 20:
            stopM2(roboclaw)
            break


# takes roboclaw object and coordinate(integer) to move to between 0 and -2000
# moves motors to that relative location
def stopAtLateralAddress(roboclaw, pos):
    print("POS:", pos)
    if readEncoderM1(roboclaw)[1] < pos:
        # case if coordinate is ahead of current location of motors
        roboclaw.ForwardM1(ADDRESS, 10)
        while (True):
            print(readEncoderM1(roboclaw)[1])
            if (readEncoderM1(roboclaw)[1] >= pos):
                stopM1(roboclaw)
                break
    if readEncoderM1(roboclaw)[1] > pos:
        # case if coordinate is behind current location of motors
        roboclaw.BackwardM1(ADDRESS, 10)
        while (True):
            print(readEncoderM1(roboclaw)[1])
            if (readEncoderM1(roboclaw)[1] <= pos):
                stopM1(roboclaw)
                break

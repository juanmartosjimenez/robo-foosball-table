from roboclaw import Roboclaw
import time
from measurements import measurements

ADDRESS = 0x80


# testing functions
def main():
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    # print('Encoder 1:', readEncoderM1(roboclaw))
    print('Encoder 2:', read_encoder_m2(roboclaw))
    print('Encoder 1:', read_encoder_m1(roboclaw)[1])
    # stopAtLateralAddress(roboclaw, -1000)
    kick_motion(roboclaw)


# takes roboclaw object
# stops motor 1
def stop_m1(roboclaw):
    roboclaw.ForwardM1(ADDRESS, 0)


# takes roboclaw object
# stops motor 2
def stop_m2(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 0)


# takes roboclaw object
# returns encoder tuple for motor 1
def read_encoder_m1(roboclaw):
    encoderM1 = roboclaw.ReadEncM1(ADDRESS)
    return encoderM1


# takes roboclaw obejct
# returns encoder tuple for motor 2
def read_encoder_m2(roboclaw):
    encoderM2 = roboclaw.ReadEncM2(ADDRESS)
    return encoderM2


# takes roboclaw object
# makes a kicking motion and returns to rotational zero position
def kick_motion(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 30)
    time.sleep(0.1)
    stop_m2(roboclaw)
    roboclaw.BackwardM2(ADDRESS, 20)
    while True:
        if read_encoder_m2(roboclaw)[1] < 20:
            stop_m2(roboclaw)
            break


# takes roboclaw object and coordinate(integer) to move to between 0 and -2000
# moves motors to that relative location
def stop_at_lateral_address(roboclaw, coordinate):
    if coordinate < -1600 or coordinate > -400:
        # given a buffer of about 400 on each size
        print("invalid coordinate")
    else:
        if read_encoder_m1(roboclaw)[1] < coordinate:
            # case if coordinate is ahead of current location of motors
            print(read_encoder_m1(roboclaw)[1])
            roboclaw.BackwardM1(ADDRESS, 20)
            while True:
                if read_encoder_m1(roboclaw)[1] >= coordinate:
                    stop_m1(roboclaw)
                    break
        if read_encoder_m1(roboclaw)[1] > coordinate:
            # case if coordinate is behind current location of motors
            print(read_encoder_m1(roboclaw)[1])
            roboclaw.ForwardM1(ADDRESS, 20)
            while True:
                if read_encoder_m1(roboclaw)[1] <= coordinate:
                    stop_m1(roboclaw)
                    break


if __name__ == "__main__":
    main()

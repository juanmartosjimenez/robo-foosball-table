from roboclaw import Roboclaw
import time

ADDRESS = 0x80

#testing functions
def main():
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    #print('Encoder 1:', readEncoderM1(roboclaw))
    print('Encoder 2:', readEncoderM2(roboclaw))
    print('Encoder 1:', readEncoderM1(roboclaw)[1])
    stopAtLateralAddress(roboclaw, -1000)

#takes roboclaw object
#stops motor 1
def stopM1(roboclaw):
    roboclaw.ForwardM1(ADDRESS, 0)

#takes roboclaw object
#stops motor 2
def stopM2(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 0)

#takes roboclaw object
#returns encoder tuple for motor 1
def readEncoderM1(roboclaw):
    encoderM1 = roboclaw.ReadEncM1(ADDRESS)
    return encoderM1

#takes roboclaw obejct
#returns encoder tuple for motor 2
def readEncoderM2(roboclaw):
    encoderM2 = roboclaw.ReadEncM2(ADDRESS)
    return encoderM2

#takes roboclaw object
#makes a kicking motion and returns to rotational zero position
def kickMotion(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 30)
    time.sleep(0.1)
    stopM2(roboclaw)
    roboclaw.BackwardM2(ADDRESS, 20)
    while(True):
        if readEncoderM2(roboclaw)[1] < 20:
            stopM2(roboclaw)
            break

#takes roboclaw object and coordinate(integer) to move to between 0 and -2000
#moves motors to that relative location
def stopAtLateralAddress(roboclaw, coordinate):
    if (coordinate < -1400 or coordinate > -400):
        #given a buffer of about 400 on each size
        print("invalid coordinate")
    else:
        if readEncoderM1(roboclaw)[1] < coordinate:
            #case if coordinate is ahead of current location of motors
            print(readEncoderM1(roboclaw)[1])
            roboclaw.BackwardM1(ADDRESS,20)
            while(True):
                if (readEncoderM1(roboclaw)[1] >= coordinate):
                    stopM1(roboclaw)
                    break
        if readEncoderM1(roboclaw)[1] > coordinate:
            #case if coordinate is behind current location of motors
            print(readEncoderM1(roboclaw)[1])
            roboclaw.ForwardM1(ADDRESS,20)
            while(True):
                if (readEncoderM1(roboclaw)[1] <= coordinate):
                    stopM1(roboclaw)
                    break
         
if __name__ == "__main__":
    main()

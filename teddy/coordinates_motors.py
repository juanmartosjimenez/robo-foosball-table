from roboclaw_3 import Roboclaw
import time

ADDRESS = 0x80

def main():
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    #print('Encoder 1:', readEncoderM1(roboclaw))
    #print('Encoder 2:', readEncoderM2(roboclaw))
    print('Encoder 1:', readEncoderM1(roboclaw)[1])
    stopAtLateralAddress(roboclaw, -1000)



def stopM1(roboclaw):
    roboclaw.ForwardM1(ADDRESS, 0)

def stopM2(roboclaw):
    roboclaw.ForwardM2(ADDRESS, 0)

#given lateral coordinates between 0 and 100, moves to that coordinate
def readEncoderM1(roboclaw):
    encoderM1 = roboclaw.ReadEncM1(ADDRESS)
    return encoderM1

def readEncoderM2(roboclaw):
    encoderM2 = roboclaw.ReadEncM2(ADDRESS)
    return encoderM2

#starts at -400
#ends at -1500
def stopAtLateralAddress(roboclaw, coordinate):
    if (coordinate < -1500 or coordinate > -400):
        print("invalid coordinate")
    else:
        if readEncoderM1(roboclaw)[1] < coordinate:
            print(readEncoderM1(roboclaw)[1])
            roboclaw.BackwardM1(ADDRESS,20)
            while(True):
                if (readEncoderM1(roboclaw)[1] >= coordinate):
                    stopM1(roboclaw)
                    break
        if readEncoderM1(roboclaw)[1] > coordinate:
            print(readEncoderM1(roboclaw)[1])
            roboclaw.ForwardM1(ADDRESS,20)
            while(True):
                if (readEncoderM1(roboclaw)[1] <= coordinate):
                    stopM1(roboclaw)
                    break
         

                
    



if __name__ == "__main__":
    main()

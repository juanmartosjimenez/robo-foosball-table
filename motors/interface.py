import * from './coordinates_motors'
import * from '../camera/ball_tracking_with_trajectory'
import keyboard
import './threading_util'

x_coordinate = 0

def main():
    #sets up thread lock
    data_lock = LockWithOwner()
    data_lock.owner = 'A'
    endGame = 0
    #activates connection with motors
    roboclaw = Roboclaw("/dev/ttyACM0", 38400)
    roboclaw.Open()
    #begins motor thread
    t0 = Thread(target = roboclawMovement, args=(roboclaw))
    #beings camera thread
    t1 = Thread(target = cameraTracking, args=())
    #starts threads
    t0.start()
    t1.start()
    #ends threads
    t0.join()
    t1.join()

#will set endGame bool to 1 if q is pressed, ending both threads
def terminateGame():
    if keyboard.is_pressed("q"):
        endGame = 1

#updates endXImm values, camera thread
def cameraTracking():
    while(True):
        terminateGame()
        if (endGame == 1):
            break
        lock.acquire_for('A')
        x_coordinate = ball_tracking_with_trajectory.endXImm
        lock.release_to('B')

#moves roboclaw to most recently updated x-coordinate, motor thread
def roboclawMovement(roboclaw):
    while(True):
        terminateGame()
        if (endGame == 1):
            break
        lock.acquire_for('B')
        stopAtLateralAddress(roboclaw, endXImm)
        lock.acquire_for('A')


if __name__ == "__main__":
    main()



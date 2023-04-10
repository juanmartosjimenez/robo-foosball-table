import multiprocessing
import queue
import time
from queue import Queue

from motors.motor_measurements import MotorMeasurements
from motors.roboclaw import Roboclaw
from other.events import RotationalMotorEvent


class RotationalMotor:
    def __init__(self, queue_to_rotational_motors: Queue, queue_from_rotational_motors: Queue, roboclaw: Roboclaw, stop_flag: multiprocessing.Event, lock: multiprocessing.Lock):
        self.measurements = MotorMeasurements()
        self.address = self.measurements.address
        self.queue_to_motors = queue_to_rotational_motors
        self.queue_from_motors = queue_from_rotational_motors
        self.roboclaw: Roboclaw = roboclaw
        self.stop_flag = stop_flag
        self.lock = lock
        self.last_strike = None
        self.homed = False

    def event_loop(self):
        while True:
            time.sleep(0.001)
            last_event = None
            if self.stop_flag.is_set():
                try:
                    self.stop()
                except Exception as e:
                    pass
                return
            # Only interested in the last event.
            while True:
                try:
                    last_event = self.queue_to_motors.get_nowait()
                except queue.Empty:
                    break

            if last_event is not None:
                event = last_event[0]
                if event == RotationalMotorEvent.STRIKE:
                    print("Strike")
                    # Only strike if the last strike was more than 1 second ago.
                    if self.last_strike is None or time.time() - self.last_strike > 1:
                        self.strike()
                        self.last_strike = time.time()
                elif event == RotationalMotorEvent.QUICK_STRIKE:
                    if self.last_strike is None or time.time() - self.last_strike > 1:
                        self.quick_strike()
                        self.last_strike = time.time()
                elif event == RotationalMotorEvent.HOME:
                    self.home()
                elif event == RotationalMotorEvent.MOVE_TO_DEFAULT:
                    self.move_to_default_pos()
                elif event == RotationalMotorEvent.TEST_STRIKE:
                    self.test_strike()
                else:
                    raise Exception("Unknown event in rotational motor", last_event)

    def quick_strike(self):
        """
        Strike the ball with the m2 motor.
        :return:
        """
        self.move_to_pos(self.measurements.enc_m2_360_rotation + 60, accell=48000, speed=6000, deccell=32000)
        time.sleep(0.1)
        self.move_to_default_pos()
        time.sleep(0.1)


    def strike(self):
        """
        Strike the ball with the m2 motor.
        :return:
        """

        # Gets the shortest distance to move player to strike start position and moves there.
        with self.lock:
            curr_pos = self.roboclaw.ReadEncM2(self.address)[1]
        nearest_0 = curr_pos % self.measurements.enc_m2_360_rotation
        if nearest_0 > self.measurements.enc_m2_360_rotation / 2:
            nearest_0 = self.measurements.enc_m2_360_rotation - nearest_0
        else:
            nearest_0 = -nearest_0
        # self.move_to_pos_m2(nearest_0 + self.measurements.enc_m2_strike, accell=32000, speed=4000, deccell=32000)
        self.move_backward(35)

        # Moves the player to strike end position.
        while True:
            # Don't wait for motors to reach exactly the strike start position because it will be too slow.
            with self.lock:
                enc_m2 = self.roboclaw.ReadEncM2(self.address)[1]
            if enc_m2 <= nearest_0 + self.measurements.enc_m2_strike:
                break
        self.stop()
        self.move_forward(120)
        time.sleep(0.08)
        self.move_forward(60)
        time.sleep(0.02)
        # Moves the player back to start position.
        self.move_to_default_pos()

    def test_strike(self):
        start_time = time.time()
        print("Latency test end time", time.time())
        print("Rotational motor: Test strike start time", start_time)
        self.strike()
        print("Rotational motor: Test strike end time", time.time() - start_time)
        print("Rotational motor end time", time.time())

    def move_backward(self, speed=30):
        """
        Moves motor 2 backward at the given speed.
        :param speed:
        :return:
        """
        with self.lock:
            self.roboclaw.BackwardM2(self.address, speed)

    def move_forward(self, speed=30):
        """
        Moves motor 2 forward at the given speed.
        :param speed:
        :return:
        """
        with self.lock:
            self.roboclaw.ForwardM2(self.address, speed)

    def move_to_default_pos(self):
        """
        Move to default position which is player facing directly down.
        Default pos is 145 instead of 0 because can't move negative encoder values.
        :return:
        """
        self.move_to_pos(self.measurements.enc_m2_default)

    def move_to_pos(self, pos, accell=14000, speed=2000, deccell=14000):
        """
        Moves motor 2 to the given encoder position.
        :param pos:
        :return:
        """
        with self.lock:
            self.roboclaw.SpeedAccelDeccelPositionM2(self.address, accell, speed, deccell, pos, 1)

    def home(self):
        """
        Sets the encoder position of motor 2 to 0.
        :return:
        """
        with self.lock:
            self.roboclaw.SetEncM2(self.address, 145)
        self.homed = True

    def stop(self):
        """
        Stops motor 2.
        :return:
        """
        with self.lock:
            self.roboclaw.ForwardM2(self.address, 0)


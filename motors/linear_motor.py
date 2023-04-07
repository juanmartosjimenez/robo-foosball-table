import multiprocessing
import queue
import time
from queue import Queue

from motors.motor_measurements import MotorMeasurements
from motors.roboclaw import Roboclaw
from other.events import LinearMotorEvent


class LinearMotor:
    def __init__(self, queue_to_linear_motors: Queue, queue_from_linear_motors: Queue, roboclaw: Roboclaw,
                 stop_flag: multiprocessing.Event, lock: multiprocessing.Lock):
        self.measurements = MotorMeasurements()
        self.address = self.measurements.address
        self.queue_to_motors = queue_to_linear_motors
        self.queue_from_motors = queue_from_linear_motors
        self.roboclaw: Roboclaw = roboclaw
        self.stop_flag = stop_flag
        self.lock = lock

    def event_loop(self):
        while True:
            time.sleep(0.01)
            last_event = None
            # Only interested in the last event.
            if self.stop_flag.is_set():
                try:
                    self.stop()
                except Exception as e:
                    pass
                return

            while True:
                try:
                    last_event = self.queue_to_motors.get_nowait()
                except queue.Empty:
                    break

            if last_event is not None:
                event = last_event[0]
                if event == LinearMotorEvent.MOVE_TO_POS:
                    print(last_event[1])
                    self.move_to_pos(last_event[1])
                elif event == LinearMotorEvent.HOME:
                    self.home()
                elif event == LinearMotorEvent.MOVE_TO_DEFAULT:
                    self.move_to_default()
                else:
                    raise Exception("Unknown event in linear motor", last_event)

    def move_to_pos(self, mm):
        """
        Moves the goalie to the center of the goal.
        :return:
        """
        mm_distance_to_goalie_2 = 240
        mm_distance_to_goalie_1 = 45
        mm_distance_to_goalie_3 = 435
        mm_goalie_2_movement = self._mm_to_encoder(mm - mm_distance_to_goalie_2)
        mm_goalie_1_movement = self._mm_to_encoder(mm - mm_distance_to_goalie_1)
        mm_goalie_3_movement = self._mm_to_encoder(mm - mm_distance_to_goalie_3)
        if -650 < mm_goalie_2_movement < self.measurements.m1_encoder_limit + 650:
            #print("goalie2 moving")
            self._move_to_pos(mm_goalie_2_movement)
        elif mm_goalie_2_movement < -650:
            #print("goalie1 moving")
            self._move_to_pos(mm_goalie_1_movement)
        elif mm_goalie_2_movement > self.measurements.m1_encoder_limit:
            #print("goalie3 moving")
            self._move_to_pos(mm_goalie_3_movement)

    def _mm_to_encoder(self, mm: float) -> int:
        """
        Converts inches to encoder position.
        :param mm:
        :return:
        """
        return int(mm * self.measurements.m1_mm_to_enc)

    def _move_to_pos(self, pos):
        """
        Moves motor 1 to the given encoder position.
        :param pos:
        :return:
        """
        # if pos > self.right_limit:
        # raise ValueError("Position out of range")
        if pos < 0: pos = 100
        if pos > self.measurements.m1_encoder_limit: pos = self.measurements.m1_encoder_limit - 100
        with self.lock:
            self.roboclaw.SpeedAccelDeccelPositionM1(self.address, 16000, 4000, 16000, pos, 1)

    def home(self):
        """
        Moves motor 1 to the left limit until limit switch is triggered.
        Firmware is set to reset encoder to 0 when limit switch is triggered.
        :return:
        """
        with self.lock:
            self.roboclaw.BackwardM1(self.address, 30)
        while True:
            time.sleep(0.4)
            with self.lock:
                speed = self.roboclaw.ReadSpeedM1(self.address)[1]
            if speed == 0:
                self.stop()
                break

    def stop(self):
        """
        Stops motor 1.
        :return:
        """
        with self.lock:
            self.roboclaw.ForwardM1(self.address, 0)

    def move_to_default(self):
        """
        Move to default position which is center of goal.
        :return:
        """
        self._move_to_pos(self.measurements.enc_m1_default)

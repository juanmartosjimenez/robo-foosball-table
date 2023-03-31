from queue import Queue

from motors.motor_measurements import MotorMeasurements
from motors.roboclaw import Roboclaw
from other.events import LinearMotorEvent


class LinearMotor:
    def __init__(self, queue_to_linear_motors: Queue, queue_from_linear_motors: Queue, roboclaw: Roboclaw, measurements: MotorMeasurements, ):
        self.queue_to_motors = queue_to_linear_motors
        self.queue_from_motors = queue_from_linear_motors
        self.roboclaw: Roboclaw = roboclaw

    def event_loop(self):
        while True:
            last_event = None
            # Only interested in the last event.
            while not self.queue_to_motors.empty():
                last_event = self.queue_to_motors.get_nowait()

            if last_event is not None:
                if last_event[0] == LinearMotorEvent.MOVE_TO_POS:



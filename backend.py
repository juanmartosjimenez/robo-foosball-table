import multiprocessing
import queue
from camera.camera_manager import CameraManager
from motors.motor_manager import MotorManager
from multiprocessing import Queue
from typing import TYPE_CHECKING, Optional
import traceback
import threading

from other.events import FrontendEvent, MotorEvent, CameraEvent

if TYPE_CHECKING:
    from app import Frontend

from subscriber_publisher import Publisher


class Backend(object):
    def __init__(self):
        self.queue_from_camera = Queue()
        self.queue_from_motors = Queue()
        self.queue_to_camera = Queue()
        self.queue_to_motors = Queue()
        self.frontend: Optional[Frontend] = None
        self.publisher = Publisher(
            events=[FrontendEvent.ENCODER_VALS, FrontendEvent.CURRENT_BALL_POS, FrontendEvent.PREDICTED_BALL_POS,
                    FrontendEvent.ERROR])
        self.active_threads = []

        try:
            self.motor_manager = MotorManager()
        except Exception as e:
            self.publisher.publish(FrontendEvent.ERROR, e)
            raise e
        self.start_motors_event_loop()
        try:
            self.camera_manager = CameraManager()
        except Exception as e:
            # print(traceback.format_exc())
            # print(e)
            self.publisher.publish(FrontendEvent.ERROR, e)
            raise e
        self.start_camera_event_loop()

    def _read_motors(self):
        try:
            queue_data = self.queue_from_motors.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == MotorEvent.ENCODER_VALS:
                self.publisher.publish(FrontendEvent.ENCODER_VALS, data)
        except queue.Empty:
            return

    def _read_camera(self):
        try:
            queue_data = self.queue_from_camera.get_nowait()
            event = queue_data[0]
            data = queue_data[1]

            if event == CameraEvent.CURRENT_BALL_POS:
                self.publisher.publish(FrontendEvent.CURRENT_BALL_POS, data)
            elif event == CameraEvent.PREDICTED_BALL_POS:
                self.publisher.publish(FrontendEvent.PREDICTED_BALL_POS, data)
                self.queue_to_motors.put_nowait((MotorEvent.MOVE_TO_MM_M1, data["mm"][0]))
            else:
                print(f"Unknown read_camera event: {str(queue_data)}")
        except queue.Empty:
            return

    def event_loop(self):
        # Get data from camera
        self._read_camera()
        # Get data from motors
        self._read_motors()

    def start_camera_event_loop(self):
        self.active_threads.append(multiprocessing.Process(target=self.camera_manager.event_loop,
                                                    args=(self.queue_to_camera, self.queue_from_camera)).start())

    def start_motors_event_loop(self):
        self.active_threads.append(threading.Thread(target=self.motor_manager.event_loop,
                                                    args=(self.queue_to_motors, self.queue_from_motors)).start())

    def home_m1(self):
        self.queue_to_motors.put_nowait((MotorEvent.HOME_M1, None))

    def home_m2(self):
        self.queue_to_motors.put_nowait((MotorEvent.HOME_M2, None))

    def start_ball_tracking(self):
        self.queue_to_camera.put_nowait((CameraEvent.START_BALL_TRACKING, None))

    def move_to_default(self):
        self.queue_to_motors.put_nowait((MotorEvent.MOVE_TO_START_POS, None))

import multiprocessing
import queue
import time

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
        self.stop_flag = multiprocessing.Event()
        self.stop_flag.set()

    def assert_not_stopped(self):
        if self.stop_flag.is_set():
            self.publisher.publish(FrontendEvent.ERROR, "Robot is at Stop state.")

    def _clear_queues(self):
        while not self.queue_from_camera.empty():
            self.queue_from_camera.get_nowait()
        while not self.queue_from_motors.empty():
            self.queue_from_motors.get_nowait()
        while not self.queue_to_camera.empty():
            self.queue_to_camera.get_nowait()
        while not self.queue_to_motors.empty():
            self.queue_to_motors.get_nowait()

    def start(self):
        self._clear_queues()
        self.stop_flag.clear()
        self.start_camera_process()
        self.start_motor_process()

    def stop(self):
        self.stop_flag.set()

def start_motor_process(queue_to_motors, queue_from_motors, stop_flag):
    try:
        motor_manager = MotorManager(stop_flag, queue_to_motors, queue_from_motors)
        motor_manager.event_loop()
    except Exception as e:
        queue_from_motors.put_nowait((MotorEvent.ERROR, str(e)))
        raise e


def start_camera_process(queue_to_camera, queue_from_camera, stop_flag):
    try:
        camera_manager = CameraManager(stop_flag, queue_to_camera, queue_from_camera)
        camera_manager.event_loop()
    except Exception as e:
        queue_from_camera.put_nowait((CameraEvent.ERROR, str(e)))
        raise e

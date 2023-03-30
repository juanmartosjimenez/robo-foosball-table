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

    def _read_motors(self):
        try:
            queue_data = self.queue_from_motors.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == MotorEvent.ENCODER_VALS:
                self.publisher.publish(FrontendEvent.ENCODER_VALS, data)
            elif event == MotorEvent.ERROR:
                self.stop_flag.set()
                self.publisher.publish(FrontendEvent.ERROR, data)
            elif event == MotorEvent.STRIKE:
                pass
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
            elif event == CameraEvent.ERROR:
                self.stop_flag.set()
                self.publisher.publish(FrontendEvent.ERROR, data)
            elif event == CameraEvent.FPS:
                self.publisher.publish(FrontendEvent.FPS, data)
            elif event == CameraEvent.STRIKE:
                self.queue_to_motors.put_nowait((MotorEvent.STRIKE, None))
            else:
                print(f"Unknown read_camera event: {str(queue_data)}")
        except queue.Empty:
            return

    def event_loop(self):
        # Get data from camera
        self._read_camera()
        # Get data from motors
        self._read_motors()

    def start_camera_process(self):
        self.active_threads.append(multiprocessing.Process(target=start_camera_process,
                                                           args=(self.queue_to_camera, self.queue_from_camera, self.stop_flag)).start())

    def start_motor_process(self):
        self.active_threads.append(multiprocessing.Process(target=start_motor_process,
                                                           args=(self.queue_to_motors, self.queue_from_motors, self.stop_flag)).start())

    def home_m1(self):
        self.assert_not_stopped()
        self.queue_to_motors.put_nowait((MotorEvent.HOME_M1, None))

    def home_m2(self):
        self.assert_not_stopped()
        self.queue_to_motors.put_nowait((MotorEvent.HOME_M2, None))

    def start_ball_tracking(self):
        self.assert_not_stopped()
        self.queue_to_camera.put_nowait((CameraEvent.START_BALL_TRACKING, None))

    def move_to_default(self):
        self.assert_not_stopped()
        self.queue_to_motors.put_nowait((MotorEvent.MOVE_TO_START_POS, None))


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

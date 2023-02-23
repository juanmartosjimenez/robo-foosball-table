import queue
from camera.camera_manager import CameraManager
from motors.motor_manager import MotorManager
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Optional
import traceback

if TYPE_CHECKING:
    from frontend import Frontend

from subscriber_publisher import Publisher


class Backend(object):
    def __init__(self):
        self.queue_from_camera = Queue()
        self.queue_from_motors = Queue()
        self.queue_to_camera = Queue()
        self.queue_to_motors = Queue()
        self.frontend: Optional[Frontend] = None
        self.publisher = Publisher(events=["read_encoders", "ball_pos", "goalie_ball_pos", "error"])
        self.active_threads = []

        try:
            self.motor_manager = MotorManager()
        except Exception as e:
            print(traceback.format_exc())
            self.publisher.publish("error", e)
            return
        self.start_motors_event_loop()
        try:
            self.camera_manager = CameraManager()
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            self.publisher.publish("error", e)
            return
        self.start_camera_event_loop()


    def _read_motors(self):
        try:
            queue_data = self.queue_from_motors.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == "read_encoders":
                self.publisher.publish("goalie_m1_encoders", data)
        except queue.Empty:
            return

    def _read_camera(self):
        try:
            queue_data = self.queue_from_camera.get_nowait()
            event = queue_data[0]
            data = queue_data[1]

            if event == 'ball_pos':
                print(data)
            elif event == 'goalie_ball_pos':
                self.queue_to_motors.put_nowait(("move_to_mm_m1", data))
            else:
                print("Unknown event: " + event)
        except queue.Empty:
            return

    def event_loop(self):
        print("backend_event_loop")
        # Get data from camera
        self._read_camera()
        # Get data from motors
        self._read_motors()

    def start_camera_event_loop(self):
        print("start_camera_event_loop")
        self.active_threads.append(Process(target=self.camera_manager.event_loop, args=(
        {"queue_to_camera": self.queue_to_camera, "queue_from_camera": self.queue_from_camera})))

    def start_motors_event_loop(self):
        print("start_motors_event_loop")
        self.active_threads.append(Process(target=self.motor_manager.event_loop, args=(
        {"queue_to_motors": self.queue_to_motors, "queue_from_motors": self.queue_from_motors})))

    def home(self):
        self.queue_to_motors.put_nowait(("home_m1", None))
        self.queue_to_motors.put_nowait(("home_m2", None))

    def start_ball_tracking(self):
        self.queue_to_camera.put_nowait(("start_ball_tracking", None))



import time

import queue
from camera.camera_manager import CameraManager
from motors.motor_manager import MotorManager
from multiprocessing import Process, current_process, Queue


class Backend(object):
    def __init__(self):
        self.queue_from_camera = Queue()
        self.queue_from_motors = Queue()
        self.queue_to_camera = Queue()
        self.queue_to_motors = Queue()
        try:
            self.motor_manager = MotorManager()
        except Exception as e:
            print(e)
        self.camera_manager = CameraManager()
        self.active_threads = []

    def _read_motors(self):
        try:
            queue_data = self.queue_from_motors.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == "read_encoders":
                print(data)
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
        while True:
            # Get data from camera
            self._read_camera()
            # Get data from motors
            self._read_motors()

    def start_camera_event_loop(self):
        self.active_threads.append(Process(target=self.camera_manager.event_loop, args=({"queue_to_camera": self.queue_to_camera, "queue_from_camera": self.queue_from_camera})))

    def start_motors_event_loop(self):
        self.active_threads.append(Process(target=lambda: self.motor_manager.event_loop, args=({"queue_to_motors": self.queue_to_motors, "queue_from_motors": self.queue_from_motors})))







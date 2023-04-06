import multiprocessing as mp
from multiprocessing import Process
from app import Frontend
from camera.camera_manager import CameraManager
from motors.motor_manager import MotorManager
from other.events import MotorEvent


class ProcessManager:
    def __init__(self):
        self.queue_from_camera = mp.Queue()
        self.queue_from_motors = mp.Queue()
        self.queue_to_camera = mp.Queue()
        self.queue_to_motors = mp.Queue()
        self.queue_to_tkinter_frontend = mp.Queue()
        self.queue_from_tkinter_frontend = mp.Queue()
        self.queue_to_flask = mp.Queue()
        self.queue_from_flask = mp.Queue()
        self.stop_flag = mp.Event()
        self.tkinter_frontend_process = Process(target=start_tkinter_process,
                                                args=(self.queue_to_tkinter_frontend, self.queue_from_tkinter_frontend))
        self.camera_process = Process(target=start_camera_process,
                                      args=(self.queue_to_camera, self.queue_from_camera, self.stop_flag))
        self.motor_process = Process(target=start_motor_process,
                                     args=(self.queue_to_motors, self.queue_from_motors, self.stop_flag))
        self.flask_process = Process(target=start_flask_process,
                                     args=(self.queue_to_flask, self.queue_from_flask))
        self.active_threads = []
        self.stop_flag = mp.Event()

    def run(self):
        self.tkinter_frontend_process


def start_motor_process(queue_to_motors, queue_from_motors, stop_flag):
    try:
        motor_manager = MotorManager(stop_flag, queue_to_motors, queue_from_motors)
        motor_manager.event_loop()
    except Exception as e:
        queue_from_motors.put_nowait(("ERROR", str(e)))
        raise e


def start_tkinter_process(queue_to_tkinter_frontend, queue_from_tkinter_frontend, stop_flag):
    try:
        frontend = Frontend(stop_flag, queue_to_tkinter_frontend, queue_from_tkinter_frontend)
        frontend.run()
    except Exception as e:
        queue_from_tkinter_frontend.put_nowait(("ERROR", str(e)))
        raise e


def start_camera_process(queue_to_camera, queue_from_camera, stop_flag):
    try:
        camera_manager = CameraManager(stop_flag, queue_to_camera, queue_from_camera)
        camera_manager.event_loop()
    except Exception as e:
        queue_from_camera.put_nowait(("ERROR", str(e)))
        raise e


def start_flask_process(queue_to_flask, queue_from_flask):
    from foosball_app.backend.server import app as flask_app
    try:
        flask_app.queue_to_flask = queue_to_flask
        flask_app.queue_from_flask = queue_from_flask
        flask_app.run(debug=False)
    except Exception as e:
        queue_from_flask.put_nowait(("ERROR", str(e)))
        raise e

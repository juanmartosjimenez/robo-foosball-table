import multiprocessing as mp
import queue
import time
from multiprocessing import Process
from python_frontend.tkinter_frontend import Frontend
from camera.camera_manager import CameraManager
from motors.motor_manager import MotorManager
from other.events import MotorEvent, FrontendEvent, CameraEvent, FlaskAppEvent


class ProcessManager:
    def __init__(self):
        self.queue_from_camera = mp.Queue()
        self.queue_from_motors = mp.Queue()
        self.queue_to_camera = mp.Queue()
        self.queue_to_motors = mp.Queue()
        self.queue_to_tkinter_frontend = mp.Queue()
        self.queue_from_tkinter_frontend = mp.Queue()
        self.camera_queue_to_tkinter_frontend = mp.Queue()
        self.queue_to_flask = mp.Queue()
        self.queue_from_flask = mp.Queue()
        self.queue_to_ball_prediction = mp.Queue()
        self.queue_from_ball_prediction = mp.Queue()
        self.stop_flag = mp.Event()
        self.stop_flag.set()
        self.tkinter_frontend_process = Process(target=start_tkinter_process,
                                                args=(self.queue_to_tkinter_frontend, self.queue_from_tkinter_frontend, self.camera_queue_to_tkinter_frontend))
        self.camera_process = Process(target=start_camera_process,
                                      args=(self.queue_to_camera, self.queue_from_camera, self.stop_flag))
        self.motor_process = Process(target=start_motor_process,
                                     args=(self.queue_to_motors, self.queue_from_motors, self.stop_flag))
        self.flask_process = Process(target=start_flask_process,
                                     args=(self.queue_to_flask, self.queue_from_flask))
        self.active_threads = []
        self.active_threads.append(self.tkinter_frontend_process)
        self.active_threads.append(self.camera_process)
        self.active_threads.append(self.motor_process)
        self.active_threads.append(self.flask_process)

    def run(self):
        self.tkinter_frontend_process.start()
        # self.flask_process.start()
        self.event_loop()

    def event_loop(self):
        start_time = time.time()
        iterations = 0
        while True:
            iterations += 1
            if time.time() - start_time > 1:
                start_time = time.time()
                iterations = 0

            self._read_camera()
            self._read_motors()
            self._read_tkinter_frontend()
            self._read_flask()

    def _clear_queues(self):
        while not self.queue_from_camera.empty():
            self.queue_from_camera.get_nowait()
        while not self.queue_to_camera.empty():
            self.queue_to_camera.get_nowait()
        while not self.queue_to_motors.empty():
            self.queue_to_motors.get_nowait()
        while not self.queue_to_tkinter_frontend.empty():
            self.queue_to_tkinter_frontend.get_nowait()
        while not self.queue_from_tkinter_frontend.empty():
            self.queue_from_tkinter_frontend.get_nowait()
        while not self.queue_to_flask.empty():
            self.queue_to_flask.get_nowait()
        while not self.queue_from_motors.empty():
            self.queue_from_motors.get_nowait()
        while not self.queue_from_flask.empty():
            self.queue_from_flask.get_nowait()

    def _power_on(self):
        self._clear_queues()
        self.stop_flag.clear()
        self.camera_process.start()
        self.motor_process.start()

    def _read_motors(self):
        try:
            queue_data = self.queue_from_motors.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == MotorEvent.ENCODER_VALS:
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.ENCODER_VALS, data))
            elif event == MotorEvent.ERROR:
                self.stop_flag.set()
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.ERROR, data))
        except queue.Empty:
            return

    def _read_camera(self):
        try:
            queue_data = self.queue_from_camera.get_nowait()
            event = queue_data[0]
            data = queue_data[1]

            if event == CameraEvent.CURRENT_BALL_POS:
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.CURRENT_BALL_POS, data))
            elif event == CameraEvent.PREDICTED_BALL_POS:
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.PREDICTED_BALL_POS, data))
                self.queue_to_motors.put_nowait((MotorEvent.MOVE_TO_POS, data["mm"][0]))
            elif event == CameraEvent.ERROR:
                self.stop_flag.set()
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.ERROR, data))
            elif event == CameraEvent.FPS:
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.FPS, data))
            elif event == CameraEvent.STRIKE:
                self.queue_to_motors.put_nowait((MotorEvent.STRIKE, None))
            elif event == CameraEvent.QUICK_STRIKE:
                self.queue_to_motors.put_nowait((MotorEvent.QUICK_STRIKE, None))
            elif event == CameraEvent.TEST_STRIKE:
                self.queue_to_motors.put_nowait((MotorEvent.TEST_STRIKE, None))
            elif event == CameraEvent.CURRENT_FRAME:
                self.camera_queue_to_tkinter_frontend.put_nowait((FrontendEvent.CURRENT_FRAME, data))
            else:
                print(f"Unknown read_camera event: {str(queue_data)}")
        except queue.Empty:
            return

    def _read_flask(self):
        try:
            queue_data = self.queue_from_flask.get_nowait()
            event = queue_data[0]
            data = queue_data[1]

            if event == FlaskAppEvent.ERROR:
                self.stop_flag.set()
                self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.ERROR, data))
            elif event == FlaskAppEvent.START:
                self._assert_not_stopped()
                self.queue_to_camera.put_nowait((CameraEvent.START_BALL_TRACKING, None))
            elif event == FlaskAppEvent.STOP:
                self.stop_flag.set()
            elif event == FlaskAppEvent.POWER_ON:
                self._power_on()
            else:
                print(f"Unknown read_camera event: {str(queue_data)}")
        except queue.Empty:
            return

    def _assert_not_stopped(self):
        if self.stop_flag.is_set():
            self.queue_to_tkinter_frontend.put_nowait((FrontendEvent.ERROR, "Robot is at Stop state."))

    def _read_tkinter_frontend(self):
        try:
            queue_data = self.queue_from_tkinter_frontend.get_nowait()
            event = queue_data[0]
            data = queue_data[1]
            if event == FrontendEvent.START:
                self._assert_not_stopped()
                self.queue_to_camera.put_nowait((CameraEvent.START_BALL_TRACKING, None))
            elif event == FrontendEvent.POWER_ON:
                self._power_on()
            elif event == FrontendEvent.STOP:
                self.stop_flag.set()
            elif event == FrontendEvent.ERROR:
                self.stop_flag.set()
            elif event == FrontendEvent.MOVE_TO_START_POS:
                self.queue_to_motors.put_nowait((MotorEvent.MOVE_TO_START_POS, None))
            elif event == FrontendEvent.TEST_LATENCY:
                print("Testing latency: start time", time.time())
                self.queue_to_camera.put_nowait((CameraEvent.TEST_STRIKE, None))
            elif event == FrontendEvent.HOME_M2:
                self._assert_not_stopped()
                self.queue_to_motors.put_nowait((MotorEvent.HOME_M2, None))
            elif event == FrontendEvent.HOME_M1:
                self._assert_not_stopped()
                self.queue_to_motors.put_nowait((MotorEvent.HOME_M1, None))
            else:
                print(f"Unknown read_tkinter_frontend event: {str(queue_data)}")
        except queue.Empty:
            return


def start_motor_process(queue_to_motors, queue_from_motors, stop_flag):
    try:
        motor_manager = MotorManager(stop_flag, queue_to_motors, queue_from_motors)
        motor_manager.event_loop()
    except Exception as e:
        queue_from_motors.put_nowait(("ERROR", str(e)))
        raise e


def start_tkinter_process(queue_to_tkinter_frontend, queue_from_tkinter_frontend, camera_queue_to_frontend):
    try:
        frontend = Frontend(queue_to_tkinter_frontend, queue_from_tkinter_frontend, camera_queue_to_frontend)
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


if __name__ == '__main__':
    process_manager = ProcessManager()
    process_manager.run()

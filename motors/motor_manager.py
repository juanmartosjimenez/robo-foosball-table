import multiprocessing
import queue
import threading
import time
import sys

from motors.linear_motor import LinearMotor
from motors.roboclaw import Roboclaw
import serial.tools.list_ports
from motors.motor_measurements import MotorMeasurements
from motors.rotational_motor import RotationalMotor
from other.events import MotorEvent, LinearMotorEvent, RotationalMotorEvent
from dotenv import load_dotenv
import os

load_dotenv()
SERIAL_PORT = os.getenv("SERIAL_PORT")


class MotorManager:
    def __init__(self, stop_flag: multiprocessing.Event, queue_to_motors: multiprocessing.Queue,
                 queue_from_motors: multiprocessing.Queue):
        # Initialize motor measurements.
        self.measurements = MotorMeasurements()
        # Since only one roboclaw is being used, default address is 0x80.
        self.address = 0x80
        # Initialize roboclaw object.

        if SERIAL_PORT is None:
            raise Exception("SERIAL_PORT not set in .env file. Create .env file in root directory and set SERIAL_PORT.")
        self.roboclaw: Roboclaw = Roboclaw(SERIAL_PORT, 38400)
        self.roboclaw.Open()
        self.stop_flag: multiprocessing.Event = stop_flag
        self.roboclaw_lock = threading.Lock()
        self.queue_to_motors = queue_to_motors
        self.queue_from_motors = queue_from_motors
        self.queue_to_linear_motor = queue.Queue()
        self.queue_from_linear_motor = queue.Queue()
        self.queue_to_rotational_motor = queue.Queue()
        self.queue_from_rotational_motor = queue.Queue()
        self.linear_motor = LinearMotor(self.queue_to_linear_motor, self.queue_from_linear_motor, self.roboclaw,
                                        self.stop_flag, self.roboclaw_lock)
        self.linear_motor_thread = threading.Thread(target=self.linear_motor.event_loop)
        self.linear_motor_thread.start()
        self.rotational_motor = RotationalMotor(self.queue_to_rotational_motor, self.queue_from_rotational_motor,
                                                self.roboclaw, self.stop_flag, self.roboclaw_lock)
        self.rotational_motor_thread = threading.Thread(target=self.rotational_motor.event_loop)
        self.rotational_motor_thread.start()

    def event_loop(self):
        """
        Event loop for the motor manager.
        :return:
        """
        start_time = time.time()
        while True:
            time.sleep(0.01)
            if self.stop_flag.is_set():
                try:
                    self.rotational_motor_thread.join()
                    self.linear_motor_thread.join()
                except Exception:
                    pass
                return

            try:
                data = self.queue_to_motors.get_nowait()
                event = data[0]
                if event == MotorEvent.HOME_M1:
                    self.queue_to_linear_motor.put_nowait((LinearMotorEvent.HOME, None))
                elif event == MotorEvent.HOME_M2:
                    self.queue_to_rotational_motor.put_nowait((RotationalMotorEvent.HOME, None))
                elif event == MotorEvent.MOVE_TO_POS:
                    self.queue_to_linear_motor.put_nowait((LinearMotorEvent.MOVE_TO_POS, data[1]))
                elif event == MotorEvent.STRIKE:
                    self.queue_to_linear_motor.put_nowait((RotationalMotorEvent.STRIKE, None))
                elif event == MotorEvent.ENCODER_VALS:
                    encoder_val = self.read_encoders()
                    self.queue_from_motors.put_nowait((MotorEvent.ENCODER_VALS, {"encoders": encoder_val,
                                                                                 "mm_m1": self._encoder_to_mm_m1(
                                                                                     encoder_val[0]),
                                                                                 "degrees_m2": self._encoder_to_degrees_m2(
                                                                                     encoder_val[0])}))
                elif event == MotorEvent.MOVE_TO_START_POS:
                    self.queue_to_rotational_motor.put_nowait((RotationalMotorEvent.MOVE_TO_DEFAULT, None))
                    self.queue_to_linear_motor.put_nowait((LinearMotorEvent.MOVE_TO_DEFAULT, None))
                elif event == MotorEvent.TEST_STRIKE:
                    print("Motor Manager start", time.time())
                    start_time = time.time()
                    self.queue_to_rotational_motor.put_nowait((RotationalMotorEvent.TEST_STRIKE, None))
                    print("Motor Manager end", time.time())
                    print("Motor Manager time elapsed", time.time() - start_time)
                else:
                    raise ValueError("Unknown motor_manager event: " + data)
            except queue.Empty:
                if time.time() - start_time > 1:
                    # Every 1 seconds, read the encoders.
                    start_time = time.time()
                    self.queue_to_motors.put_nowait((MotorEvent.ENCODER_VALS, None))
                    end_time = time.time()
                    # print("Reading encoders time elapsed", end_time - start_time)
                pass

    @staticmethod
    def read_serial_ports():
        """
        Reads connected serial ports, useful to identify what port the roboclaw is connected to.
        :return:
        """
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            print(p.manufacturer)
            print(p.device)
            print(p.description)
            print()

    def read_encoders(self):
        """
        Returns the encoder positions for both motors.
        :return:
        """
        with self.roboclaw_lock:
            return self.roboclaw.ReadEncM1(self.address)[1], self.roboclaw.ReadEncM2(self.address)[1]

    def read_encoder_counters(self):
        """
        Reads the encoder counters for both motors.
        :return:
        """
        with self.roboclaw_lock:
            return self.roboclaw.ReadEncoderCounters(self.address)

    def _encoder_to_mm_m1(self, encoder: int) -> float:
        """
        Converts encoder position to inches.
        :param encoder:
        :return:
        """
        return round(encoder / self.measurements.m1_mm_to_enc, 2)

    def _encoder_to_degrees_m2(self, encoder: int) -> float:
        """
        Converts encoder position to degrees.
        :param encoder:
        :return:
        """
        return round(encoder % self.measurements.enc_m2_360_rotation, 2)

    def home(self):
        """
        Moves motor 1 to the left limit until limit switch is triggered.
        Firmware is set to reset encoder to 0 when limit switch is triggered.
        :return:
        """
        with self.roboclaw_lock:
            self.roboclaw.BackwardM1(self.address, 30)
        while True:
            time.sleep(0.4)

            with self.roboclaw_lock:
                if self.roboclaw.ReadSpeedM1(self.address)[1] == 0:
                    self.roboclaw.ForwardM1(self.address, 0)
                    break


if __name__ == "__main__":
    MotorManager.read_serial_ports()
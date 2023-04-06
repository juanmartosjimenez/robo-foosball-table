import tkinter as tk
from multiprocessing import Queue
from tkinter import messagebox
from typing import Optional
import traceback

from backend import Backend
from other.events import FrontendEvent


class Frontend(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Robot GUI")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        # set dimensions
        self.geometry("1600x480")
        self.backend = Backend()
        self.backend.publisher.add_subscriber(FrontendEvent.ENCODER_VALS, self.update_encoder_positions)
        self.backend.publisher.add_subscriber(FrontendEvent.CURRENT_BALL_POS, self.update_ball_position)
        self.backend.publisher.add_subscriber(FrontendEvent.PREDICTED_BALL_POS, self.update_predicted_ball_position)
        self.backend.publisher.add_subscriber(FrontendEvent.ERROR, self.display_error)
        self.backend.publisher.add_subscriber(FrontendEvent.FPS, self.update_fps)
        self.backend.frontend = self
        self.fps_var = tk.StringVar()
        self.fps_var.set("FPS: ")
        self.encoder_var = tk.StringVar()
        self.encoder_var.set("M1 Encoder:  M2 Encoder:  M1 MM:  M2 Degrees:  ")
        self.encoder_label = tk.Label(self, textvariable=self.encoder_var, font=("Helvetica", 20))
        self.encoder_label.grid(row=0, column=0, sticky="NSWE", columnspan=2)
        self.ball_position_var = tk.StringVar()
        self.ball_position_var.set("Ball Pixels (). Ball MM ()")
        self.ball_position_label = tk.Label(self, textvariable=self.ball_position_var, font=("Helvetica", 20))
        self.ball_position_label.grid(row=1, column=0, sticky="NSWE", columnspan=2)
        self.predicted_ball_var = tk.StringVar()
        self.predicted_ball_var.set("Predicted Ball Pixels (). Predicted Ball MM ().")
        self.goalie_ball_position_label = tk.Label(self, textvariable=self.predicted_ball_var, font=("Helvetica", 20))
        self.goalie_ball_position_label.grid(row=2, column=0, sticky="NSWE", columnspan=2)
        self.fps_label = tk.Label(self, textvariable=self.fps_var, font=("Helvetica", 20))
        self.fps_label.grid(row=3, column=0, sticky="NSWE", columnspan=2)

        self.home_m1_button = tk.Button(self, text="Home M1", command=self.home_m1)
        self.home_m1_button.grid(row=4, column=0)
        self.home_m2_button = tk.Button(self, text="Home M2", command=self.home_m2)
        self.home_m2_button.grid(row=4, column=1)
        self.move_to_default_button = tk.Button(self, text="Move to Default", command=self.backend.move_to_default)
        self.move_to_default_button.grid(row=5, column=0)
        self.start_ball_tracking_button = tk.Button(self, text="Start",
                                                    command=lambda: self.start_ball_tracking())
        self.start_ball_tracking_button.grid(row=5, column=1)

        self.power_on = tk.Button(self, text="Power On", command=lambda: self.backend.start())
        self.power_on.grid(row=6, column=0)
        self.stop = tk.Button(self, text="Stop", command=lambda: self.backend.stop())
        self.stop.grid(row=6, column=1)

        self.test_latency_button = tk.Button(self, text="Test Latency", command=lambda: self.backend.test_latency())
        self.test_latency_button.grid(row=7, column=0)



        def backend_helper():
            self.backend.event_loop()
            self.after(1, backend_helper)

        backend_helper()

    def start_ball_tracking(self):
        messagebox.showinfo("Start",
                            "Make sure that there are no obstructions on the playing field before pressing Ok.")
        self.backend.start_ball_tracking()

    def home_m1(self):
        self.backend.home_m1()

    def update_fps(self, data):
        self.fps_var.set(f'FPS: {str(data)}')

    def home_m2(self):
        self.backend.home_m2()

    def update_encoder_positions(self, data):
        self.encoder_var.set(
            f'M1 Encoder:{data["encoders"][0]}, M2 Encoder:{data["encoders"][1]}, M1 MM:{data["mm_m1"]}, M2 Degrees:{data["degrees_m2"]}')

    def update_ball_position(self, data):
        self.ball_position_var.set(f'Ball Pixel ({data["pixel"][0]}, {data["pixel"][1]}). Ball MM ({data["mm"][0]}, {data["mm"][1]}).')

    def update_predicted_ball_position(self, data):
        self.predicted_ball_var.set(f'Predicted Ball Pixel ({data["pixel"][0]}, {data["pixel"][1]}). Predicted Ball MM ({data["mm"][0]}, {data["mm"][1]}).')

    def display_error(self, error):
        messagebox.showerror("Error", str(error))

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    def report_callback_exception(self, exc, val, tb):
        messagebox.showerror("Error", message=str(val))

    tk.Tk.report_callback_exception = report_callback_exception

    frontend = Frontend()
    frontend.run()

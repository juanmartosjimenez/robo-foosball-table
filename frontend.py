import tkinter as tk
from multiprocessing import Queue
from tkinter import messagebox
from typing import Optional
import traceback

from backend import Backend


class Frontend(tk.Tk):
    def __init__(self):
        super().__init__()
        self.backend = Backend()
        self.backend.publisher.add_subscriber("read_encoders", self.update_encoder_positions)
        self.backend.publisher.add_subscriber("ball_pos", self.update_ball_position)
        self.backend.publisher.add_subscriber("goalie_ball_pos", self.update_goalie_ball_position)
        self.backend.publisher.add_subscriber("error", self.display_error)
        self.backend.frontend = self
        self.encoder_var = tk.StringVar()
        self.encoder_var.set("M1 Encoder:  M2 Encoder:  M1 MM:  M2 Degrees:  ")
        self.encoder_label = tk.Label(self, textvariable=self.encoder_var)
        self.encoder_label.grid(row=0, column=0)
        self.ball_position_var = tk.StringVar()
        self.ball_position_var.set("Ball Position:  ")
        self.ball_position_label = tk.Label(self, textvariable=self.ball_position_var)
        self.ball_position_label.grid(row=0, column=1)
        self.goalie_ball_position_var = tk.StringVar()
        self.goalie_ball_position_var.set("Goalie Ball Position:  ")
        self.goalie_ball_position_label = tk.Label(self, textvariable=self.goalie_ball_position_var)
        self.goalie_ball_position_label.grid(row=0, column=2)
        self.home_button = tk.Button(self, text="Home", command=self.home)
        self.home_button.grid(row=1, column=0)
        self.start_ball_tracking_button = tk.Button(self, text="Start Ball Tracking", command=lambda: self.start_ball_tracking())
        self.start_ball_tracking_button.grid(row=1, column=1)

        def backend_helper():
            self.backend.event_loop()
            self.after(50, backend_helper)

        backend_helper()

    def start_ball_tracking(self):
        messagebox.showinfo("Start", "Make sure that there are no obstructions on the playing field before pressing Ok.")
        self.backend.start_ball_tracking()

    def home(self):
        messagebox.showinfo("Home", "Make sure that the players are facing down before pressing OK.")
        self.backend.home()

    def update_encoder_positions(self, data):
        self.encoder_var.set(
            f'M1 Encoder:{data["encoders"][0]}, M2 Encoder:{data["encoders"][1]}, M1 MM:{data["mm_m1"]}, M2 Degrees:{data["degrees_m2"]}')

    def update_ball_position(self, data):
        self.ball_position_var.set(f'Ball Position: {data}')

    def update_goalie_ball_position(self, data):
        self.goalie_ball_position_var.set(f'Goalie Ball Position: {data}')

    def display_error(self, error):
        messagebox.showerror("Error", traceback.format_exc())

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    frontend = Frontend()
    frontend.run()
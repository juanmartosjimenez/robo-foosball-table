import tkinter as tk
from backend import Backend

class Frontend(tk.Frame):
    def __init__(self):
        super().__init__()
        self.backend = Backend()
        self.home_m1_button = tk.Button(self, text="Start robo-foosball table", command=lambda: self.backend.home_m1())
        self.home_m1_button.grid(row=0, column=0)
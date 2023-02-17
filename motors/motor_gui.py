import tkinter as tk

from motors.hardware_manager import HardwareManager


class MotorGUI(tk.Frame):
    def __init__(self):
        super().__init__()
        self.hardware_manager = HardwareManager()
        self.home_m1_button = tk.Button(self, text="Home M1", command=lambda: self.hardware_manager.home_m1())
        self.home_m1_button.grid(row=0, column=0)
        self.home_m2_button = tk.Button(self, text="Home M2", command=lambda: self.hardware_manager.home_m2())
        self.home_m2_button.grid(row=0, column=1)
        self.stop_button = tk.Button(self, text="Stop", command=lambda: self.hardware_manager.stop())
        self.stop_button.grid(row=0, column=2)
        self.forward_m1_button = tk.Button(self, text="Forward M1", command=lambda: self.hardware_manager.move_forward_m1())
        self.forward_m1_button.grid(row=1, column=0)
        self.backward_m1_button = tk.Button(self, text="Backward M1", command=lambda: self.hardware_manager.move_backward_m1())
        self.backward_m1_button.grid(row=1, column=1)
        self.current_pos_label = tk.Label(self, text="Current encoder position: {}".format(self.hardware_manager.read_encoders()))
        self.current_pos_label.grid(row=2, column=0)
        self.refresh_pos_button = tk.Button(self, text="Refresh position", command=lambda: self.current_pos_label.config(text="Current encoder position: {}".format(self.hardware_manager.read_encoders())))
        self.refresh_pos_button.grid(row=2, column=1)
        self.move_to_pos_m1_entry = tk.Entry(self, textvariable=tk.StringVar(self, value="0"))
        self.move_to_pos_m1_entry.grid(row=3, column=0)
        self.move_to_pos_m1_button = tk.Button(self, text="Move to position M1", command=lambda: self.hardware_manager.move_to_pos_m1(int(self.move_to_pos_m1_entry.get() if self.move_to_pos_m1_entry.get() else 0)))
        self.move_to_pos_m1_button.grid(row=3, column=1)
        self.move_to_default_pos_m1_button = tk.Button(self, text="Move to default position", command=lambda: self.hardware_manager.move_to_default_pos_m1())
        self.move_to_default_pos_m1_button.grid(row=3, column=2)
        self.move_to_pos_m2_entry = tk.Entry(self, textvariable=tk.StringVar(self, value="0"))
        self.move_to_pos_m2_entry.grid(row=4, column=0)
        self.move_to_pos_m2_button = tk.Button(self, text="Move to position M2", command=lambda: self.hardware_manager.move_to_pos_m2(int(self.move_to_pos_m2_entry.get() if self.move_to_pos_m2_entry.get() else 0)))
        self.move_to_pos_m2_button.grid(row=4, column=1)
        self.move_to_default_pos_m2_button = tk.Button(self, text="Move to default position", command=lambda: self.hardware_manager.move_to_default_pos_m2())
        self.move_to_default_pos_m2_button.grid(row=4, column=2)
        self.strike_button = tk.Button(self, text="Strike", command=lambda: self.hardware_manager.strike_m2())
        self.strike_button.grid(row=5, column=0)
        self.move_to_mm_m1_entry = tk.Entry(self, textvariable=tk.StringVar(self, value="0"))
        self.move_to_mm_m1_entry.grid(row=6, column=0)
        self.move_to_mm_m1_button = tk.Button(self, text="Move to mm M1", command=lambda: self.hardware_manager.move_to_mm_m1(int(self.move_to_mm_m1_entry.get() if self.move_to_mm_m1_entry.get() else 0)))
        self.move_to_mm_m1_button.grid(row=6, column=1)






if __name__ == "__main__":
    win = tk.Tk()
    win.title("Motor GUI")
    motor_gui = MotorGUI()
    motor_gui.pack()
    win.mainloop()

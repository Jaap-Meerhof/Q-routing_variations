from tkinter import *
from tkinter import ttk
import time


class TinkerGUI:

    def __init__(self):
        root = Tk()
        root.title("simulator")
        root.geometry("400x200")
        self.progress_bar = ttk.Progressbar(root, orient=HORIZONTAL, length=450, mode='determinate')
        self.progress_bar.pack(pady=20)
        root.mainloop()


    def updateProgression(self, current_value, max_value):
        self.progress_bar['value'] = (100 * current_value) / max_value

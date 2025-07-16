import tkinter as tk
from tkinter import font
import requests
import threading
import time

class PerformanceDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        # Setup UI window
        self.title("Server Performance Monitor")
        self.geometry("600x500")
        self.configure(bg="#2E2E2E")
        self.resizable(False, False)

        # UI Styling
        self.default_bg = "#3C3C3C"
        self.alert_bg = "#8B0000"
        self.label_fg = "#FFFFFF"
        self.title_font = font.Font(family="Helvetica", size=16, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=12)
        self.status_font = font.Font(family="Helvetica", size=10)

        # Default varables
        self.server_ip = tk.StringVar()
        self.cpu_threshold = tk.DoubleVar(value=80.0)
        self.mem_threshold = tk.DoubleVar(value=80.0)
        self.load_threshold = tk.DoubleVar(value=2.0)
        self.monitoring = False

        # Setup UI to close on exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Setup the UI to close on exit properly
    def on_closing(self):
        self.monitoring = False
        self.destroy()

if __name__ == "__main__":
    app = PerformanceDashboard()
    app.mainloop()

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

        # Create UI
        self.create_widgets()

        # Setup UI to close on exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self["bg"], padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # User set configutation and monitoring control button
        config_frame = tk.LabelFrame(main_frame, text="Configuration", bg=self["bg"], fg=self.label_fg, padx=10, pady=10)
        config_frame.pack(fill="x", pady=(0, 15))

        tk.Label(config_frame, text="Server IP:Port", bg=self["bg"], fg=self.label_fg).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ip_entry = tk.Entry(config_frame, textvariable=self.server_ip, width=25)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ip_entry.insert(0, "") # Example IP

        self.toggle_button = tk.Button(config_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.toggle_button.grid(row=0, column=2, padx=10, pady=5)

        # User-inputted thresholds
        tk.Label(config_frame, text="CPU Threshold (%):", bg=self["bg"], fg=self.label_fg).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.cpu_threshold, width=8).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        tk.Label(config_frame, text="Memory Threshold (%):", bg=self["bg"], fg=self.label_fg).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.mem_threshold, width=8).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        tk.Label(config_frame, text="Load Threshold:", bg=self["bg"], fg=self.label_fg).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.load_threshold, width=8).grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # Live metrics display
        metrics_frame = tk.LabelFrame(main_frame, text="Live Metrics", bg=self["bg"], fg=self.label_fg, padx=10, pady=10)
        metrics_frame.pack(fill="both", expand=True)

        self.metric_labels = {}
        metrics = ["CPU Usage", "Memory Usage", "System Load", "Disk I/O", "Network I/O"]
        for i, metric in enumerate(metrics):
            tk.Label(metrics_frame, text=f"{metric}:", bg=self["bg"], fg=self.label_fg, font=self.label_font).grid(row=i, column=0, sticky="w", padx=5, pady=8)
            value_label = tk.Label(metrics_frame, text="--", bg=self.default_bg, fg=self.label_fg, font=self.label_font, width=25, anchor="w", padx=10)
            value_label.grid(row=i, column=1, sticky="ew", padx=5, pady=8)
            self.metric_labels[metric] = value_label

        metrics_frame.grid_columnconfigure(1, weight=1)

        # Status bar setup
        self.status_label = tk.Label(self, text="Ready. Enter server IP and start monitoring.", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#2E2E2E", fg=self.label_fg)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # Monitoring control function
    def toggle_monitoring(self):
        if self.monitoring:
            self.monitoring = False
            self.toggle_button.config(text="Start Monitoring")
            self.status_label.config(text="Monitoring stopped.")
        else:
            if not self.server_ip.get():
                self.status_label.config(text="Error: Please enter a server IP address.")
                return
            self.monitoring = True
            self.toggle_button.config(text="Stop Monitoring")
            self.status_label.config(text="Starting monitoring thread...")
            # Start the monitoring loop in a separate thread to not freeze the GUI
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()

    # Monitoring loop that pull data when monitoring is active
    def monitor_loop(self):
        while self.monitoring:
            try:
                url = f"http://{self.server_ip.get()}/metrics"
                response = requests.get(url, timeout=2.5)
                response.raise_for_status()
                data = response.json()
                self.after(0, self.update_ui, data) # Schedule UI update on main thread
            except requests.exceptions.RequestException as e:
                self.after(0, self.update_status, f"Connection Error: {e}")
            except Exception as e:
                self.after(0, self.update_status, f"An error occurred: {e}")

            time.sleep(3) # Poll every 3 seconds

    # UI update function
    def update_ui(self, data):
        if not self.monitoring: return

        # Update status
        self.status_label.config(text=f"Connected. Last update: {time.strftime('%H:%M:%S')}")

        # Update metric labels and check thresholds
        cpu = data.get('cpu_percent', 0)
        self.metric_labels["CPU Usage"].config(text=f"{cpu:.2f} %", bg=self.alert_bg if cpu > self.cpu_threshold.get() else self.default_bg)

        mem = data.get('memory_percent', 0)
        self.metric_labels["Memory Usage"].config(text=f"{mem:.2f} %", bg=self.alert_bg if mem > self.mem_threshold.get() else self.default_bg)

        load = data.get('load_avg', 0)
        self.metric_labels["System Load"].config(text=f"{load:.2f}", bg=self.alert_bg if load > self.load_threshold.get() else self.default_bg)

        disk_io = data.get('disk_io_bytes', 0) / 1024 # in KB
        self.metric_labels["Disk I/O"].config(text=f"{disk_io:.2f} KB/s")

        net_io = data.get('net_io_bytes', 0) / 1024 # in KB
        self.metric_labels["Network I/O"].config(text=f"{net_io:.2f} KB/s")

    # Check status of monitoring
    def update_status(self, message):
        self.status_label.config(text=message)

    # Setup the UI to close on exit properly
    def on_closing(self):
        self.monitoring = False
        self.destroy()

if __name__ == "__main__":
    app = PerformanceDashboard()
    app.mainloop()

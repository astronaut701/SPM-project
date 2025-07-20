import tkinter as tk
from tkinter import ttk, font, messagebox
import requests
import threading
import time

from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import math

# A single server tab
class ServerTab(tk.Frame):

    def __init__(self, parent, dashboard, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dashboard = dashboard # Reference the main window to deal with update_status scope being funky
        self.configure(bg="#2E2E2E")

        # Styling
        self.default_bg = "#3C3C3C"
        self.alert_bg = "#8B0000"
        self.label_fg = "#FFFFFF"
        self.label_font = font.Font(family="Helvetica", size=12)

        # User input monitoring varables
        self.server_ip = tk.StringVar()
        self.cpu_threshold = tk.DoubleVar(value=80.0)
        self.mem_threshold = tk.DoubleVar(value=80.0)
        self.load_threshold = tk.DoubleVar(value=2.0)
        self.update_interval = tk.IntVar(value=3)
        self.monitoring = False
        self.monitor_thread = None
        self.flash_job_id = None

        # Graph data
        self.max_data_points = 200  # A large buffer to hold data history
        self.cpu_data = deque([0] * self.max_data_points, maxlen=self.max_data_points)
        self.mem_data = deque([0] * self.max_data_points, maxlen=self.max_data_points)
        self.load_data = deque([0] * self.max_data_points, maxlen=self.max_data_points)
        self.disk_data = deque([0] * self.max_data_points, maxlen=self.max_data_points)
        self.net_data = deque([0] * self.max_data_points, maxlen=self.max_data_points)

        # Flashing alert (TODO: Make timer configurable? It's already kinda cramped in this space though.)
        self.alert_timers = {}
        self.flash_state = {}

        self.create_widgets()
        self.setup_graphs()

    # Create the data widgets (the user inputs, live data and graphs) for each server tab
    def create_widgets(self):
        # Main background frame to hold everything
        main_frame = tk.Frame(self, bg=self["bg"], padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # Foreground frame to hold GUI contents
        top_frame = tk.Frame(main_frame, bg=self["bg"])
        top_frame.pack(fill="x", pady=(0, 10), anchor="n")
        top_frame.grid_columnconfigure(1, weight=1)

        # User-input configuation frame
        config_frame = tk.LabelFrame(top_frame, text="Configuration", bg=self["bg"], fg=self.label_fg, padx=10, pady=10)
        config_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # User inputs and button to start monitoring
        tk.Label(config_frame, text="Server IP:Port", bg=self["bg"], fg=self.label_fg).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(config_frame, textvariable=self.server_ip, width=20).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(config_frame, text="Refresh Rate (s):", bg=self["bg"], fg=self.label_fg).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.update_interval, width=8).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        tk.Label(config_frame, text="CPU Threshold (%):", bg=self["bg"], fg=self.label_fg).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.cpu_threshold, width=8).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        tk.Label(config_frame, text="Memory Threshold (%):", bg=self["bg"], fg=self.label_fg).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.mem_threshold, width=8).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        tk.Label(config_frame, text="Load Threshold:", bg=self["bg"], fg=self.label_fg).grid(row=4, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(config_frame, textvariable=self.load_threshold, width=8).grid(row=4, column=1, sticky="w", padx=5, pady=2)
        self.toggle_button = tk.Button(config_frame, text="Start Monitoring", command=self.toggle_monitoring, width=20)
        self.toggle_button.grid(row=5, column=0, columnspan=2, padx=5, pady=10)

        # Live metrics frame
        metrics_frame = tk.LabelFrame(top_frame, text="Live Metrics", bg=self["bg"], fg=self.label_fg, padx=10, pady=10)
        metrics_frame.grid(row=0, column=1, sticky="nsew")

        # Live metrics display
        self.metric_labels = {}
        metrics = ["CPU Usage", "Memory Usage", "System Load", "Disk I/O", "Network I/O"]
        for i, metric in enumerate(metrics):
            tk.Label(metrics_frame, text=f"{metric}:", bg=self["bg"], fg=self.label_fg, font=self.label_font).grid(row=i, column=0, sticky="w", padx=5, pady=8)
            value_label = tk.Label(metrics_frame, text="--", bg=self.default_bg, fg=self.label_fg, font=self.label_font, width=20, anchor="w", padx=10)
            value_label.grid(row=i, column=1, sticky="ew", padx=5, pady=8)
            self.metric_labels[metric] = value_label
        metrics_frame.grid_columnconfigure(1, weight=1)

        # Metrics graph frame
        graph_outer_frame = tk.LabelFrame(main_frame, text="Metrics Graphs (Last 30 seconds)", bg=self["bg"], fg=self.label_fg, padx=10, pady=10)
        graph_outer_frame.pack(fill="both", expand=True, anchor="s")

        # Make the graph frame scrollable
        self.scrollable_canvas = tk.Canvas(graph_outer_frame, bg=self["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(graph_outer_frame, orient="vertical", command=self.scrollable_canvas.yview)
        self.scrollable_canvas.configure(yscrollcommand=scrollbar.set)

        # Scrollbar for frame
        scrollbar.pack(side="right", fill="y")
        self.scrollable_canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_inner_frame = tk.Frame(self.scrollable_canvas, bg=self["bg"])
        self.canvas_window = self.scrollable_canvas.create_window((0, 0), window=self.scrollable_inner_frame, anchor="nw")

        self.scrollable_inner_frame.bind("<Configure>", self.on_frame_configure)
        self.scrollable_canvas.bind("<Configure>", self.on_canvas_configure)

    # Automatic adjustment of the graph frame if it's resized
    def on_frame_configure(self, event):
        self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.scrollable_canvas.itemconfig(self.canvas_window, width=event.width)

    # Setup the graphs with matplotlib
    def setup_graphs(self):
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(8, 12), facecolor="#2E2E2E")
        self.fig.subplots_adjust(hspace=0.8, left=0.15, right=0.95, top=0.95, bottom=0.05)

        self.axes = self.fig.subplots(5, 1)
        self.ax_map = {
            "CPU Usage": self.axes[0], "Memory Usage": self.axes[1], "System Load": self.axes[2],
            "Disk I/O": self.axes[3], "Network I/O": self.axes[4],
        }

        # Basic graph layout
        for name, ax in self.ax_map.items():
            ax.set_title(name, fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.set_xticklabels([])
            ax.set_facecolor('#3C3C3C')

        # Add formatting for the Disk and Network I/O's units
        for ax_name in ["Disk I/O", "Network I/O"]:
            self.ax_map[ax_name].yaxis.set_major_formatter(FuncFormatter(self.format_bytes_ax))

        # Place the graphs in the scrollable graph frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.scrollable_inner_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_graphs()

    # Function to control the monitoring
    def toggle_monitoring(self):
        if self.monitoring:
            self.monitoring = False
            self.toggle_button.config(text="Start Monitoring")
            self.dashboard.update_status("Monitoring stopped.")
        else:
            server_ip_val = self.server_ip.get()
            if not server_ip_val:
                self.dashboard.update_status("Error: Please enter a server IP address.")
                return

            self.monitoring = True
            self.toggle_button.config(text="Stop Monitoring")
            self.dashboard.update_status(f"Starting monitoring for {server_ip_val}...")

            # Use a config dictionary to pass to the thread.
            # This prevents the thread from accessing Tkinter variables directly, preventing a lockup.
            config = {
                "ip": server_ip_val,
                "interval": self.update_interval.get()
            }
            self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(config,), daemon=True)

            self.monitor_thread.start()
            self.flash_alerting_labels()  # Start the loop to give a flashing alert

    # Loop that executes while monitoring is active, that pulls data from the API as often as set by the user
    def monitor_loop(self, config):
        server_ip = config["ip"]
        update_interval = config["interval"]

        while self.monitoring:
            try:
                response = requests.get(f"http://{server_ip}/metrics", timeout=2.5)
                response.raise_for_status()
                data = response.json()
                # Check again if monitoring was stopped while waiting for the request
                if self.monitoring:
                    self.after(0, self.update_ui, data)
            except requests.exceptions.RequestException as e:
                if self.monitoring:
                    self.after(0, lambda e=e: self.dashboard.update_status(f"Connection Error: {e}"))
                    self.after(10000, self.reset_metrics)
            except Exception as e:
                if self.monitoring:
                    self.after(0, lambda e=e: self.dashboard.update_status(f"An error occurred: {e}"))

            # Sleep for the user-defined interval
            time.sleep(update_interval)

    # Formatting of data units functions
    def format_bytes_ax(self, byte_count, pos=None):
        if byte_count is None: return "0 B"
        power = 1024
        n = 0
        power_labels = {0: 'B/s', 1: 'KB/s', 2: 'MB/s', 3: 'GB/s'}
        while byte_count >= power and n < len(power_labels) - 1:
            byte_count /= power
            n += 1
        return f"{byte_count:.1f} {power_labels[n]}"

    def format_bytes_label(self, byte_count):
        return self.format_bytes_ax(byte_count)

    # Function to prompt an update of the UI as new data is pulled.
    def update_ui(self, data):
        if not self.monitoring: return
        self.dashboard.update_status(f"Connected to {self.server_ip.get()}. Last update: {time.strftime('%H:%M:%S')}")

        metrics_to_check = {
            "CPU Usage": (data.get('cpu_percent', 0), self.cpu_threshold.get()),
            "Memory Usage": (data.get('memory_percent', 0), self.mem_threshold.get()),
            "System Load": (data.get('load_avg', 0), self.load_threshold.get())
        }

        for name, (value, threshold) in metrics_to_check.items():
            label = self.metric_labels[name]
            text_format = "{:.2f} %" if "Usage" in name else "{:.2f}"
            label.config(text=text_format.format(value))

            if value > threshold:
                if name not in self.alert_timers:
                    self.alert_timers[name] = time.time()
                    label.config(bg=self.alert_bg)
            else:
                if name in self.alert_timers:
                    del self.alert_timers[name]
                    if name in self.flash_state: del self.flash_state[name]
                    label.config(bg=self.default_bg)

        self.cpu_data.append(metrics_to_check["CPU Usage"][0])
        self.mem_data.append(metrics_to_check["Memory Usage"][0])
        self.load_data.append(metrics_to_check["System Load"][0])

        disk_io = data.get('disk_io_bytes', 0)
        self.metric_labels["Disk I/O"].config(text=self.format_bytes_label(disk_io))
        self.disk_data.append(disk_io)

        net_io = data.get('net_io_bytes', 0)
        self.metric_labels["Network I/O"].config(text=self.format_bytes_label(net_io))
        self.net_data.append(net_io)

        self.update_graphs()

    # Flash the live metric if it exceeds the threshold for several seconds
    def flash_alerting_labels(self):
        now = time.time()
        for name, start_time in list(self.alert_timers.items()):
            if now - start_time > 6: # Currently hardcoded. See TODO at line 41 about this issue.
                # Cycle between the colors
                current_color = self.flash_state.get(name, 'red')
                if self.monitoring == False:
                    break
                if current_color == 'red':
                    self.metric_labels[name].config(bg=self.default_bg)
                    self.flash_state[name] = 'default'
                else:
                    self.metric_labels[name].config(bg=self.alert_bg)
                    self.flash_state[name] = 'red'

        self.flash_job_id = self.after(500, self.flash_alerting_labels)

    def update_graphs(self):
        # Dynanically calculate points for the last 30 seconds
        try:
            interval = max(1, self.update_interval.get()) # Prevent division by zero, min interval of 1
        except tk.TclError:
            interval = 3 # Default if widget is destroyed

        points_to_show = math.ceil(30 / interval)
        points_to_show = max(2, points_to_show) # Ensure at least 2 points to draw a line

        # Sliced the data for plotting
        cpu_plot_data = list(self.cpu_data)[-points_to_show:]
        mem_plot_data = list(self.mem_data)[-points_to_show:]
        load_plot_data = list(self.load_data)[-points_to_show:]
        disk_plot_data = list(self.disk_data)[-points_to_show:]
        net_plot_data = list(self.net_data)[-points_to_show:]

        # CPU Usage Graph
        ax_cpu = self.ax_map["CPU Usage"]
        ax_cpu.clear()
        ax_cpu.plot(cpu_plot_data, color='cyan')
        ax_cpu.axhline(y=self.cpu_threshold.get(), color='orange', linestyle='--', linewidth=1)
        ax_cpu.set_ylim(0, 105)
        ax_cpu.set_title("CPU Usage (%)", fontsize=9)
        ax_cpu.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))

        # Memory Usage Graph
        ax_mem = self.ax_map["Memory Usage"]
        ax_mem.clear()
        ax_mem.plot(mem_plot_data, color='lime')
        ax_mem.axhline(y=self.mem_threshold.get(), color='orange', linestyle='--', linewidth=1)
        ax_mem.set_ylim(0, 105)
        ax_mem.set_title("Memory Usage (%)", fontsize=9)
        ax_mem.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))

        # System Load Graph
        ax_load = self.ax_map["System Load"]
        ax_load.clear()
        ax_load.plot(load_plot_data, color='magenta')
        ax_load.axhline(y=self.load_threshold.get(), color='orange', linestyle='--', linewidth=1)
        max_load = max(1.0, self.load_threshold.get() * 1.2, max(load_plot_data) * 1.1)
        ax_load.set_ylim(bottom=0, top=max_load)
        ax_load.set_title("System Load", fontsize=9)
        ax_load.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.2f}'))

        # Disk I/O Graph
        ax_disk = self.ax_map["Disk I/O"]
        ax_disk.clear()
        ax_disk.plot(disk_plot_data, color='yellow')
        max_disk_io = max(disk_plot_data) if any(disk_plot_data) else 0
        disk_ylim_top = max(1024, max_disk_io * 1.1)
        ax_disk.set_ylim(bottom=0, top=disk_ylim_top)
        ax_disk.set_title("Disk I/O", fontsize=9)
        ax_disk.yaxis.set_major_formatter(FuncFormatter(self.format_bytes_ax))

        # Network I/O Graph
        ax_net = self.ax_map["Network I/O"]
        ax_net.clear()
        ax_net.plot(net_plot_data, color='orange')
        max_net_io = max(net_plot_data) if any(net_plot_data) else 0
        net_ylim_top = max(1024, max_net_io * 1.1)
        ax_net.set_ylim(bottom=0, top=net_ylim_top)
        ax_net.set_title("Network I/O", fontsize=9)
        ax_net.yaxis.set_major_formatter(FuncFormatter(self.format_bytes_ax))

        for ax in self.ax_map.values():
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_xticklabels([])

        self.canvas.draw()

    # Function to reset the metrics whenever required
    def reset_metrics(self):
        self.alert_timers.clear()
        self.flash_state.clear()
        for key in self.metric_labels:
            self.metric_labels[key].config(text="--", bg=self.default_bg)

        self.cpu_data.extend([0]*self.max_data_points)
        self.mem_data.extend([0]*self.max_data_points)
        self.load_data.extend([0]*self.max_data_points)
        self.disk_data.extend([0]*self.max_data_points)
        self.net_data.extend([0]*self.max_data_points)
        self.update_graphs()

    # Convenience function to control monitoring status
    def stop_monitoring(self):
        self.monitoring = False
        if self.flash_job_id:
            self.after_cancel(self.flash_job_id)
            self.flash_job_id = None

# Seperate foreground class responsable for the window, server buttons/tabs, updating, and closing the program.
class PerformanceDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi-Server Performance Monitor")
        self.geometry("745x865")
        self.configure(bg="#2E2E2E")

        top_bar = tk.Frame(self, bg=self["bg"])
        top_bar.pack(side="top", fill="x", padx=10, pady=(5, 0))

        self.add_server_button = tk.Button(top_bar, text="➕ Add Server", command=self.add_server_tab)
        self.add_server_button.pack(side="left", padx=(0, 5))

        self.remove_server_button = tk.Button(top_bar, text="➖ Remove Server", command=self.remove_server_tab)
        self.remove_server_button.pack(side="left")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.status_label = tk.Label(self, text="Ready. Add a server tab to begin.", bd=1, relief=tk.SUNKEN, anchor="w", bg="#3C3C3C", fg="#FFFFFF")
        self.status_label.pack(side="bottom", fill="x")

        self.tabs = []

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_server_tab(self):
        tab_count = len(self.notebook.tabs()) + 1
        new_tab = ServerTab(self.notebook, dashboard=self)
        self.notebook.add(new_tab, text=f"Server {tab_count}")
        self.tabs.append(new_tab)
        self.notebook.select(new_tab)
        self.update_status(f"Added Server {tab_count}. Please configure and start monitoring.")
        self.update_tab_titles()

    def remove_server_tab(self):
        if not self.notebook.tabs():
            self.update_status("No servers to remove.")
            return

        try:
            # Get the widget and index of the currently selected tab
            selected_tab_widget = self.nametowidget(self.notebook.select())
            current_selection_index = self.notebook.index(self.notebook.select())
        except tk.TclError:
            self.update_status("No server tab selected to remove.")
            return

        ip_address = selected_tab_widget.server_ip.get() or "this server"
        question = f"Are you sure you want to remove the tab for {ip_address}?"

        if messagebox.askyesno("Confirm Removal", question, parent=self):
            # Bring the monitoring loop and any scheduled jobs to stop.
            selected_tab_widget.stop_monitoring()
            self.update_status(f"Stopping monitoring for {ip_address}...")

            # Remove the tab after a short delay with a helper function
            self.after(100, self._finalize_tab_removal, selected_tab_widget, current_selection_index, ip_address)

    # Helper function to perform the actual removal of everything
    def _finalize_tab_removal(self, tab_to_remove, tab_index, ip_address):
        # Forget the tab from the notebook, destroying its widgets
        self.notebook.forget(tab_to_remove)
        # Remove the tab object from the list of tabs
        self.tabs.pop(tab_index)

        self.update_status(f"Removed tab for {ip_address}.")
        self.update_tab_titles()

    def update_tab_titles(self):
        for i, tab in enumerate(self.tabs):
            self.notebook.tab(tab, text=f"Server {i + 1}")

    def update_status(self, message):
        self.status_label.config(text=message)

    def on_closing(self):
        for tab in self.tabs:
            tab.stop_monitoring()
        plt.close('all')
        self.destroy()

if __name__ == "__main__":
    app = PerformanceDashboard()
    app.mainloop()

import psutil
import json
import time
import os
import atexit

# Define pipe and define usage of psutil
PIPE_PATH = '/tmp/metrics_pipe'
last_disk_io = psutil.disk_io_counters()
last_net_io = psutil.net_io_counters()

# Function to clean up pipe on exit
def cleanup():
    # Remove the pipe on exit.
    print("Collector shutting down. Cleaning up pipe.")
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)

# Setup the cleanup to fire when the program exits
atexit.register(cleanup)

# Create the named pipe if it doesn't exist
if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)
    # Set permissions to be world-writable
    os.chmod(PIPE_PATH, 0o666)

# Log the start of the collector
print(f"Collector started. Writing to pipe: {PIPE_PATH}")

# Run the collection of metrics
while True:
    try:
        # 1. CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # 2. Memory Usage
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent

        # 3. Disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_io_bytes = (current_disk_io.read_bytes - last_disk_io.read_bytes) + \
                        (current_disk_io.write_bytes - last_disk_io.write_bytes)
        last_disk_io = current_disk_io

        # 4. Network I/O
        current_net_io = psutil.net_io_counters()
        net_io_bytes = (current_net_io.bytes_sent - last_net_io.bytes_sent) + \
                       (current_net_io.bytes_recv - last_net_io.bytes_recv)
        last_net_io = current_net_io
        # 5. System Load Average
        load_avg = psutil.getloadavg()[0] # 1-minute average

        # Format the data for flask
        metrics = {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_io_bytes': disk_io_bytes,
            'net_io_bytes': net_io_bytes,
            'load_avg': load_avg
        }
        # Convert to JSON
        metrics_json = json.dumps(metrics) + '\n' # Add newline as delimiter

        # Open the pipe, in non-blocking write mode to avoid waiting for it to be read
        with open(PIPE_PATH, 'w') as pipe:
            pipe.write(metrics_json)

    # Account for exceptions in the program
    except Exception as e:
        print(f"An error occurred in the collector: {e}")
        time.sleep(5) # Wait before retrying

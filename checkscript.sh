#!/bin/bash

# Pathes to the scripts
AGENT_SCRIPT_PATH="/opt/monitor/agent.py"
COLLECTOR_SCRIPT_PATH="/opt/monitor/collector.py"
# The user to run the agent as
RUN_AS_USER="monitor"

# Check if the process is running
if ! pgrep -f -u "$RUN_AS_USER" "$AGENT_SCRIPT_PATH" > /dev/null; then
    echo "Agent process not found. Restarting..."
    # Use sudo to run the command as the specified user
    # The 'nohup' and '&' ensure the script runs in the background
    # and continues running after this script exits.
    # Redirect output to a log file.
    sudo -u "$RUN_AS_USER" nohup python3 "$AGENT_SCRIPT_PATH" > /opt/monitor/agent.log 2>&1 &
else
    echo "Agent is running."
fi

# Check if the process is running
if ! pgrep -f -u "$RUN_AS_USER" "$COLLECTOR_SCRIPT_PATH" > /dev/null; then
    echo "Collector process not found. Restarting..."
    sudo -u "$RUN_AS_USER" nohup python3 "$COLLECTOR_SCRIPT_PATH" > /opt/monitor/collector.log 2>&1 &
else
    echo "Collector is running."
fi

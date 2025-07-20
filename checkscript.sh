#!/bin/bash

# Path to the agent script
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
    su - "$RUN_AS_USER" -s /bin/bash -c \ "exec /usr/bin/nohup python3 $AGENT_SCRIPT_PATH > /opt/monitor/agent.log 2>&1 < /dev/null &"
else
    echo "Agent is running."
fi

if ! pgrep -f -u "$RUN_AS_USER" "$COLLECTOR_SCRIPT_PATH" > /dev/null; then
    echo "Collector process not found. Restarting..."
    su - "$RUN_AS_USER" -s /bin/bash -c \ "exec /usr/bin/nohup python3 $COLLECTOR_SCRIPT_PATH > /opt/monitor/collector.log 2>&1 < /dev/null &"
else
    echo "Collector is running."
fi

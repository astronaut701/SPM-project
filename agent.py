from flask import Flask, jsonify
import json

# Setup flash server and define pipe
app = Flask(__name__)
PIPE_PATH = '/tmp/metrics_pipe'

# Define where the metrics are
@app.route('/metrics', methods=['GET'])
def get_metrics():
    try:
        # Open the pipe.
        with open(PIPE_PATH, 'r') as pipe:
            # Read all available lines and take the last one. This ensures we get the most recent data if the client polls slowly.
            lines = pipe.readlines()
            if not lines:
                return jsonify({"error": "No data available from collector"}), 503
            latest_line = lines[-1].strip()
            data = json.loads(latest_line)
            return jsonify(data)
    # Account for a missing pipe or an exception being thrown.
    except FileNotFoundError:
        return jsonify({"error": f"Metrics pipe not found at {PIPE_PATH}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This isn't exactly safe for production, for this project, it'll do.
    app.run(host='0.0.0.0', port=5050)

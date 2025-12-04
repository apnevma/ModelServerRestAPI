from flask import Flask, request, jsonify, Response, render_template
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
from flask_cors import cross_origin
import os
import signal, sys
import json
from threading import Thread

# Local imports
import model_detector, tf_serving_manager

API_HOST = os.getenv("API_HOST", "localhost")
PORT = int(os.getenv("PORT", "8086"))

app = Flask(__name__)

# Define the folder to monitor (with fallback if docker environment variable is not set)
folder_to_monitor = os.environ.get("MODELS_PATH", "./models")
print("folder_to_monitor:", folder_to_monitor)
print("folder_to_monitor contents:", os.listdir(folder_to_monitor))

# Dictionary to store endpoints for each file
endpoints = {}
# Store extra metadata for help endpoint
models_info = {}


def initialize_endpoints():
    # Loop through each file in the folder
    for filename in os.listdir(folder_to_monitor):
        file_path = os.path.join(folder_to_monitor, filename)

        print(f"file_path for filename {filename}:", file_path)

        create_endpoint(file_path)

    # Print models in models_info
    print("=== Registered Endpoints ===")
    for endpoint in models_info:
        print(endpoint)
    # Print Flask URL rules
    print("=== Flask URL Rules ===")
    for rule in app.url_map.iter_rules():
        print(rule, "->", app.view_functions[rule.endpoint])


class MyHandler(FileSystemEventHandler):
    
    def __init__(self):
        super().__init__()
        # Keep track of models currently registered
        self.registered_models = set(os.listdir(folder_to_monitor))

    def on_any_event(self, event):
        # Ignore the root folder itself
        if os.path.abspath(event.src_path) == os.path.abspath(folder_to_monitor):
            self.resync_models()
        else:
            # Any event inside the folder triggers a resync
            self.resync_models()

    def resync_models(self):
        current_models = set(os.listdir(folder_to_monitor))
        previous_models = self.registered_models

        # Detect added models
        for model in current_models - previous_models:
            path = os.path.join(folder_to_monitor, model)
            print(f"[WATCHDOG][CREATED] {path}")
            create_endpoint(path)

        # Detect removed models
        for model in previous_models - current_models:
            path = os.path.join(folder_to_monitor, model)
            print(f"[WATCHDOG][DELETED] {path}")
            delete_endpoint(path)

        # Update the registered models set
        self.registered_models = current_models



def create_endpoint(file_path):
    """
    Registers a model in the internal registry.
    """
    endpoint_path = os.path.relpath(file_path, folder_to_monitor)
    filename, extension = os.path.splitext(endpoint_path)
    endpoint = filename.replace(os.path.sep, '/')  # just store name, no leading /

    model_info, model = model_detector.detect(os.path.join(folder_to_monitor, endpoint_path))

    if model is not None:
        print(f"[+] Model detected: {filename}")
        # Store everything needed for dynamic prediction
        models_info[endpoint] = {
            "model_name": filename,
            "model_path": os.path.join(folder_to_monitor, endpoint_path),
            "model": model,
            "model_info": model_info
        }
        print(f"[+] Registered '{endpoint}' for dynamic prediction")
    else:
        print(f"[!] Extension not supported: {extension}")


def delete_endpoint(file_path):
    """
    Remove a model from the internal registry and Flask endpoints.
    """
    endpoint_path = os.path.relpath(file_path, folder_to_monitor)
    filename, _ = os.path.splitext(endpoint_path)
    endpoint = filename.replace(os.path.sep, '/')

    # Remove from models_info
    if endpoint in models_info:
        models_info.pop(endpoint)
        print(f"[-] Removed '{endpoint}' from registry")
    else:
        print(f"[!] Model '{endpoint}' not found in registry")    


@app.route("/predict/<model_name>", methods=["POST"])
def dynamic_predict(model_name):
    if model_name not in models_info:
        return jsonify({"error": f"Model '{model_name}' not found"}), 404

    model_entry = models_info[model_name]
    features = request.get_json().get("input")

    try:
        result = model_detector.predict(
            model_entry["model_path"],
            model_entry["model"],
            features
        )

        # If TF Serving, unwrap the 'predictions' key
        if isinstance(result, dict) and "predictions" in result:
            return jsonify({"prediction": result["predictions"]})
        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({
            "error": str(e),
            "expected_input": model_entry["model_info"]
        })


@app.route('/test')
def test_endpoint():
    return 'The Model Server is ALIVE!'

# Help endpoint to provide info for all the available models
@app.route('/help')
def help_endpoint():
    if not models_info:
        return jsonify({"message": "No models currently loaded."})
    
    response_data = {
        "message": (
            "Below are all the available models loaded from the models/ folder. "
            "To add new models, simply drop them into that folder and the system "
            "will automatically detect and expose them via the dynamic /predict/<model_name> endpoint."
        ),
        "available_models": [
            {
                "model_name": info["model_name"],
                "endpoint_url": f"http://{API_HOST}:{PORT}/predict/{info['model_name']}",
                "model_info": info["model_info"]
            }
            for info in models_info.values()
        ]
    }

    # Pretty-print in JSON
    return Response(
        json.dumps(response_data, indent=4),
        content_type="application/json"
    )


# Web-based UI for help
@app.route('/help/ui')
def help_ui():
    models = [
        {
            "model_name": info["model_name"],
            "endpoint_url": f"/predict/{info['model_name']}",
            "model_info": info["model_info"]
        }
        for info in models_info.values()
    ]
    return render_template('help.html', models=models)


def start_monitoring():
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder_to_monitor, recursive=True)
    observer_thread = Thread(target=observer.start, daemon=True)
    observer_thread.start()
    print(f"[WATCHDOG] Monitoring '{folder_to_monitor}' for model changes...")


def cleanup(signum, frame):
    print("Stopping all TF Serving containers...")
    for c in tf_serving_manager.list_managed_containers():
        try:
            print(f"Stopping {c.name}...")
            c.remove(force=True)
        except Exception as e:
            print(f"Failed to stop {c.name}: {e}")
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


if __name__ == '__main__':
    initialize_endpoints()
    start_monitoring()       # Start the watchdog in the background

    app.run(host='0.0.0.0', port=PORT)

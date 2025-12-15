from flask import Flask, request, jsonify, Response, render_template
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
import os
import signal, sys
import json
from threading import Thread

# Local imports
import model_detector, tf_serving_manager
from github_client import list_github_models

API_HOST = os.getenv("API_HOST", "localhost")
PORT = int(os.getenv("PORT", "8086"))
MODEL_SOURCE = os.getenv("MODEL_SOURCE", "local")  # "local" or "github"

app = Flask(__name__)

# Define the folder to monitor (with fallback if docker environment variable is not set)
folder_to_monitor = os.environ.get("MODELS_PATH", "./models")
print("folder_to_monitor:", folder_to_monitor)
print("folder_to_monitor contents:", os.listdir(folder_to_monitor))

# Dictionary to store endpoints for each file
endpoints = {}
# All detected models (from filesystem)
available_models = {}   # model_name -> {model_path}
# Only active models get loaded and registered here
active_models = {}   # model_name -> {model, model_info, model_path}


def initialize_models():
    available_models.clear()
    if MODEL_SOURCE == "github":
        try:
            github_entries = list_github_models()
            for entry in github_entries.values():
                name = entry["model_name"]
                # keep the github metadata so we can download later
                available_models[name] = entry
            print("[INIT] loaded models from Github:", list(available_models.keys()))
        except Exception as e:
            print("[INIT][ERROR] failed to list Github models:", e)
    else:
        # local filesystem
        for filename in os.listdir(folder_to_monitor):
            file_path = os.path.join(folder_to_monitor, filename)
            if os.path.isdir(file_path) or os.path.isfile(file_path):
                model_name = filename
                available_models[model_name] = {
                    "source": "local",
                    "model_name": model_name,
                    "model_path": file_path
                }
        print("[INIT] loaded local models:", list(available_models.keys()))        


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
            self.add_model(model, path)

        # Detect removed models
        for model in previous_models - current_models:
            path = os.path.join(folder_to_monitor, model)
            print(f"[WATCHDOG][DELETED] {path}")
            self.remove_model(model)

        # Update the registered models set
        self.registered_models = current_models

    def add_model(self, model, path):
        model_name = os.path.splitext(model)[0]
        available_models[model_name] = {
            "model_name": model_name,
            "model_path": path
        }
        print(f"[+] Added '{model_name}' to available_models.")

    def remove_model(self, model):
        model_name = os.path.splitext(model)[0]

        if model_name in active_models:
            print(f"[!] Removing active model '{model_name}' from disk → auto-deactivate...")
            try:
                tf_serving_manager.stop_container(model_name)
            except:
                pass
            del active_models[model_name]

        if model_name in available_models:
            del available_models[model_name]

        print(f"[-] Removed '{model_name}' from available_models.")



# Get model status (active/not_active)
@app.route('/status/<model_name>')
def model_status(model_name):
    if model_name not in available_models:
        return jsonify({"error": "Model not found"}), 404
    
    is_active = model_name in active_models
    return jsonify({
        "model_name": model_name,
        "active": is_active
    })


# Activate available model
@app.route('/activate/<model_name>', methods=['POST'])
def activate_model(model_name):
    if model_name not in available_models:
        return jsonify({"error": "Model not found"}), 404

    # Already active?
    if model_name in active_models:
        return jsonify({"message": "Model already active"})

    model_path = available_models[model_name]["model_path"]
    model_info, model = model_detector.detect(model_path)

    if model is None:
        return jsonify({"error": "Unsupported or invalid model"}), 400

    active_models[model_name] = {
        "model_name": model_name,
        "model": model,
        "model_info": model_info,
        "model_path": model_path
    }

    return jsonify({
        "message": f"Model {model_name} activated",
        "predict_endpoint": f"/predict/{model_name}"
    })

# Deactivate model
@app.route('/deactivate/<model_name>', methods=['POST'])
def deactivate_model(model_name):
    if model_name not in active_models:
        return jsonify({"message": "Model already inactive"})

    # Stop TF container (if used)
    try:
        tf_serving_manager.stop_container(model_name)
    except:
        pass

    del active_models[model_name]

    return jsonify({"message": f"Model {model_name} deactivated"})


# Endpoint for predictions
@app.route("/predict/<model_name>", methods=["POST"])
def dynamic_predict(model_name):
    if model_name not in active_models:
        return jsonify({"error": f"Model '{model_name}' not found"}), 404

    model_entry = active_models[model_name]
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

# List all available models
@app.route('/models', methods=['GET'])
def list_models():
    output = []

    for model_name, entry in available_models.items():
        is_active = model_name in active_models

        output.append({
            "model_name": model_name,
            "status": "active" if is_active else "inactive",
            "repo_path": entry["repo_path"],
            "predict_url": (
                f"http://{API_HOST}:{PORT}/predict/{model_name}"
                if is_active else None
            )
        })

    return jsonify(output)

# list raw github entries
@app.route('/models/github', methods=['GET'])
def models_github():
    try:
        return jsonify(list_github_models())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Help endpoint to provide info for all the active models
@app.route('/help')
def help_endpoint():
    if not active_models:
        return jsonify({"message": "No models currently loaded."})
    
    response_data = {
        "message": (
            "Below are all the active models loaded from the models/ folder. "
            "To add new models, simply drop them into that folder and the system "
            "will automatically detect and expose them via the dynamic /predict/<model_name> endpoint."
        ),
        "active_models": [
            {
                "model_name": info["model_name"],
                "endpoint_url": f"http://{API_HOST}:{PORT}/predict/{info['model_name']}",
                "model_info": info["model_info"]
            }
            for info in active_models.values()
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
        for info in active_models.values()
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
    initialize_models()
    start_monitoring()       # Start the watchdog in the background

    app.run(host='0.0.0.0', port=PORT)

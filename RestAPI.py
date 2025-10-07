from flask import Flask, request, jsonify, Response
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask_cors import cross_origin
import os
import signal, sys
import json

# Local imports
import model_detector, tf_serving_manager

PORT = 8086

app = Flask(__name__)

# Define the folder to monitor (with fallback if docker environment variable is not set)
folder_to_monitor = os.environ.get("MODELS_PATH", "./models")
print("folder_to_monitor:", folder_to_monitor)
print("folder_to_monitor contents:", os.listdir(folder_to_monitor))

# Dictionary to store endpoints for each file
endpoints = {}
# Store extra metadata for help endpoint
models_info = {}

model_types = {'type1': 'h5', 'type2': 'pkl', 'type3': 'joblib', 'type4': 'pt', 'type5': 'params'}


def initialize_endpoints():
    # Loop through each file in the folder
    for filename in os.listdir(folder_to_monitor):
        file_path = os.path.join(folder_to_monitor, filename)

        print(f"file_path for filename {filename}:", file_path)

        create_endpoint(file_path)

    # Print endpoints
    print("=== Registered Endpoints ===")
    for ep, func in endpoints.items():
        print(ep, "->", func)
    # Print Flask URL rules
    print("=== Flask URL Rules ===")
    for rule in app.url_map.iter_rules():
        print(rule, "->", app.view_functions[rule.endpoint])



class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.event_type != 'created':
            return

        file_path = event.src_path

        # Ignore subdirectories inside a model folder -> only the root folder gets passed inside create_endpoint
        rel_path = os.path.relpath(file_path, folder_to_monitor)
        parts = rel_path.split(os.sep)
        if len(parts) > 1:  # "fire_nn/1" → ignore
            return

        create_endpoint(file_path)


def create_endpoint(file_path):
    endpoint_path = os.path.relpath(file_path, folder_to_monitor)
    filename, extension = os.path.splitext(endpoint_path)
    endpoint = '/' + filename.replace(os.path.sep, '/')


    model_info, model = model_detector.detect(os.path.join(folder_to_monitor, endpoint_path))

    if model is not None:
        print("Model info for", filename + ":", model_info)

        # Store model metadata for /help
        models_info[endpoint] = {
            "model_name": filename,
            "endpoint": endpoint,
            "model_info": model_info
        }

        def predict():
            data = request.get_json()
            features = data["input"]

            try:
                print("What I pass in model_detector.predict():", os.path.join(folder_to_monitor, endpoint_path))
                result = model_detector.predict(os.path.join(folder_to_monitor, endpoint_path), model, features)

                # If TF Serving, unwrap the 'predictions' key
                if isinstance(result, dict) and "predictions" in result:
                    return jsonify({"prediction": result["predictions"]})
                return jsonify({"prediction": result})
            
            except Exception as e:
                return jsonify({
                    "error": str(e),
                    "expected_input": model_info
                })

        app.add_url_rule(
            endpoint,                      # URL path (e.g., /fire_nn)
            endpoint,                      # unique endpoint name
            cross_origin()(predict),       # enable CORS
            methods=['POST']
        )

        endpoints[endpoint] = predict
        print("Created endpoint " + endpoint)

    else:
        print(extension + " extension not supported!")


@app.route('/test')
def test_endpoint():
    return 'The Model Server is ALIVE!'


@app.route('/help')
def help_endpoint():
    if not models_info:
        return jsonify({"message": "No models currently loaded."})
    
    response_data = {
        "message": (
            "Below are all the available models loaded from the models/ folder. "
            "To add new models, simply drop them into that folder and the system "
            "will automatically detect and expose them."
        ),
        "available_models": list(models_info.values())
    }

    # Pretty-print in JSON
    return Response(
        json.dumps(response_data, indent=4),
        content_type="application/json"
    )


def start_monitoring():
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder_to_monitor, recursive=True)
    observer.start()

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
    start_monitoring()
    # Run the Flask app on port
    app.run(host='0.0.0.0', port=PORT)

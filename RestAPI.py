from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask_cors import cross_origin
import os

# Local imports
import model_detector

PORT = 8086

app = Flask(__name__)

# Define the folder to monitor
folder_to_monitor = "./models/"

# Dictionary to store endpoints for each file
endpoints = {}

model_types = {'type1': 'h5', 'type2': 'pkl', 'type3': 'joblib', 'type4': 'pt', 'type5': 'params'}


def initialize_endpoints():
    # Loop through each file in the folder
    for filename in os.listdir(folder_to_monitor):
        file_path = os.path.join(folder_to_monitor, filename)

        # Check if it's a file (not a subdirectory)
        if os.path.isfile(file_path):
            # Define a dynamic route for the endpoint
            create_endpoint(file_path)


class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        elif event.event_type == 'created':
            file_path = event.src_path
            create_endpoint(file_path)


def create_endpoint(file_path):
    endpoint_path = os.path.relpath(file_path, folder_to_monitor)
    filename, extension = os.path.splitext(endpoint_path)
    endpoint = '/' + filename.replace(os.path.sep, '/')
    model = model_detector.detect(folder_to_monitor + endpoint_path)

    # Define a dynamic route for the endpoint
    if model is not None:
        @app.route(endpoint, methods=['POST'])
        @cross_origin()
        def dynamic_endpoint():
            data = request.get_json()

            # Process the data (example: echoing back the received data)
            result = {"received_data": data}
            result = model_detector.predict(folder_to_monitor + endpoint_path,model,data)

            # Return the result as JSON
            return jsonify(result)

            # Add the endpoint to the dictionary for future reference
        endpoints[endpoint] = dynamic_endpoint
        print("Created endpoint " + endpoint)
    else:
        print(extension + " extension not supported!")


@app.route('/test')
def test_endpoint():
    return 'The Model Server is ALIVE!'


def start_monitoring():
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder_to_monitor, recursive=True)
    observer.start()


if __name__ == '__main__':
    initialize_endpoints()
    start_monitoring()
    # Run the Flask app on port
    app.run(host='0.0.0.0', port=PORT)

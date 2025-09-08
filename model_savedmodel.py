import os
import requests
from utils import find_latest_saved_model_folder

def load_savedmodel(model_folder):
    # Ensure there's at least one version folder with saved_model.pb
    latest_folder = find_latest_saved_model_folder(model_folder)
    if latest_folder is None:
        raise ValueError(f"No valid SavedModel found inside {model_folder}")

    model_name = os.path.basename(model_folder.rstrip("/\\"))
    serving_url = f"http://localhost:8501/v1/models/{model_name}:predict"

    info = {
        "type": "TensorFlow (TF Serving)",
        "model_name": model_name,
        "serving_url": serving_url,
        "note": "Input/output info not introspected yet — query TF Serving metadata or keep a metadata.json."
    }

    return info, serving_url


def predict_savedmodel(serving_url, input_data):
    payload = {"instances": [input_data]}
    try:
        response = requests.post(serving_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
import os
import requests
from tf_serving_manager import ensure_container
from utils import find_latest_saved_model_folder, wait_until_stable, transform_to_friendly_inputs
from flask import jsonify

def load_savedmodel(model_folder):
    # Wait until file is fully written before loading
    if wait_until_stable(model_folder):
        print(f"Folder {model_folder} is stable, loading SavedModel folder...")
    else:
        print(f"Folder {model_folder} did not stabilize in time, skipping.")
        return

    # Ensure there's at least one version folder with saved_model.pb
    latest_folder = find_latest_saved_model_folder(model_folder)
    if latest_folder is None:
        raise ValueError(f"No valid SavedModel found inside {model_folder}")

    model_name = os.path.basename(model_folder.rstrip("/\\"))
    # model_abs = os.path.abspath(model_folder)
    model_abs = os.path.abspath(f"./models/{model_name}")
    
    info = ensure_container(model_name, model_abs)  # starts/returns container
    model_info = {
        "type": "TensorFlow (TF Serving, per-model container)",
        "model_name": model_name,
        "serving_url": info["serving_url"],
        "status_url": info["status_url"],
        "host_port": info["host_port"],
        "note": "I/O schema not introspected; use metadata"
    }
    return model_info, info["serving_url"]
    

def predict_savedmodel(serving_url, input_data):
    # If input_data comes from Flask {"input": [...]}, extract the array
    if isinstance(input_data, dict) and "input" in input_data:
        instances = input_data["input"]
    else:
        instances = input_data  # fallback

    payload = {"instances": instances}
    
    try:
        response = requests.post(serving_url, json=payload)
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException as e:
        # Derive metadata URL
        metadata_url = serving_url.replace(":predict", "") + "/metadata"
        try:
            meta_resp = requests.get(metadata_url)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()
            
            # Transform metadata to a friendlier, user-readable schema
            friendly_inputs = transform_to_friendly_inputs(metadata)
                
        except Exception as meta_err:
            friendly_inputs = {"error": f"Failed to fetch metadata: {meta_err}"}

        return {
            "error": str(e),
            "expected_input": friendly_inputs
        }
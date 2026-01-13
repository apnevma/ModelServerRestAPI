import os
import requests
import tensorflow as tf
from tf_serving_manager import ensure_container
from utils import find_latest_saved_model_folder, wait_until_stable, transform_to_friendly_inputs


def load_savedmodel(model_folder, version):
    print("model_folder:", model_folder)
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

    # Use the folder name as the model name
    model_name = os.path.basename(model_folder.rstrip("/\\"))

    # pass model subdir
    model_subdir = model_name
    print("model_subdir:", model_subdir)

    info = ensure_container(model_name, model_subdir)

    try:
        loaded = tf.saved_model.load(f"{model_folder}/{version}")
        signatures = list(loaded.signatures.keys())
        signature = loaded.signatures["serving_default"]

        input_info = {k: str(v) for k, v in signature.structured_input_signature[1].items()}
        output_info = {k: str(v) for k, v in signature.structured_outputs.items()}

    except Exception as e:
        print("ERROR getting model_info:", str(e))
        return {"error": str(e)}    
    
    model_info = {
        "type": "TensorFlow SavedModel",
        "model_name": model_name,
        "signatures": signatures,
        "inputs": input_info,
        "outputs": output_info
    }

    return model_info, info["serving_url"]
    

def predict_savedmodel(serving_url, input_data):
    if isinstance(input_data, dict) and "input" in input_data:
        instances = input_data["input"]
    else:
        instances = input_data

    payload = {"instances": instances}

    try:
        response = requests.post(serving_url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()

        # Defensive check: TF Serving sometimes returns 200 with an error body
        if "error" in result:
            raise RuntimeError(result["error"])

        return result

    except Exception as e:
        # Try to enrich the error with model metadata
        metadata_url = serving_url.replace(":predict", "") + "/metadata"

        try:
            meta_resp = requests.get(metadata_url, timeout=5)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()
            friendly_inputs = transform_to_friendly_inputs(metadata)

        except Exception as meta_err:
            friendly_inputs = {
                "error": f"Failed to fetch metadata: {meta_err}"
            }

        # Raise Error, do NOT return
        raise RuntimeError(
            {
                "tf_serving_error": str(e)
            }
        )
    
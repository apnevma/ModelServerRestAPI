import numpy as np
import torch
import os
import time


def make_json_serializable(obj):
    """
    Recursively convert objects to JSON-serializable types.
    - NumPy int/float → Python int/float
    - NumPy arrays → lists
    - PyTorch tensors → lists
    """
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, torch.Tensor):
        return obj.tolist()
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    else:
        return obj  # assume already serializable



def wait_until_stable(path, timeout=10, interval=0.5):
    """
    Wait until a file or directory stops changing in size.
    Returns True if stable, False if timeout.
    """
    prev_size = -1
    start = time.time()

    while time.time() - start < timeout:
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
            elif os.path.isdir(path):
                # Sum of sizes of all files inside the directory
                size = sum(
                    os.path.getsize(os.path.join(root, f))
                    for root, _, files in os.walk(path)
                    for f in files
                    if os.path.isfile(os.path.join(root, f))
                )
            else:
                size = -1
        except OSError:
            size = -1

        if size == prev_size and size > 0:
            return True
        prev_size = size
        time.sleep(interval)

    return False



def find_latest_saved_model_folder(model_root_folder):
    """
    Automatically finds the latest version folder containing a saved_model.pb file.
    
    Args:
        model_root_folder (str): Path to the model folder (e.g., 'models/my_model')
    
    Returns:
        str or None: Path to the latest version folder containing saved_model.pb, or None if not found
    """
    if not os.path.isdir(model_root_folder):
        return None

    # List all subfolders (versions)
    subfolders = [f for f in os.listdir(model_root_folder) if os.path.isdir(os.path.join(model_root_folder, f))]

    # Filter only numeric version folders
    version_folders = []
    for folder in subfolders:
        try:
            version_number = int(folder)
            version_folders.append((version_number, folder))
        except ValueError:
            continue  # skip non-numeric folders

    if not version_folders:
        return None

    # Pick the folder with the highest version number
    latest_version_folder = max(version_folders, key=lambda x: x[0])[1]
    latest_version_path = os.path.join(model_root_folder, latest_version_folder)

    # Check if it contains saved_model.pb
    if "saved_model.pb" in os.listdir(latest_version_path):
        return latest_version_path
    else:
        return None



# Transform metadata to a friendlier, user-readable schema
def transform_to_friendly_inputs(metadata):

    # Extract only input names, shapes, and dtypes
    sig_def = metadata.get("metadata", {}).get("signature_def", {}).get("signature_def", {})
    serving_default = sig_def.get("serving_default", {})
    inputs = serving_default.get("inputs", {})
            
    friendly_inputs = {}
    for name, tensor_info in inputs.items():
        shape = [int(dim.get("size", -1)) for dim in tensor_info.get("tensor_shape", {}).get("dim", [])]
        dtype = tensor_info.get("dtype", "unknown")

        # Turn -1 into "batch_size"
        shape_str = ["batch_size" if dim == -1 else str(dim) for dim in shape]
        shape_str = f"[{', '.join(shape_str)}]"   

        friendly_inputs[name] = {
            "dtype": dtype.lower().replace("dt_", ""),  # e.g. "DT_FLOAT" -> "float"
            "shape": shape_str,
        }

    return friendly_inputs


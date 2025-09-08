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



# Wait until a new file stabilizes
def wait_until_stable(filepath, timeout=10, interval=0.5):
    prev_size = -1
    start = time.time()
    while time.time() - start < timeout:
        try:
            size = os.path.getsize(filepath)
        except OSError:
            size = -1
        if size == prev_size and size > 0:
            return True
        prev_size = size
        time.sleep(interval)
    return False
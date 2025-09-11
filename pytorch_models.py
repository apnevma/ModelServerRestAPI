import importlib.util
import sys
import torch
from pathlib import Path
from flask import jsonify
from utils import wait_until_stable


def load_pytorch_file(model_path):
    # Wait until file is fully written before loading
    if wait_until_stable(model_path):
        print(f"File {model_path} is stable, loading model...")
        model = torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)
        model.eval()
        info = get_pytorch_model_info(model)
        return info, model
    else:
        print(f"File {model_path} did not stabilize in time, skipping.")
        return None, None


def load_pytorch_folder(folder):
    folder = Path(folder)
    model_file = folder / "model.pt"
    class_file = folder / "model_class.py"

    # --- Dynamically import module ---
    spec = importlib.util.spec_from_file_location("model_class", class_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["model_class"] = module
    spec.loader.exec_module(module)

    # --- Find the first nn.Module subclass dynamically ---
    import torch.nn as nn
    ModelClass = None
    for name, obj in vars(module).items():
        if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
            ModelClass = obj
            break

    if ModelClass is None:
        raise ValueError("No nn.Module subclass found in model_class.py")

    # --- Instantiate + load weights ---
    model = ModelClass()
    state_dict = torch.load(model_file, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    info = get_pytorch_model_info(model)

    # --- Info extraction (input/output shapes if possible) ---
    info = get_pytorch_model_info(model)

    return info, model

# model.pt has to be state_dict
def get_pytorch_model_info(model):
    try:
        example_input = torch.randn(1, *list(model.parameters())[0].shape[1:])
        traced = torch.jit.trace(model, example_input)
        input_shape = tuple(example_input.shape)
        output_shape = tuple(traced(example_input).shape)
        input_type = str(example_input.dtype)
    except Exception as e:
        print(f"Could not infer model info: {e}")
        input_shape = "unknown"
        output_shape = "unknown"
        input_type = "unknown"

    return {
        "type": "PyTorch",
        "input_shape": input_shape,
        "input_type": input_type,
        "output_shape": output_shape,
    }



def predict_pytorch(model, input_data):
    # Convert input data to tensor
    tensor_input = torch.tensor([input_data], dtype=torch.float32)

    # Perform prediction
    with torch.no_grad():
        output = model(tensor_input)

    # Convert predictions to JSON
    response = {"predictions": output.tolist()}
    return response
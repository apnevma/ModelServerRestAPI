from flask import jsonify
import mxnet as mx
import os

def check_json_exists(path,filename):
    params_file = os.path.join(path, f"{filename}.params")
    json_file = os.path.join(path, f"{filename}.json")

    if os.path.exists(params_file) and os.path.exists(json_file):
        return True

    return False

def load_params(filename):
    directory, filename_with_extension = os.path.split(filename)
    filename, extension = os.path.splitext(filename_with_extension)
    if not check_json_exists(directory,filename):
        print("Respective .json file not found in folder")
        return None

    # Load the MXNet model and bind it to a context
    model = mx.gluon.SymbolBlock.imports(directory, f"{filename}.json", ['data'], filename, ctx=mx.cpu())
    model.hybridize(static_alloc=True)

def predict_params(model, input_data):
    # Perform prediction using the loaded model
    output = model(input_data)

    # Convert prediction to a JSON response
    response = {'prediction': output.asnumpy().tolist()}

    return jsonify(response)
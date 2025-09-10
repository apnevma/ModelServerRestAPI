import torch
from flask import jsonify

def load_pt(filename):
    model = torch.load(filename, map_location=torch.device('cpu'))
    model.eval()

def predict_pt(model, input_data):
    # Perform prediction using the loaded model
    with torch.no_grad():
        output = model(input_data)

    # Convert prediction to a JSON response
    response = {'prediction': output[0].tolist()}

    return jsonify(response)
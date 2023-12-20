import joblib
from flask import jsonify

def load_joblib(filename):
    model = joblib.load(filename)
    return model


def predict_joblib(model, input_data):
    # Perform prediction using the loaded model
    prediction = model.predict(input_data)[0]

    # Convert prediction to a JSON response
    response = {'prediction': prediction}

    return jsonify(response)
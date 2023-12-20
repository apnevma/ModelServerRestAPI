import tensorflow as tf
from flask import jsonify

def load_h5(model_path):
    model = tf.keras.models.load_model(model_path)
    return model

def predict_h5(model, input_data):
    # Perform prediction using the loaded model
    predictions = model.predict(tf.constant([input_data]))

    # Convert predictions to a JSON response
    response = {'predictions': predictions.tolist()}

    return jsonify(response)
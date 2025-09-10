import tensorflow as tf
from flask import jsonify
from utils import wait_until_stable


def load_tensorflow(model_path):
    # Wait until file is fully written before loading
    if wait_until_stable(model_path):
        print(f"File {model_path} is stable, loading model...")
        model = tf.keras.models.load_model(model_path)
        info = get_tensorflow_model_info(model)
        return info, model
    else:
        print(f"File {model_path} did not stabilize in time, skipping.")
    


def get_tensorflow_model_info(model):
    
    model.summary()

    # Input shape
    try:
        input_shape = model.input_shape
        input_type = str(model.inputs[0].dtype)
    except AttributeError:
        input_shape = "unknown"
    
    # Output shape
    try:
        output_shape = model.output_shape
    except AttributeError:
        output_shape = "unknown"

    return {
        "type": "Keras/TensorFlow",
        "input_shape": input_shape,
        "input_type": input_type,
        "output_shape": output_shape,
        #"summary": summary_text
    }


def predict_tensorflow(model, input_data):
    # Perform prediction using the loaded model
    predictions = model.predict(tf.constant([input_data]))

    # Convert predictions to a JSON response
    response = {'predictions': predictions.tolist()}

    return jsonify(response)
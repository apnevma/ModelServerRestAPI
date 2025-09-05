import tensorflow as tf
from flask import jsonify


def load_h5(model_path):
    model = tf.keras.models.load_model(model_path)
    info = get_h5_model_info(model)

    return info, model


def get_h5_model_info(model):
    
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

    '''
    # Layer summary (text)
    from io import StringIO
    import sys
    buffer = StringIO()
    model.summary(print_fn=lambda x: buffer.write(x + "\n"))
    summary_text = buffer.getvalue()
    '''

    return {
        "type": "Keras/TensorFlow",
        "input_shape": input_shape,
        "input_type": input_type,
        "output_shape": output_shape,
        #"summary": summary_text
    }


def predict_h5(model, input_data):
    # Perform prediction using the loaded model
    predictions = model.predict(tf.constant([input_data]))

    # Convert predictions to a JSON response
    response = {'predictions': predictions.tolist()}

    return jsonify(response)
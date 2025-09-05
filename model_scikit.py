import joblib
from utils import make_json_serializable 

def load_joblib(filename):
    model = joblib.load(filename)
    info = get_scikit_model_info(model)
    return info, model


def get_scikit_model_info(model):
    try:
        input_shape = [model.n_features_in_]
    except AttributeError:
        input_shape = "unknown"
    
    return {
        "type": "Scikit-learn",
        "input_shape": input_shape,
        "example": [0] * input_shape[0] if input_shape != "unknown" else None
    }


def predict_joblib(model, input_data):
    # Perform prediction using the loaded model
    prediction = model.predict(input_data)[0]


    # Convert to pure Python types (int, float, list)
    prediction = make_json_serializable(prediction)

    return prediction
import joblib
from utils import make_json_serializable, wait_until_stable

def load_joblib(filename):
    # Wait until file is fully written before loading
    if wait_until_stable(filename):
        print(f"File {filename} is stable, loading model...")
        model = joblib.load(filename)
        info = get_scikit_model_info(model)
        return info, model
    else:
        print(f"File {filename} did not stabilize in time, skipping.")    
    



def get_scikit_model_info(model):
    try:
        input_shape = [model.n_features_in_]
    except AttributeError:
        input_shape = "unknown"
    
    input_dtype = "unknown"
    try:
        if hasattr(model, "coef_"):
            # coefficients usually have same dtype as training data
            input_dtype = str(model.coef_.dtype)
        elif hasattr(model, "feature_importances_"):
            input_dtype = str(model.feature_importances_.dtype)
    except Exception:
        input_dtype = "unknown"

    return {
        "type": "Scikit-learn",
        "input_shape": input_shape,
        "input_dtype": input_dtype,
        "example": [0] * input_shape[0] if input_shape != "unknown" else None
    }


def predict_joblib(model, input_data):
    # Perform prediction using the loaded model
    prediction = model.predict(input_data)[0]


    # Convert to pure Python types (int, float, list)
    prediction = make_json_serializable(prediction)

    return prediction
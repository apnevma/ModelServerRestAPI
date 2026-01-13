import joblib
import numpy as np
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
    print("Going to predict with data:", input_data)

    # Convert to numpy array for easier shape handling
    X = np.array(input_data)

    # If input is 1D (single sample like [25.1, 55, 30.5]),
    # reshape it to (1, n_features)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    # Perform prediction
    predictions = model.predict(X)

    # Convert to pure Python types (int, float, list)
    predictions = make_json_serializable(predictions)

    return predictions
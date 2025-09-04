import joblib
from utils import make_json_serializable 

def load_joblib(filename):
    model = joblib.load(filename)
    return model


def predict_joblib(model, input_data):
    # Perform prediction using the loaded model
    prediction = model.predict(input_data)[0]


    # Convert to pure Python types (int, float, list)
    prediction = make_json_serializable(prediction)

    return prediction
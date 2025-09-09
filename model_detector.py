import os
import model_tensorflow
import model_scikit
import model_pytorch
import model_savedmodel
from utils import make_json_serializable


def switch_case_load(filename):
    _, extension = os.path.splitext(filename)
    model = None

    if extension in ['.h5', '.tf']:
        print("Processing model from Tensorflow (H5)")
        info, model = model_tensorflow.load_h5(filename)

    elif extension in ['.pkl', '.joblib']:
        print("Processing model from Scikit-learn")
        info, model = model_scikit.load_joblib(filename)

    elif extension in ['.pt', '.pth']:
        print("Processing model from PyTorch")
        model = model_pytorch.load_pt(filename)

    elif extension == '.params':
        print("Processing model from MXNet")
        # model = model_mxnet.load_params(filename)

    elif os.path.isdir(filename):
        # SavedModel → TF Serving
        print("Processing SavedModel for TF Serving")
        info, model = model_savedmodel.load_savedmodel(filename)

    else:
        print("Unsupported format:", filename)

    return info, model


def switch_case_predict(filename, model, data):
    _, extension = os.path.splitext(filename)

    # Case: TF Serving (model is just a serving URL string)
    if isinstance(model, str) and model.startswith("http"):
        return model_savedmodel.predict_savedmodel(model, data)

    # Case: local models
    prediction = None
    if extension in ['.h5', '.tf']:
        prediction = model_tensorflow.predict_h5(model, data)
    elif extension in ['.pkl', '.joblib']:
        prediction = model_scikit.predict_joblib(model, data)
    elif extension in ['.pt', '.pth']:
        prediction = model_pytorch.predict_pt(model, data)

    return prediction


def detect(filename):
    info, model = switch_case_load(filename)
    return info, model


def predict(filename, model, data):
    prediction = switch_case_predict(filename, model, data)
    return make_json_serializable(prediction)
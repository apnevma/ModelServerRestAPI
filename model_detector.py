import os
import tensorflow_models
import scikit_models
import pytorch_models
import savedmodel
from utils import make_json_serializable


def switch_case_load(filename):
    _, extension = os.path.splitext(filename)
    model = None

    if extension in ['.h5', '.keras']:
        print("Processing model from Tensorflow (.h5 or .keras)")
        info, model = tensorflow_models.load_tensorflow(filename)

    elif extension in ['.pkl', '.joblib']:
        print("Processing model from Scikit-learn")
        info, model = scikit_models.load_joblib(filename)

    elif extension in ['.pt', '.pth']:
        # raw torch.save(model) format (class must exist)
        print("Processing model from PyTorch")
        model = pytorch_models.load_pytorch(filename)

    elif extension == '.params':
        print("Processing model from MXNet")
        # info, model = model_mxnet.load_params(filename)

    elif os.path.isdir(filename):
        # SavedModel → TF Serving
        print("Processing SavedModel for TF Serving")
        info, model = savedmodel.load_savedmodel(filename)

    else:
        print("Unsupported format:", filename)

    return info, model


def switch_case_predict(filename, model, data):
    _, extension = os.path.splitext(filename)

    # Case: TF Serving (model is just a serving URL string)
    if isinstance(model, str) and model.startswith("http"):
        return savedmodel.predict_savedmodel(model, data)

    # Case: local models
    prediction = None
    if extension in ['.h5', '.keras']:
        prediction = tensorflow_models.predict_tensorflow(model, data)
    elif extension in ['.pkl', '.joblib']:
        prediction = scikit_models.predict_joblib(model, data)
    elif extension in ['.pt', '.pth']:
        prediction = pytorch_models.predict_pytorch(model, data)

    return prediction


def detect(filename):
    info, model = switch_case_load(filename)
    return info, model


def predict(filename, model, data):
    prediction = switch_case_predict(filename, model, data)
    return make_json_serializable(prediction)
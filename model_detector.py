import os
import tensorflow_models
import scikit_models
import pytorch_models
import savedmodel
from utils import make_json_serializable


def switch_case_load(path):
    info, model = None, None

    # Case: file-based models
    if os.path.isfile(path):
        _, extension = os.path.splitext(path)

        if extension in ['.h5', '.keras']:
            print("Processing model from Tensorflow (.h5 or .keras)")
            info, model = tensorflow_models.load_tensorflow(path)

        elif extension in ['.pkl', '.joblib']:
            print("Processing model from Scikit-learn")
            info, model = scikit_models.load_joblib(path)

        elif extension in ['.pt', '.pth']:
            print("Processing PyTorch single-file model (.pt/.pth)")
            info, model = pytorch_models.load_pytorch(path)

        elif extension == '.params':
            print("Processing model from MXNet")

        else:
            print("Unsupported file format:", path)

    # Case: folder-based models
    elif os.path.isdir(path):
        if all(d.isdigit() and os.path.exists(os.path.join(path, d, "saved_model.pb"))
                for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))):
            # TensorFlow SavedModel with versioning
            version_dirs = sorted(
                [d for d in os.listdir(path)
                if d.isdigit() and os.path.isdir(os.path.join(path, d))]
            )
            if version_dirs:
                latest_version = version_dirs[-1]  # pick highest version
                print(f"Processing TensorFlow SavedModel (TF Serving format), version={latest_version}")
                info, model = savedmodel.load_savedmodel(path, latest_version)
        

        elif (os.path.exists(os.path.join(path, "model.pt")) or
              os.path.exists(os.path.join(path, "model.pth"))) and \
              os.path.exists(os.path.join(path, "model_class.py")):
            # PyTorch "drop-in folder" format
            print("Processing PyTorch folder model")
            info, model = pytorch_models.load_pytorch_folder(path)

        else:
            print("Unsupported folder format:", path)

    else:
        print("Path does not exist:", path)

    return info, model


def switch_case_predict(path, model, data):
    import os
    prediction = None

    # TF Serving case
    if isinstance(model, str) and model.startswith("http"):
        return savedmodel.predict_savedmodel(model, data)

    # File or folder
    if os.path.isfile(path):
        _, extension = os.path.splitext(path)
        if extension in ['.h5', '.keras']:
            prediction = tensorflow_models.predict_tensorflow(model, data)
        elif extension in ['.pkl', '.joblib']:
            print("Hit .pkl extension branch!")
            prediction = scikit_models.predict_joblib(model, data)
        elif extension in ['.pt', '.pth']:
            prediction = pytorch_models.predict_pytorch(model, data)

    elif os.path.isdir(path):
        if os.path.exists(os.path.join(path, "model_class.py")):
            prediction = pytorch_models.predict_pytorch(model, data)

    return prediction


def detect(filename):
    info, model = switch_case_load(filename)
    return info, model


def predict(filename, model, data):
    prediction = switch_case_predict(filename, model, data)
    return make_json_serializable(prediction)
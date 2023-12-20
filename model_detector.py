import os
import model_tensorflow
import model_scikit
import model_pytorch

def switch_case_load(filename):
    _, extension = os.path.splitext(filename)
    model = None
    if extension == '.h5' or extension == '.tf':
        print("Processing model from Tensorflow")
        model = model_tensorflow.load_h5(filename)
    if extension == '.pkl' or extension == '.joblib':
        print("Processing model from Scikit")
        model = model_scikit.load_joblib(filename)
    if extension == '.pt' or extension == '.pth':
        print("Processing model from Pytorch")
        model = model_pytorch.load_pt(filename)
    if extension == '.params':
        print('Processing model from MXNet')
        model = model_mxnet.load_params(filename)
    return model


def switch_case_predict(filename, model, data):
    _, extension = os.path.splitext(filename)
    prediction = None
    if extension == '.h5' or extension == '.tf':
        prediction = model_tensorflow.predict_h5(model, data)
    if extension == '.pkl' or extension == '.joblib':
        prediction = model_scikit.predict_joblib(model, data)
    if extension == '.pt' or extension == '.pth':
        prediction = model_pytorch.predict_pt(model, data)
    #if extension == 'params':
    #    print('Processing model from MXNet')
    #    model = model_mxnet.load_params(filename)
    return prediction


def detect(filename):
    # A method which detects how to load a model judging by its extension
    model = switch_case_load(filename)
    return model

def predict(filename, model,data):
    # A method which detects how to load a model judging by its extension
    prediction = switch_case_predict(filename,model,data)
    return prediction
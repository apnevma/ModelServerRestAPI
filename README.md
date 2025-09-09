# ModelServer REST API

A Flask-based REST API for serving machine learning models dynamically. So far, supports **Scikit-learn** (`.pkl`) and **TensorFlow** models. Each model is exposed as its own endpoint, allowing clients to send input data and receive predictions in JSON format.


## Features

- **Dynamic model serving**  
  Automatically detects and loads models from the `models/` folder.

- **Automatic endpoint creation**  
  Each model is served under `/model_name` (e.g., `/rf_model`, `/global_model`).

- **TF Serving integration**  
  SavedModel folders are automatically served via individual Docker containers running TensorFlow Serving. Flask endpoints proxy requests to the corresponding TF Serving URL.

- **File stability check**  
  Ensures a model file/folder is fully written before loading it, preventing `PermissionError`.

- **Multi-framework support**  
  - Scikit-learn models (`.pkl`, `.joblib`)  
  - TensorFlow/Keras models (`.h5`)  
  - TensorFlow SavedModels (`./models/model_name/version/saved_model.pb`) served via TF Serving

- **Model info introspection**  
  Provides input shape and expected data type for each local model.  
  If a prediction request fails due to wrong input format, the API returns the model’s input requirements.

- **JSON predictions**  
  Predictions are returned in structured JSON format.

- **CORS enabled**  
  Easy integration with web clients.



## Installation

1. Clone the repository:
```bash
git clone <repo_url>
cd ModelServerrRestAPI
```

2. Create a Python virtual environment and activate it:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Place your models in the `models/` folder.



## Usage
### Start the server
```bash
python RestAPI.py
```
The API will run on:
http://127.0.0.1:8086


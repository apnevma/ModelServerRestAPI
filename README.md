# ModelServer REST API

A Flask-based REST API for dynamically serving machine learning models. Supports **Scikit-learn**, **TensorFlow/Keras**, **TensorFlow SavedModels**, and **PyTorch** models. Each model is automatically exposed as its own endpoint, allowing clients to send input data and receive predictions in JSON format.  

Now fully **Dockerized**:
* One container for the API (`model_server_api`)
* One TF Serving container per TensorFlow SavedModel

## Features

- **Dynamic model serving**  
  Automatically detects and loads models from the `models/` folder.

- **Automatic endpoint creation**  
  Each model is served under `/model_name` (e.g., `/rf_model`, `/global_model`).

- **TF Serving integration**  
  SavedModel folders are automatically served via individual Docker containers running TensorFlow Serving. Flask endpoints proxy requests to the corresponding TF Serving URL.

- **PyTorch folder-based models**  
  Drop-in folders containing `model.pt` (or `.pth`) and `model_class.py` are supported. The API dynamically loads the class and weights.

- **File stability check**  
  Ensures a model file/folder is fully written before loading it, preventing `PermissionError`.

- **Multi-framework support**  
  - Scikit-learn models (`.pkl`, `.joblib`)  
  - TensorFlow/Keras models (`.h5`)  
  - TensorFlow SavedModels (`./models/model_name/version/saved_model.pb`) served via TF Serving
  - PyTorch folder-based models (`model.pt` + `model_class.py`)

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

2. Create a `models/` folder and place your models in it. Examples:
```bash
models/
│
├── rf_model.pkl            # Scikit Learn .pkl model
│
├── fire_savedmodel/        # TensorFlow SavedModel folder
│   └── 1/
│       ├── assets/
│       ├── variables/
│       ├── fingerprint.pb
│       └── saved_model.pb
│   
└── fire_pytorch/           # PyTorch folder-based model
    ├── model.pt
    └── model_class.py

```
## Docker Setup

1. Make sure you have Docker and Docker Compose installed and running on your machine.

2. Create Docker network  
  All containers communicate via a dedicated network:
    ```bash
    docker network create model_server_net
    ```

3. Build and start containers
    ```bash
    docker-compose up -d --build
    ```
    * model_server_api detects all models and exposes endpoints.
    * Each TensorFlow SavedModel is served via its own TF Serving container automatically.
    * Communication is internal via Docker network. No extra ports needed for TF Serving containers.


## Usage
### Start the server
```bash
python RestAPI.py
```
The API will run on:
http://127.0.0.1:8086

### Test a model
You can test a loaded model using the provided `prediction_test.py` script. For example, to test the `fire_nn` model:  
```python
import requests

# URL of the local model endpoint
url = "http://localhost:8086/fire_nn"

# Example input data (features = [temperature, humidity, soundLevel])
data = {
    "input": [[70.5, 20.0, 76.0]]
}

try:
    # Send POST request
    response = requests.post(url, json=data)
    response.raise_for_status()  # Raise exception if HTTP error

    # Get JSON result
    prediction = response.json()
    print(prediction)

except requests.exceptions.RequestException as e:
    print("Error communicating with server:", e)
```
#### Notes:
  * Replace `"fire_nn"` with the name of the model you want to test.
  * Input data should match the model’s expected format. If it doesn’t, the API will return the expected input info.

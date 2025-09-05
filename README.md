# ModelServer REST API

A Flask-based REST API for serving machine learning models dynamically. So far, supports **Scikit-learn** (`.pkl`) and **TensorFlow** (`.h5`) models. Each model is exposed as its own endpoint, allowing clients to send input data and receive predictions in JSON format.



## Features

- Automatically detects and loads models from a specified folder: `models/`.
- Creates a REST endpoint for each model.
- Supports both Scikit-learn and TensorFlow/Keras models.
- Provides input shape and type information for each model.
- Returns predictions in JSON format.
- Cross-Origin Resource Sharing (CORS) enabled for easy integration.



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


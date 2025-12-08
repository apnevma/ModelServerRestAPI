import requests

models_to_activate = ("saved_model", "capacitor_fit_model_savedmodel", "rf_model")

for model in models_to_activate:
    resp = requests.post(f"http://localhost:8086/activate/{model}")
    print(resp.json())
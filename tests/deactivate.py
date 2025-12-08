import requests

models_to_deactivate = ("saved_model", "fake_model")

for model in models_to_deactivate:
    resp = requests.post(f"http://localhost:8086/deactivate/{model}")
    print(resp.json())
import requests
import os


API_HOST = os.getenv("API_HOST", "localhost")
PORT = int(os.getenv("PORT", "8086"))

# URL of local model endpoint
url = f"http://{API_HOST}:{PORT}/predict/rf_model"

# Example input data (features = [temperature, humidity, soundLevel])
data = {
    "input": [[70.5, 20.0, 30.5]]
}

try:
    # Send POST request
    response = requests.post(url, json=data)
    response.raise_for_status()  # Raise exception if HTTP error

    # Get JSON result (prediction is already JSON-serializable)
    prediction = response.json()
    print(prediction)

except requests.exceptions.RequestException as e:
    print("Error communicating with server:", e)
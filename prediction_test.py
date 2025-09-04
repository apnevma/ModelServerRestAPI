import requests

# URL of your local model endpoint
url = "http://127.0.0.1:8086/rf_model"

# Example input data (features = [temperature, humidity, soundLevel])
data = {
    "input": [[75.5, 20.0, 76.0]]
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
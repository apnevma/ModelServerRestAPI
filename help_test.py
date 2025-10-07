import requests

API_URL = "http://168.119.235.102:8086/help"

def test_help():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        
        data = response.json()
        print("=== Help Endpoint Response ===")
        print(response.text)
        
    except requests.exceptions.RequestException as e:
        print("Error contacting the API:", e)

if __name__ == "__main__":
    test_help()
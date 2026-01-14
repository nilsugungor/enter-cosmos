import requests
import json

url = "http://127.0.0.1:5000/chart"

data = {
    "date": "1990-06-15",
    "time": "14:30",
    "city": "New York, USA"
}

response = requests.post(url, json=data)

print(response.status_code)
print(response.json())

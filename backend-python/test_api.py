import requests
import json

url = "http://localhost:5000/api/match-jobs"
data = {
    "profile_text": "Im Fullstack developer, I make projects in python, react, js, ts",
    "job_keyword": "Developer"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}") 
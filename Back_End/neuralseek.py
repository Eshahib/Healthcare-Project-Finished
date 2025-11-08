import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://stagingapi.neuralseek.com/v1/stony4/maistro")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")

inputSymptoms = {"fever": True, "cough": True, "fatigue": False}  # example payload

payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "symptoms",
        "value": inputSymptoms
    },
    "id": 1
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {NEURALSEEK_API_KEY}"
}

# 🧠 Print the payload you’re about to send
print("📦 Sending payload:")
print(json.dumps(payload, indent=2))

# 🚀 Send request
response = requests.post(NEURALSEEK_API_URL, headers=headers, json=payload)

# 🧾 Print HTTP status + body
print(f"\n🔁 Status Code: {response.status_code}")
print("🧩 Response JSON:")
try:
    print(json.dumps(response.json(), indent=2))
except ValueError:
    print(response.text)

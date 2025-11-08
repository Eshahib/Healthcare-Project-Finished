import os
import requests
from dotenv import load_dotenv
import json
from encryption import encrypt_phi
from audit_log import log_phi_access

load_dotenv()

NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://stagingapi.neuralseek.com/v1/stony4/maistro")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")

inputSymptoms = ["fever", "cough", "fatigue", "vomitting from head injury"]  # example payload

payload = {
    "agent": "Healthcare",
    "params": [
        {
            "name": "symptoms",
            "value": inputSymptoms  # Convert list to JSON string
        }
    ],
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "apikey": NEURALSEEK_API_KEY
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
    data = response.json()
    print(data)
    print(data["answer"])
except ValueError:
    print(response.text)

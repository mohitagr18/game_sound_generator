
# test_advisor_api.py (FULL FILE)

import requests
import json

# Change this to match your local/server setup
ADVISOR_API_URL = "http://localhost:8080/advisor"

sample_payload = {
    "session_log": [
        {
            "event": {
                "state": "explore",
                "intensity": 35,
                "flags": ["lowhealth"]
            },
            "intent": {
                "theme": "explore",
                "activestems": ["pad", "bass"],
                "targetgains": {"pad": 0.7, "bass": 0.6},
                "fadedurations": {"pad": 1.2, "bass": 1.0},
                "timestamp": "2025-10-28T19:48:00Z"
            }
        }
    ],
    "current_state": {
        "state": "combat",
        "intensity": 85,
        "flags": ["boss"]
    },
    "user_query": "What should the transition be for maximum tension?"
}

def main():
    resp = requests.post(
        ADVISOR_API_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(sample_payload)
    )
    print("Status:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print("Response text:", resp.text)
        print("Error parsing JSON:", str(e))

if __name__ == "__main__":
    main()

# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# filepath: mobile/swarmz_client.py
"""
SWARMZ mobile client.
"""

import requests

SERVER_URL = "http://localhost:8765"

def send_request(endpoint, data=None):
    try:
        response = requests.post(f"{SERVER_URL}/{endpoint}", json=data)
        print(response.json())
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    send_request("ping")

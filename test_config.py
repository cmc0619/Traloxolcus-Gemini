import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:8001/api/v1"

def test_config():
    print("Getting Config...")
    try:
        res = requests.get(f"{BASE_URL}/config")
        print(f"Initial: {res.json()}")
        
        new_config = {
            "node_id": "TEST_NODE_UPDATED",
            "width": 1920,
            "height": 1080,
            "fps": 60,
            "bitrate": 15000000
        }
        
        print("\nUpdating Config...")
        res = requests.post(f"{BASE_URL}/config", json=new_config)
        print(f"Update: {res.status_code}")
        
        print("\nVerifying Config Get...")
        res = requests.get(f"{BASE_URL}/config")
        data = res.json()
        print(f"Result: {data}")
        
        if data["node_id"] == "TEST_NODE_UPDATED" and data["fps"] == 60:
            print("PASS: Config updated via API")
        else:
            print("FAIL: Config mismatch")
            
        # Verify persistence file
        if os.path.exists("settings.json"):
             with open("settings.json") as f:
                 file_data = json.load(f)
                 if file_data["node_id"] == "TEST_NODE_UPDATED":
                     print("PASS: Settings file persisted")
                 else:
                     print("FAIL: Settings file mismatch")
        else:
             print("FAIL: settings.json not created")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_config()

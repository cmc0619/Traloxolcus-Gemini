import requests
import asyncio
import time

# To strictly verify mesh, we'd need multiple servers. 
# For this e2e, we'll verify the API accepts the new 'source' param 
# and doesn't crash when it tries to broadcast (it will fail to connect to peers but should log warning).

BASE_URL = "http://127.0.0.1:8004/api/v1"

def test_mesh_api():
    print("Testing Start Trigger (User -> Mesh)...")
    payload = {"session_id": "mesh_test_01", "source": "user"}
    try:
        res = requests.post(f"{BASE_URL}/record/start", json=payload)
        print(f"Start: {res.status_code}")
        if res.status_code == 200:
            print("PASS: Start command accepted")
    except Exception as e:
        print(f"FAIL: {e}")

    time.sleep(1)

    print("Testing Stop Trigger (User -> Mesh)...")
    payload = {"source": "user"}
    try:
        res = requests.post(f"{BASE_URL}/record/stop", json=payload)
        print(f"Stop: {res.status_code}")
        if res.status_code == 200:
             print("PASS: Stop command accepted")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test_mesh_api()

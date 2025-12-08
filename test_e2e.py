import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_api():
    print("Checking Status...")
    try:
        res = requests.get(f"{BASE_URL}/status")
        print(f"Status: {res.status_code}")
        if res.status_code != 200:
             print(res.text)
             return
        print(res.json())
        
        print("\nStarting Recording...")
        res = requests.post(f"{BASE_URL}/record/start", json={"session_id": "test_session_01"})
        print(f"Start: {res.status_code}")
        print(res.json())
        
        time.sleep(2)
        
        print("\nChecking Status (Recording)...")
        res = requests.get(f"{BASE_URL}/status")
        print(res.json())
        
        print("\nStopping Recording...")
        res = requests.post(f"{BASE_URL}/record/stop")
        print(f"Stop: {res.status_code}")
        stop_data = res.json()
        print(stop_data)
        
        print("\nListing Recordings...")
        res = requests.get(f"{BASE_URL}/recordings")
        files = res.json()["files"]
        print(files)
        
        manifest_file = stop_data.get("manifest")
        if manifest_file:
             print(f"\nConfirming Offload for {manifest_file}...")
             # Need real session/camera id from filename?
             # Filename format: {session_id}_{NODE_ID}.json
             # Splitting roughly:
             session_id = stop_data["session_id"]
             # Recalculated locally or trusted? The confirm endpoint expects us to send what we have.
             # We need camera_id.
             camera_id = res.json().get("camera_id", "DESKTOP-MOCK") # Actually read from status
             status_res = requests.get(f"{BASE_URL}/status").json()
             camera_id = status_res["node_id"]
             
             confirm_payload = {
                 "session_id": session_id,
                 "camera_id": camera_id,
                 "file": stop_data["file"],
                 "checksum": {"algo": "sha256", "value": "mock"}
             }
             res = requests.post(f"{BASE_URL}/recordings/confirm", json=confirm_payload)
             print(f"Confirm: {res.status_code}, {res.json()}")
        
        print("\nTesting Update Check...")
        res = requests.post(f"{BASE_URL}/update/check")
        print(res.json())
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    # Wait for server to be up
    for i in range(5):
        try:
             requests.get(f"{BASE_URL}/status")
             break
        except:
             time.sleep(1)
    test_api()

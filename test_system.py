import requests
import asyncio
import sys

# Since we are testing endpoints that call services, we can test the API responses.
# Mock mode is active, so this shouldn't shutdown the dev machine.

BASE_URL = "http://127.0.0.1:8002/api/v1"

def test_system_endpoints():
    print("Testing Network Status...")
    res = requests.get(f"{BASE_URL}/system/network")
    print(f"Network: {res.json()}")
    
    print("\nTesting Reboot (Mock)...")
    res = requests.post(f"{BASE_URL}/system/reboot")
    print(f"Reboot: {res.json()}")
    
    if res.json()["status"] == "rebooting":
        print("PASS: Reboot")
    else:
        print("FAIL: Reboot")

if __name__ == "__main__":
    test_system_endpoints()

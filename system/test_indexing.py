import requests
import time
import sys

API_URL = "http://localhost:8000"

def test_indexing():
    # Login
    print("Logging in...")
    try:
        res = requests.post(f"{API_URL}/token", data={"username": "adminuser", "password": "admin"})
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # Trigger Indexing
        print("Triggering indexing...")
        res = requests.post(f"{API_URL}/api/admin/index", json={"storage_mode": "nas"}, headers=headers)
        if res.status_code == 200:
            print("Indexing triggered successfully.")
        else:
            print(f"Failed to trigger indexing: {res.text}")
            return

        # Monitor status
        print("Monitoring status...")
        for _ in range(10):
            time.sleep(2)
            try:
                res = requests.get(f"{API_URL}/api/admin/nas/status", headers=headers)
                if res.status_code == 200:
                    status = res.json()
                    print(f"Status: {status['indexing_status']}, Progress: {status['indexing_progress']}%")
                    if status['indexing_status'] == "Completed" or status['indexing_status'].startswith("Failed"):
                        break
                else:
                    print(f"Failed to get status: {res.status_code}")
            except requests.exceptions.ConnectionError:
                print("Connection refused! Server might have crashed.")
                break

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_indexing()

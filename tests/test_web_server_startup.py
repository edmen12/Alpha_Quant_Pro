import sys
import os
import time
import threading
import requests
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import web_server

# Mock Engine
class MockEngine:
    def __init__(self):
        self.running = False
        self.symbols = ["XAUUSD"]
        self.last_equity = 10000.0
        self.last_balance = 10000.0
        self.last_daily_pnl = 0.0
        self.open_positions_cache = []

def test_server():
    print("Starting Test Server...")
    engine = MockEngine()
    
    # Set password
    web_server.set_password("testpass")
    
    # Start server in thread
    web_server.start_background_server(engine, port=8001)
    
    # Wait for startup
    time.sleep(2)
    
    try:
        # Test 1: Open Access (Should fail without token)
        print("Testing Unprotected Access...")
        try:
            r = requests.get("http://127.0.0.1:8001/api/status", timeout=2)
            if r.status_code == 403 or r.status_code == 401:
                print("PASS: Unprotected access blocked")
            else:
                print(f"FAIL: Unexpected status code {r.status_code}")
        except Exception as e:
            print(f"FAIL: Connection error {e}")

        # Test 2: Login
        print("Testing Login...")
        r = requests.post("http://127.0.0.1:8001/api/login", json={"password": "testpass"})
        if r.status_code == 200:
            token = r.json()["token"]
            print(f"PASS: Login successful. Token: {token[:10]}...")
        else:
            print(f"FAIL: Login failed {r.status_code} {r.text}")
            return

        # Test 3: Protected Access
        print("Testing Protected Access...")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get("http://127.0.0.1:8001/api/status", headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data["equity"] == 10000.0:
                print("PASS: Status data correct")
            else:
                print(f"FAIL: Data mismatch {data}")
        else:
            print(f"FAIL: Protected access failed {r.status_code}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        print("Stopping Server...")
        web_server.stop_background_server()

if __name__ == "__main__":
    test_server()

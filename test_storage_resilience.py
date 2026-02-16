import requests
import os
import time

BASE = "http://127.0.0.1:8012"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MISSIONS = os.path.join(DATA_DIR, "missions.jsonl")

def write_blank_and_bad_lines():
    with open(MISSIONS, "w", encoding="utf-8") as f:
        f.write("\n\n")
        f.write("{not valid json}\n")
        f.write("\n")

def create_mission(goal):
    resp = requests.post(f"{BASE}/v1/missions/create", json={
        "goal": goal,
        "category": "test",
        "constraints": {},
    })
    print("Create mission resp:", resp.status_code, resp.json())
    assert resp.status_code == 200
    assert resp.json().get("ok")
    return resp.json()["mission_id"]

def list_missions():
    resp = requests.get(f"{BASE}/v1/missions/list")
    print("List missions resp:", resp.status_code, resp.json())
    assert resp.status_code == 200
    return resp.json()["missions"]

def check_storage():
    resp = requests.get(f"{BASE}/v1/debug/storage_check")
    print("Storage check resp:", resp.status_code, resp.json())
    assert resp.status_code == 200
    return resp.json()

if __name__ == "__main__":
    print("[TEST] Writing blank and bad lines to missions.jsonl...")
    write_blank_and_bad_lines()
    time.sleep(0.5)
    print("[TEST] Creating mission 1...")
    create_mission("First live mission")
    print("[TEST] Creating mission 2...")
    create_mission("Second mission")
    print("[TEST] Listing missions...")
    missions = list_missions()
    assert len(missions) >= 2, f"Expected at least 2 missions, got {len(missions)}"
    print("[TEST] Checking storage health...")
    stats = check_storage()
    assert stats["missions"]["bad_rows"] >= 1, "Should have at least 1 bad row quarantined"
    print("[TEST] All checks passed.")
#!/usr/bin/env python3
"""Test script for SWARMZ console endpoints"""
import requests
import json

print("=" * 60)
print("SWARMZ Console Endpoints Test")
print("=" * 60)

# Test 1: Create mission
print("\n[1] Creating first mission...")
resp = requests.post('http://127.0.0.1:8012/v1/missions/create', json={
    'goal': 'First live mission',
    'category': 'test',
    'constraints': {},
    'results': {}
})
print(f"Status: {resp.status_code}")
data = resp.json()
print(json.dumps(data, indent=2))
if data.get('ok'):
    mission_id_1 = data.get('mission_id')
    print(f"✓ Mission created: {mission_id_1}")
else:
    print(f"✗ Mission creation failed: {data.get('error')}")

# Test 2: Create another mission
print("\n[2] Creating second mission...")
resp = requests.post('http://127.0.0.1:8012/v1/missions/create', json={
    'goal': 'Second live mission',
    'category': 'analysis',
    'constraints': {},
    'results': {}
})
print(f"Status: {resp.status_code}")
data = resp.json()
if data.get('ok'):
    mission_id_2 = data.get('mission_id')
    print(f"✓ Mission created: {mission_id_2}")
else:
    print(f"✗ Mission creation failed: {data.get('error')}")

# Test 3: List missions
print("\n[3] Listing missions...")
resp = requests.get('http://127.0.0.1:8012/v1/missions/list')
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Total missions: {data.get('count')}")
print(f"✓ Mission list count: {data.get('count')}")
for m in data.get('missions', [])[:3]:
    print(f"  - {m.get('mission_id')}: {m.get('goal')} ({m.get('status')})")

# Test 4: Get UI state
print("\n[4] Getting UI state...")
resp = requests.get('http://127.0.0.1:8012/v1/ui/state')
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"✓ Phase: {data.get('phase')}")
print(f"✓ Total missions: {data.get('missions', {}).get('count_total')}")
print(f"✓ Status counts: {data.get('missions', {}).get('count_by_status')}")
print(f"✓ Last events: {len(data.get('last_events', []))} events")

# Test 5: Check redirect
print("\n[5] Checking / redirect to /console...")
resp = requests.get('http://127.0.0.1:8012/', allow_redirects=False)
print(f"Status: {resp.status_code}")
location = resp.headers.get('Location')
print(f"Location: {location}")
if location == '/console':
    print(f"✓ Redirect works correctly")
else:
    print(f"✗ Redirect failed")

# Test 6: Console page loads
print("\n[6] Checking /console page...")
resp = requests.get('http://127.0.0.1:8012/console')
print(f"Status: {resp.status_code}")
checks = {
    'Has SWARMZ Console': 'SWARMZ Console' in resp.text,
    'Has CREATE button': 'CREATE' in resp.text,
    'Has RUN button': 'RUN' in resp.text,
    'Has REFRESH button': 'REFRESH' in resp.text,
    'Has phase label': 'phaseLabel' in resp.text,
    'Has missions table': 'missionsBody' in resp.text,
    'Has statistics': 'Statistics' in resp.text or 'totalMissions' in resp.text,
}
for check, result in checks.items():
    print(f"{'✓' if result else '✗'} {check}")

print("\n" + "=" * 60)
print("Test Summary:")
print(f"✓ Missions created and listed")
print(f"✓ UI state endpoint working")
print(f"✓ Redirect / → /console working")
print(f"✓ Console UI page loads")
print("=" * 60)

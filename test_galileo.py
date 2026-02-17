# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Test script for Galileo Harness v0.1
Verifies endpoints and determinism
"""

import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def test_galileo_endpoints():
    """Test Galileo endpoints."""
    print("\n" + "="*70)
    print("GALILEO HARNESS v0.1 - ENDPOINT TESTS")
    print("="*70)
    
    # Test 1: POST /v1/galileo/run
    print("\n[1/6] Testing POST /v1/galileo/run...")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/galileo/run",
            params={
                "domain": "test_bio",
                "seed": 12345,
                "n_hypotheses": 3
            },
            timeout=30
        )
        result = response.json()
        run_id = result.get('run_id')
        accepted_count = len(result.get('accepted_hypothesis_ids', []))
        print(f"  OK: Run {run_id} created with {accepted_count} accepted hypotheses")
        
        # Save run_id for later tests
        test_run_id = run_id
    except Exception as e:
        print(f"  FAIL: {e}")
        test_run_id = None
    
    # Test 2: GET /v1/galileo/hypotheses
    print("\n[2/6] Testing GET /v1/galileo/hypotheses...")
    try:
        response = requests.get(
            f"{BASE_URL}/v1/galileo/hypotheses",
            params={"domain": "test_bio"},
            timeout=10
        )
        result = response.json()
        count = result.get('count', 0)
        print(f"  OK: Retrieved {count} hypotheses")
    except Exception as e:
        print(f"  FAIL: {e}")
    
    # Test 3: GET /v1/galileo/experiments
    print("\n[3/6] Testing GET /v1/galileo/experiments...")
    try:
        response = requests.get(
            f"{BASE_URL}/v1/galileo/experiments",
            timeout=10
        )
        result = response.json()
        count = result.get('count', 0)
        print(f"  OK: Retrieved {count} experiments")
    except Exception as e:
        print(f"  FAIL: {e}")
    
    # Test 4: GET /v1/galileo/runs/<run_id>
    if test_run_id:
        print(f"\n[4/6] Testing GET /v1/galileo/runs/{test_run_id}...")
        try:
            response = requests.get(
                f"{BASE_URL}/v1/galileo/runs/{test_run_id}",
                timeout=10
            )
            result = response.json()
            if result.get('ok'):
                print(f"  OK: Retrieved run details")
            else:
                print(f"  FAIL: {result.get('error')}")
        except Exception as e:
            print(f"  FAIL: {e}")
    else:
        print(f"\n[4/6] SKIPPED (no run_id from test 1)")
    
    # Test 5: POST /v1/galileo/experiments/{id}/run (operator-gated)
    print("\n[5/6] Testing POST /v1/galileo/experiments/{id}/run (authorization gate)...")
    try:
        # Try without operator_key (should be denied)
        response = requests.post(
            f"{BASE_URL}/v1/galileo/experiments/test_exp_id/run",
            timeout=10
        )
        result = response.json()
        if not result.get('ok') and 'authorization' in result.get('error', '').lower():
            print(f"  OK: Operator gate working (denied as expected)")
        else:
            print(f"  WARNING: Expected authorization denial, got: {result.get('error')}")
    except Exception as e:
        print(f"  FAIL: {e}")
    
    # Test 6: GET /v1/galileo/selfcheck
    print("\n[6/6] Testing GET /v1/galileo/selfcheck (determinism verification)...")
    try:
        response = requests.get(
            f"{BASE_URL}/v1/galileo/selfcheck",
            timeout=60
        )
        result = response.json()
        deterministic = result.get('deterministic', False)
        if deterministic:
            print(f"  OK: Determinism verified! (runs produce identical outputs)")
        else:
            print(f"  FAIL: Determinism check failed")
            print(f"       Results: {result.get('selfcheck_results')}")
    except Exception as e:
        print(f"  FAIL: {e}")
    
    print("\n" + "="*70)
    print("TESTS COMPLETE")
    print("="*70)
    
    # Verify storage files exist
    storage_dir = Path(__file__).parent / "data" / "galileo"
    print(f"\n[Storage Check]")
    print(f"  Storage dir: {storage_dir}")
    if storage_dir.exists():
        files = list(storage_dir.glob("*.jsonl"))
        print(f"  JSONL files: {len(files)}")
        for f in files:
            print(f"    - {f.name}")
    else:
        print(f"  Storage dir does not exist")
    
    return True


if __name__ == "__main__":
    test_galileo_endpoints()


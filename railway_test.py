#!/usr/bin/env python3
"""
Railway startup verification script.
Run this to test if the app starts correctly before deployment.
"""

import sys
import traceback
from pathlib import Path

print("=" * 60)
print("RAILWAY STARTUP TEST")
print("=" * 60)


def test_imports():
    """Test critical imports."""
    print("\n1. Testing imports...")
    try:
        import uvicorn

        print("   ✓ uvicorn")
    except ImportError as e:
        print(f"   ✗ uvicorn: {e}")
        return False

    try:
        import fastapi

        print("   ✓ fastapi")
    except ImportError as e:
        print(f"   ✗ fastapi: {e}")
        return False

    try:
        from server import app

        print("   ✓ server:app")
    except Exception as e:
        print(f"   ✗ server:app: {e}")
        traceback.print_exc()
        return False

    return True


def test_paths():
    """Test critical paths exist."""
    print("\n2. Testing paths...")
    paths_to_check = [
        Path("web/index.html"),
        Path("data"),
        Path("server.py"),
        Path("requirements.txt"),
    ]

    all_exist = True
    for p in paths_to_check:
        exists = p.exists()
        symbol = "✓" if exists else "✗"
        print(f"   {symbol} {p}")
        if not exists and str(p) != "data":  # data/ is created on first run
            all_exist = False

    return all_exist


def test_health_endpoint():
    """Test if health endpoint is defined."""
    print("\n3. Testing health endpoint...")
    try:
        from server import app

        routes = [route.path for route in app.routes]

        if "/health" in routes:
            print("   ✓ /health endpoint defined")
            return True
        else:
            print("   ✗ /health endpoint missing")
            print(f"   Available routes: {routes}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking routes: {e}")
        return False


def main():
    tests = [
        ("Imports", test_imports),
        ("Paths", test_paths),
        ("Health Endpoint", test_health_endpoint),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    for name, passed in results.items():
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ All tests passed! Ready for Railway deployment.")
        return 0
    else:
        print("\n❌ Some tests failed. Fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Quick test script for security module functionality."""

import os
os.environ['JWT_SECRET'] = 'test-secret-key-minimum-32-chars-long'

from addons.security import (
    TokenData,
    create_access_token,
    decode_access_token,
    security_status_snapshot,
    append_security_event,
)
from pydantic import ValidationError

def test_token_data_model():
    """Test Pydantic TokenData model."""
    print("Testing TokenData model...")
    td = TokenData(sub='user123', roles=['admin', 'operator'], exp=1234567890)
    assert td.sub == 'user123'
    assert 'admin' in td.roles
    print(f"✓ TokenData model: {td.sub}, roles={td.roles}")

    # Test validation
    try:
        TokenData(sub=123)  # Should fail - sub must be string
        print("✗ Validation should have failed")
    except ValidationError:
        print("✓ Pydantic validation works correctly")

def test_jwt_operations():
    """Test JWT token creation and validation."""
    print("\nTesting JWT operations...")
    token = create_access_token('testuser', ['admin', 'moderator'], 60)
    print(f"✓ Token created: {token[:50]}...")

    decoded = decode_access_token(token)
    assert decoded.sub == 'testuser'
    assert 'admin' in decoded.roles
    print(f"✓ Token decoded: user={decoded.sub}, roles={decoded.roles}")

def test_security_logging():
    """Test security event logging."""
    print("\nTesting security logging...")
    append_security_event("test_event", {"action": "testing", "status": "ok"})
    print("✓ Security event logged")

def test_status_snapshot():
    """Test security status snapshot."""
    print("\nTesting security status snapshot...")
    status = security_status_snapshot(limit_events=5)
    assert 'config' in status
    assert 'recent_events' in status
    print(f"✓ Status snapshot: jwt_configured={status['config']['jwt_configured']}")
    print(f"  Recent events: {len(status['recent_events'])}")

if __name__ == '__main__':
    print("=" * 60)
    print("SWARMZ Security Module Test")
    print("=" * 60)

    test_token_data_model()
    test_jwt_operations()
    test_security_logging()
    test_status_snapshot()

    print("\n" + "=" * 60)
    print("✓ All security module tests passed!")
    print("=" * 60)

"""
SWARMZ Proprietary License
Copyright (c) 2026 SWARMZ. All Rights Reserved.

This software is proprietary and confidential to SWARMZ.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Authorized SWARMZ developers may modify this file solely for contributions
to the official SWARMZ repository. See LICENSE for full terms.
"""

import pytest
from fastapi.testclient import TestClient

# Simplify the import of create_app
from swarmz_runtime.api.server import app


@pytest.fixture
def client():
    """FastAPI TestClient using a fresh app instance."""
    return TestClient(app)

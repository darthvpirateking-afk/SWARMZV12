"""
SWARMZ Proprietary License
Copyright (c) 2026 SWARMZ. All Rights Reserved.

This software is proprietary and confidential to SWARMZ.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Authorized SWARMZ developers may modify this file solely for contributions
to the official SWARMZ repository. See LICENSE for full terms.
"""


def test_initialize_activity_stream(tmp_path, monkeypatch):
    import os
    import json
    from core import activity_stream

    # Patch paths to use temp directory
    monkeypatch.setattr(activity_stream, "EVENTS_FILE", tmp_path / "events.jsonl")
    monkeypatch.setattr(activity_stream, "SESSION_FILE", str(tmp_path / "session.json"))

    activity_stream.initialize_activity_stream()
    assert os.path.exists(tmp_path / "session.json")
    with open(tmp_path / "session.json") as f:
        data = json.load(f)
        assert "session_id" in data
        assert "start_time" in data
        assert "pid" in data

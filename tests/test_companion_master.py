# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_companion_master.py â€” Tests for core/companion_master.py (Commit 4).
"""



def test_ensure_master():
    from core.companion_master import ensure_master
    m = ensure_master()
    assert m["identity"] == "MASTER_SWARMZ"
    assert m["policy"] == "prepare_only"
    assert isinstance(m["total_missions_witnessed"], int)


def test_record_mission_observed():
    from core.companion_master import ensure_master, record_mission_observed
    before = ensure_master()
    count_before = before.get("total_missions_witnessed", 0)
    record_mission_observed("test_m1", "smoke", "SUCCESS", "test summary")
    after = ensure_master()
    assert after["total_missions_witnessed"] == count_before + 1
    assert after["last_mission_id"] == "test_m1"


def test_record_insight():
    from core.companion_master import record_insight, ensure_master
    record_insight("Pattern detected: increasing efficiency")
    m = ensure_master()
    assert "increasing efficiency" in m.get("last_insight", "")


def test_get_composite_context():
    from core.companion_master import get_composite_context
    ctx = get_composite_context()
    assert "master_identity" in ctx
    assert "confidence_level" in ctx
    assert "memory_summary" in ctx
    assert "policy" in ctx
    assert ctx["policy"] == "prepare_only"


def test_self_assessment():
    from core.companion_master import self_assessment
    text = self_assessment()
    assert "MASTER_SWARMZ" in text
    assert "Policy:" in text


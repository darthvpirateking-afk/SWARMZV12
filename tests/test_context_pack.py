# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_context_pack.py â€” Tests for core/context_pack.py (Commit 13).

Integration tests: load engines, before_mission, after_mission, scoreboard.
"""



def test_load_engines():
    from core.context_pack import load
    eng = load()
    assert isinstance(eng, dict)
    # Key engines should be present
    assert "evolution" in eng
    assert "perf_ledger" in eng
    assert "phase" in eng
    assert "trajectory" in eng
    assert "relevance" in eng
    assert "counterfactual" in eng
    assert "world_model" in eng
    assert "divergence" in eng
    assert "entropy" in eng
    assert "companion_master" in eng
    assert "anchor" in eng


def test_before_mission():
    from core.context_pack import before_mission
    ctx = before_mission({"mission_id": "test_bp", "intent": "smoke"})
    assert "strategy" in ctx
    assert "inputs_hash" in ctx
    assert "personality" in ctx
    assert "attention_bundle" in ctx
    assert isinstance(ctx["candidates"], list)


def test_after_mission():
    from core.context_pack import after_mission
    # Should not crash even with minimal data
    after_mission(
        {"mission_id": "test_ap", "intent": "smoke"},
        {"ok": True, "note": "test"},
        runtime_ms=50,
        strategy="baseline",
        inputs_hash="abc",
        candidates=["baseline"],
    )


def test_get_scoreboard():
    from core.context_pack import get_scoreboard
    sb = get_scoreboard()
    assert "timestamp" in sb
    assert "personality" in sb
    assert "read_only" in sb


def test_daily_tick():
    from core.context_pack import daily_tick
    result = daily_tick()
    assert result["ok"] is True
    assert isinstance(result["ran"], list)


def test_companion_selftest():
    """The companion master self-assessment should be deterministic and non-empty."""
    from core.companion_master import self_assessment
    text = self_assessment()
    assert len(text) > 20
    assert "MASTER_SWARMZ" in text
    # Calling again gives same result (deterministic)
    text2 = self_assessment()
    assert text == text2


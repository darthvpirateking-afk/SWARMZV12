# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_ai_audit.py â€” Tests for core/ai_audit.py (Commit 3).
"""



def test_log_model_call():
    from core.ai_audit import log_model_call, tail_ai
    log_model_call(
        provider="test",
        model="test-model",
        ok=True,
        latency_ms=42,
        input_tokens=10,
        output_tokens=20,
        context="unit_test",
    )
    entries = tail_ai(5)
    assert len(entries) >= 1
    last = entries[-1]
    assert last["event"] == "model_call"
    assert last["provider"] == "test"
    assert last["ok"] is True


def test_log_decision():
    from core.ai_audit import log_decision, tail_decisions
    log_decision(
        decision_type="strategy_selection",
        mission_id="test_m1",
        strategy="baseline",
        inputs_hash="abc123",
        rationale="test rationale",
        confidence=0.9,
        source="test",
    )
    entries = tail_decisions(5)
    assert len(entries) >= 1
    last = entries[-1]
    assert last["event"] == "decision"
    assert last["decision_type"] == "strategy_selection"
    assert last["mission_id"] == "test_m1"


def test_sequence_numbers_increment():
    from core.ai_audit import log_model_call, tail_ai
    log_model_call(provider="seq1", model="m", ok=True)
    log_model_call(provider="seq2", model="m", ok=True)
    entries = tail_ai(10)
    seq_entries = [e for e in entries if e.get("provider", "").startswith("seq")]
    if len(seq_entries) >= 2:
        assert seq_entries[-1]["seq"] > seq_entries[-2]["seq"]


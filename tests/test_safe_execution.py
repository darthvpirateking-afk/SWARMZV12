# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_safe_execution.py â€” Tests for core/safe_execution.py + tool_gate.py (Commit 5).
"""

import json
from pathlib import Path


def test_prepare_action_creates_files():
    from core.safe_execution import prepare_action
    path = prepare_action(
        category="commands",
        mission_id="test_safe_1",
        action_data={"cmd": "echo hello"},
        reason="testing safe execution",
        expected_effect={"outcome": "prints hello"},
        risk_level="low",
    )
    p = Path(path)
    assert p.exists()
    assert (p / "proposal.json").exists()
    assert (p / "reason.txt").exists()
    assert (p / "expected_effect.json").exists()
    proposal = json.loads((p / "proposal.json").read_text(encoding="utf-8"))
    assert proposal["category"] == "commands"
    assert proposal["executed"] is False


def test_list_pending():
    from core.safe_execution import list_pending
    items = list_pending("commands")
    assert isinstance(items, list)
    # Should include the item we just created
    ids = [i.get("mission_id") for i in items]
    assert "test_safe_1" in ids


def test_mark_executed():
    from core.safe_execution import mark_executed, list_pending
    path = Path("prepared_actions/commands/test_safe_1")
    assert mark_executed(str(path)) is True
    # Should no longer be in pending list
    items = list_pending("commands")
    ids = [i.get("mission_id") for i in items]
    assert "test_safe_1" not in ids


def test_count_pending():
    from core.safe_execution import count_pending
    counts = count_pending()
    assert isinstance(counts, dict)
    assert "commands" in counts
    assert "messages" in counts


def test_tool_gate():
    from core.tool_gate import gate, is_allowed
    assert is_allowed("shell_command") is True
    result = gate(
        action_type="shell_command",
        payload={"cmd": "ls -la"},
        mission_id="test_gate_1",
        reason="testing gate",
        risk_level="medium",
    )
    assert result["ok"] is True
    assert result["category"] == "commands"
    assert "proposal_dir" in result


def test_tool_gate_message():
    from core.tool_gate import gate
    result = gate(
        action_type="email",
        payload={"to": "test@example.com", "body": "hello"},
        mission_id="test_gate_email",
        reason="testing email gate",
    )
    assert result["ok"] is True
    assert result["category"] == "messages"


def test_tool_gate_purchase():
    from core.tool_gate import gate
    result = gate(
        action_type="purchase",
        payload={"item": "widget", "cost": 9.99},
        mission_id="test_gate_buy",
        reason="testing purchase gate",
        risk_level="high",
    )
    assert result["ok"] is True
    assert result["category"] == "purchases"


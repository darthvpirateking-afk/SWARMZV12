# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Unit tests for DecisionLedger and ContractValidator.
"""

import threading
import tempfile
import os

import pytest

from swarmz_runtime.decision_ledger.decision_ledger import DecisionLedger
from swarmz_runtime.contract_validator.contract_validator import ContractValidator


# ── DecisionLedger ────────────────────────────────────────────────────────────

class TestDecisionLedger:

    def _ledger(self, tmp_path):
        """Return a ledger backed by a temp file."""
        return DecisionLedger(ledger_file=tmp_path / "ledger.jsonl")

    def test_record_returns_entry(self, tmp_path):
        ledger = self._ledger(tmp_path)
        entry = ledger.record("AgentA", "deploy", rationale="test", outcome="success")
        assert entry["agent"] == "AgentA"
        assert entry["action"] == "deploy"
        assert entry["rationale"] == "test"
        assert entry["outcome"] == "success"
        assert "timestamp" in entry

    def test_get_entries_grows(self, tmp_path):
        ledger = self._ledger(tmp_path)
        assert len(ledger) == 0
        ledger.record("AgentA", "ping")
        ledger.record("AgentB", "scan")
        assert len(ledger) == 2
        entries = ledger.get_entries()
        assert len(entries) == 2

    def test_get_entries_is_copy(self, tmp_path):
        ledger = self._ledger(tmp_path)
        ledger.record("AgentA", "ping")
        snapshot = ledger.get_entries()
        snapshot.clear()
        assert len(ledger) == 1  # original unchanged

    def test_get_entries_for_agent(self, tmp_path):
        ledger = self._ledger(tmp_path)
        ledger.record("AgentA", "act1")
        ledger.record("AgentB", "act2")
        ledger.record("AgentA", "act3")
        result = ledger.get_entries_for_agent("AgentA")
        assert len(result) == 2
        assert all(e["agent"] == "AgentA" for e in result)

    def test_get_entries_for_unknown_agent(self, tmp_path):
        ledger = self._ledger(tmp_path)
        ledger.record("AgentA", "ping")
        assert ledger.get_entries_for_agent("Ghost") == []

    def test_metadata_defaults_to_empty_dict(self, tmp_path):
        ledger = self._ledger(tmp_path)
        entry = ledger.record("AgentA", "act")
        assert entry["metadata"] == {}

    def test_outcome_defaults_to_none(self, tmp_path):
        ledger = self._ledger(tmp_path)
        entry = ledger.record("AgentA", "act")
        assert entry["outcome"] is None

    def test_persistence_survives_restart(self, tmp_path):
        """Entries written to disk are re-loaded by a new instance."""
        file_path = tmp_path / "ledger.jsonl"
        ledger1 = DecisionLedger(ledger_file=file_path)
        ledger1.record("AgentA", "deploy", rationale="first")
        ledger1.record("AgentB", "scan")

        # New instance reads same file
        ledger2 = DecisionLedger(ledger_file=file_path)
        assert len(ledger2) == 2
        agents = {e["agent"] for e in ledger2.get_entries()}
        assert agents == {"AgentA", "AgentB"}

    def test_thread_safety(self, tmp_path):
        """Concurrent record() calls must not corrupt the ledger."""
        ledger = self._ledger(tmp_path)
        errors = []

        def worker(agent_id):
            try:
                for _ in range(20):
                    ledger.record(f"Agent{agent_id}", "concurrent_action")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        assert len(ledger) == 100  # 5 threads × 20 records


# ── ContractValidator ─────────────────────────────────────────────────────────

class TestContractValidator:

    def test_valid_contract_passes(self):
        v = ContractValidator()
        ok, reason = v.validate({"agent": "PartnerAgent", "action": "deploy"})
        assert ok is True
        assert reason == "ok"

    def test_missing_agent_fails(self):
        v = ContractValidator()
        ok, reason = v.validate({"action": "deploy"})
        assert ok is False
        assert "agent" in reason

    def test_missing_action_fails(self):
        v = ContractValidator()
        ok, reason = v.validate({"agent": "PartnerAgent"})
        assert ok is False
        assert "action" in reason

    def test_none_agent_fails(self):
        v = ContractValidator()
        ok, reason = v.validate({"agent": None, "action": "deploy"})
        assert ok is False
        assert "agent" in reason

    def test_non_dict_contract_fails(self):
        v = ContractValidator()
        ok, reason = v.validate("not a dict")  # type: ignore[arg-type]
        assert ok is False
        assert "dict" in reason

    def test_empty_dict_fails(self):
        v = ContractValidator()
        ok, reason = v.validate({})
        assert ok is False

    def test_add_custom_rule_pass(self):
        v = ContractValidator()

        def rule_no_test_agent(contract):
            if contract.get("agent") == "TestAgent":
                return False, "TestAgent not allowed in production"
            return True, "ok"

        v.add_rule(rule_no_test_agent)
        ok, reason = v.validate({"agent": "PartnerAgent", "action": "deploy"})
        assert ok is True

    def test_add_custom_rule_fail(self):
        v = ContractValidator()

        def rule_no_test_agent(contract):
            if contract.get("agent") == "TestAgent":
                return False, "TestAgent not allowed in production"
            return True, "ok"

        v.add_rule(rule_no_test_agent)
        ok, reason = v.validate({"agent": "TestAgent", "action": "deploy"})
        assert ok is False
        assert "TestAgent not allowed" in reason

    def test_first_failing_rule_short_circuits(self):
        """Only the first failure reason should be returned."""
        v = ContractValidator()
        called = []

        def rule_a(contract):
            called.append("a")
            return False, "rule_a failed"

        def rule_b(contract):
            called.append("b")
            return False, "rule_b failed"

        v.add_rule(rule_a)
        v.add_rule(rule_b)

        ok, reason = v.validate({"agent": "X", "action": "Y"})
        assert ok is False
        assert reason == "rule_a failed"
        assert "b" not in called  # rule_b was never reached

    def test_extra_fields_are_allowed(self):
        v = ContractValidator()
        ok, reason = v.validate({"agent": "A", "action": "B", "extra": "ignored"})
        assert ok is True

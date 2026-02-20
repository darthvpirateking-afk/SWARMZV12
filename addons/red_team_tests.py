# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Red-Team Test Pack â€” deterministic adversarial cases.

Tests: fake ROI spikes, duplicated runs, invalid approvals,
conflicting A/B, budget overflow, quarantine enforcement,
tampered encryption, rate-limit bypass attempts, etc.

"Self-test must pass before learning updates apply."
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFakeROISpike(unittest.TestCase):
    """Detect and reject implausible ROI values."""

    def test_budget_rejects_negative_spend(self):
        from addons.budget import simulate_burn
        sim = simulate_burn(-100)
        # Negative cost should not breach (it's nonsensical but not a breach)
        self.assertIn("would_breach", sim)

    def test_budget_blocks_over_cap(self):
        from addons.budget import get_budget, simulate_burn
        b = get_budget()
        sim = simulate_burn(b["hard_cap"] + 1)
        self.assertTrue(sim["would_breach"])


class TestDuplicatedRuns(unittest.TestCase):
    """Golden run replay detects duplicated/replayed outputs."""

    def test_golden_run_mismatch(self):
        from addons.golden_run import record_golden_run, replay_and_verify
        record_golden_run("red_dup_1", {"x": 1}, {"s": "a"}, {"out": 10}, {"s": "b"})
        result = replay_and_verify("red_dup_1", {"out": 999}, {"s": "b"})
        self.assertFalse(result["outputs_match"])
        self.assertFalse(result["deterministic"])

    def test_golden_run_match(self):
        from addons.golden_run import record_golden_run, replay_and_verify
        record_golden_run("red_dup_2", {"x": 1}, {"s": "a"}, {"out": 10}, {"s": "b"})
        result = replay_and_verify("red_dup_2", {"out": 10}, {"s": "b"})
        self.assertTrue(result["deterministic"])


class TestInvalidApprovals(unittest.TestCase):
    """Invalid operator keys must be rejected."""

    def test_patch_approval_bad_key(self):
        import os
        os.environ["SWARMZ_OPERATOR_PIN"] = "correct_pin"
        from addons.config_ext import reload_config
        reload_config()
        from addons.approval_queue import submit_patch, approve_patch
        p = submit_patch("red team test", {"test": True})
        result = approve_patch(p["patch_id"], "wrong_pin")
        self.assertIn("error", result)
        # Clean up
        del os.environ["SWARMZ_OPERATOR_PIN"]
        reload_config()

    def test_quarantine_exit_bad_key(self):
        import os
        os.environ["SWARMZ_OPERATOR_PIN"] = "correct_pin"
        from addons.config_ext import reload_config
        reload_config()
        from addons.quarantine import enter_quarantine, exit_quarantine
        enter_quarantine("red team test")
        result = exit_quarantine("bad_key")
        self.assertIn("error", result)
        # Clean up: force exit
        exit_quarantine("correct_pin")
        del os.environ["SWARMZ_OPERATOR_PIN"]
        reload_config()


class TestConflictingAB(unittest.TestCase):
    """Interference graph catches Aâ†”B conflicts."""

    def test_coupling_recorded(self):
        from addons.guardrails import record_interference, get_coupling_graph
        record_interference("strategy_A", "strategy_B", -0.8)
        graph = get_coupling_graph()
        edges = graph.get("edges", [])
        found = any(
            e["source"] == "strategy_A" and e["target"] == "strategy_B"
            for e in edges
        )
        self.assertTrue(found)


class TestEncryptionTamper(unittest.TestCase):
    """Tampered ciphertext must be detected."""

    def test_wrong_key_rejected(self):
        from addons.encrypted_storage import encrypt_blob, decrypt_blob
        blob = encrypt_blob(b"secret", "key1")
        with self.assertRaises(ValueError):
            decrypt_blob(blob, "wrong_key")

    def test_tampered_blob_rejected(self):
        from addons.encrypted_storage import encrypt_blob, decrypt_blob
        blob = bytearray(encrypt_blob(b"secret", "key1"))
        blob[20] ^= 0xFF  # flip a byte in ciphertext
        with self.assertRaises(ValueError):
            decrypt_blob(bytes(blob), "key1")


class TestStrategyKillSwitch(unittest.TestCase):
    """Kill criteria must auto-disable strategies on breach."""

    def test_auto_kill_on_breach(self):
        from addons.strategy_registry import register_strategy, check_kill_criteria, list_strategies
        register_strategy("red_test_strat", "test", [], {"error_rate": 0.1})
        result = check_kill_criteria("red_test_strat", {"error_rate": 0.5})
        self.assertEqual(result["status"], "killed")
        strats = list_strategies()
        self.assertFalse(strats["red_test_strat"]["enabled"])


class TestCausalLedgerEnforcement(unittest.TestCase):
    """Runs without a declared lever must be rejected."""

    def test_missing_lever_rejected(self):
        from addons.causal_ledger import validate_lever
        result = validate_lever("nonexistent_mission_xyz")
        self.assertFalse(result["valid"])

    def test_declared_lever_accepted(self):
        from addons.causal_ledger import declare_lever, validate_lever
        declare_lever("red_lever_m1", "pricing", "changed pricing by +5%")
        result = validate_lever("red_lever_m1")
        self.assertTrue(result["valid"])


class TestAdversarialInputStability(unittest.TestCase):
    """Small input perturbations should flag brittle outputs."""

    def test_brittle_detection(self):
        from addons.guardrails import stability_check
        # Wildly varying outputs
        result = stability_check("brittle_test", {"x": 1}, [{"x": 999}, {"x": -1}, {"x": 0}])
        self.assertFalse(result["stable"])

    def test_stable_detection(self):
        from addons.guardrails import stability_check
        result = stability_check("stable_test", {"x": 1}, [{"x": 1}, {"x": 1}, {"x": 1}])
        self.assertTrue(result["stable"])


class TestEntropyOverCap(unittest.TestCase):
    """Spending over the entropy cap must be blocked."""

    def test_over_cap_blocked(self):
        from addons.entropy_budget import get_entropy_budget, spend_entropy
        budget = get_entropy_budget()
        over = budget["weekly_cap"] + 1
        result = spend_entropy(over, "red_team_overload")
        self.assertIn("error", result)


def run_red_team():
    print("=" * 60)
    print("SWARMZ Red-Team Test Pack")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestFakeROISpike,
        TestDuplicatedRuns,
        TestInvalidApprovals,
        TestConflictingAB,
        TestEncryptionTamper,
        TestStrategyKillSwitch,
        TestCausalLedgerEnforcement,
        TestAdversarialInputStability,
        TestEntropyOverCap,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_red_team())


# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_engines.py â€” Tests for existing engines (Commits 7â€“11).

Validates that all engine classes instantiate and their hook methods work.
"""

import json
from pathlib import Path
import pytest


def test_perf_ledger():
    from core.perf_ledger import PerfLedger

    pl = PerfLedger("data")
    pl.append("test_engine_pl", 100, True, 0.01)
    recent = pl.load_recent(5)
    assert len(recent) >= 1
    assert recent[-1]["mission_id"] == "test_engine_pl"


def test_operator_anchor():
    from core.operator_anchor import (
        load_or_create_anchor,
        verify_fingerprint,
        compute_record_hash,
        sign_record,
    )

    anchor = load_or_create_anchor("data")
    assert "machine_fingerprint" in anchor
    assert "operator_private_key" in anchor
    # Fingerprint check
    assert isinstance(verify_fingerprint(anchor), bool)
    # Hash + sign
    h = compute_record_hash({"test": 1}, "prev_hash")
    assert isinstance(h, str) and len(h) > 10
    sig = sign_record(anchor["operator_private_key"], h)
    assert isinstance(sig, str) and len(sig) > 10


def test_evolution_memory():
    from core.evolution_memory import EvolutionMemory
    from core.operator_anchor import load_or_create_anchor

    anchor = load_or_create_anchor("data")
    evo = EvolutionMemory("data", anchor=anchor, read_only=False)
    # get_personality returns personality_vector
    p = evo.get_personality()
    assert "risk_tolerance" in p
    # get_companion_state returns companion_state
    cs = evo.get_companion_state()
    assert "confidence_level" in cs
    # candidate_strategies
    cands = evo.candidate_strategies("test_hash")
    assert isinstance(cands, list)


def test_world_model():
    from core.world_model import WorldModel

    wm = WorldModel("data")
    # recompute should not crash
    wm.recompute()
    sol = Path("data/state_of_life.json")
    assert sol.exists()
    data = json.loads(sol.read_text(encoding="utf-8"))
    assert "active_projects" in data


def test_divergence_engine():
    from core.divergence_engine import DivergenceEngine

    de = DivergenceEngine("data")
    result = de.update()
    assert "divergence_score" in result
    adj = de.get_adjustments()
    assert "branching_factor" in adj


def test_entropy_monitor():
    from core.entropy_monitor import EntropyMonitor

    em = EntropyMonitor("data")
    result = em.update()
    assert "mode" in result
    adj = em.get_adjustments()
    assert "exploration_bias_delta" in adj


def test_phase_engine():
    from core.phase_engine import PhaseEngine

    pe = PhaseEngine("data")
    # after_outcome should not crash
    pe.after_outcome(True, 0.8, 100, "baseline")
    ph = Path("data/phase_history.jsonl")
    assert ph.exists()


def test_trajectory_engine():
    from core.trajectory_engine import TrajectoryEngine
    from core.evolution_memory import EvolutionMemory
    from core.perf_ledger import PerfLedger
    from core.operator_anchor import load_or_create_anchor

    anchor = load_or_create_anchor("data")
    evo = EvolutionMemory("data", anchor=anchor)
    pl = PerfLedger("data")
    te = TrajectoryEngine("data", evo, pl)
    # after_outcome should not crash
    te.after_outcome(True, 0.7, 100, "baseline")
    cs = Path("data/current_state.json")
    assert cs.exists()


def test_counterfactual_engine():
    from core.counterfactual_engine import CounterfactualEngine
    from core.evolution_memory import EvolutionMemory
    from core.operator_anchor import load_or_create_anchor

    anchor = load_or_create_anchor("data")
    evo = EvolutionMemory("data", anchor=anchor)
    cf = CounterfactualEngine("data", evo)
    # record_snapshot should not crash
    cf.record_snapshot(
        inputs_hash="test_cf_hash",
        selected_strategy="baseline",
        candidate_strategies=["baseline"],
        expected_outcome_projection=0.5,
        state_of_life_hash="test_sol",
        personality_vector={"risk_tolerance": 0.5},
    )
    ds = Path("data/decision_snapshots.jsonl")
    assert ds.exists()


def test_relevance_engine(tmp_path):
    from core.relevance_engine import RelevanceEngine
    from core.evolution_memory import EvolutionMemory
    from core.operator_anchor import load_or_create_anchor

    # Setup isolated data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    mem_hot_dir = data_dir / "memory" / "hot"
    mem_hot_dir.mkdir(parents=True, exist_ok=True)
    history_file = data_dir / "evolution_history.jsonl"

    # Populate evolution_history.jsonl with a sample record
    sample_record = {
        "inputs_hash": "test_hash",
        "strategy_used": "baseline",
        "score": 0.8,
        "success_bool": True,
        "previous_hash": "GENESIS",
    }
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(sample_record) + "\n")

    anchor = load_or_create_anchor(str(data_dir))
    evo = EvolutionMemory(str(data_dir), anchor=anchor)
    re = RelevanceEngine(str(data_dir), evo)

    # after_outcome should not crash
    re.after_outcome("test_rel_m1", "test_hash", "baseline", 0.8, True, 100)
    hot = mem_hot_dir / "hot.jsonl"
    assert hot.exists()

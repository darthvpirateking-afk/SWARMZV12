"""
NEXUSMON Phase 15 — Operator Rank System Tests

Run: python -m pytest test_operator_rank.py -v
"""

import json
import os
import tempfile
import pytest

# Patch DATA_DIR before import
_test_dir = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _test_dir

from nexusmon_operator_rank import (
    rank_from_xp,
    next_rank_info,
    traits_for_xp,
    has_permission,
    award_xp,
    get_operator_rank_state,
    tier_from_rank,
    RANKS,
    RANK_THRESHOLDS,
    XP_TABLE,
    RANK_TRAITS,
    PERMISSION_MATRIX,
    RANK_FILE,
    EVOLUTION_TIERS,
    RANK_TO_TIER,
    _save_state,
    _load_state,
    _default_state,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_state():
    """Reset operator state before each test."""
    _save_state(_default_state())
    yield
    if os.path.exists(RANK_FILE):
        os.remove(RANK_FILE)


# ─── rank_from_xp ───────────────────────────────────────────────────────────

class TestRankFromXP:
    def test_zero_xp_is_rank_e(self):
        assert rank_from_xp(0) == "E"

    def test_49_xp_is_rank_e(self):
        assert rank_from_xp(49) == "E"

    def test_50_xp_is_rank_d(self):
        assert rank_from_xp(50) == "D"

    def test_149_xp_is_rank_d(self):
        assert rank_from_xp(149) == "D"

    def test_150_xp_is_rank_c(self):
        assert rank_from_xp(150) == "C"

    def test_399_xp_is_rank_c(self):
        assert rank_from_xp(399) == "C"

    def test_400_xp_is_rank_b(self):
        assert rank_from_xp(400) == "B"

    def test_799_xp_is_rank_b(self):
        assert rank_from_xp(799) == "B"

    def test_800_xp_is_rank_a(self):
        assert rank_from_xp(800) == "A"

    def test_1499_xp_is_rank_a(self):
        assert rank_from_xp(1499) == "A"

    def test_1500_xp_is_rank_s(self):
        assert rank_from_xp(1500) == "S"

    def test_huge_xp_is_rank_s(self):
        assert rank_from_xp(999999) == "S"

    def test_negative_xp_is_rank_e(self):
        assert rank_from_xp(-10) == "E"


# ─── next_rank_info ──────────────────────────────────────────────────────────

class TestNextRankInfo:
    def test_rank_e_next_is_d(self):
        info = next_rank_info(0)
        assert info["next_rank"] == "D"
        assert info["xp_needed"] == 50

    def test_rank_s_no_next(self):
        info = next_rank_info(1500)
        assert info["next_rank"] is None
        assert info["progress"] == 1.0

    def test_midway_progress(self):
        info = next_rank_info(25)  # halfway E→D
        assert info["next_rank"] == "D"
        assert info["xp_needed"] == 25
        assert info["progress"] == 0.5

    def test_exact_boundary(self):
        info = next_rank_info(50)  # exactly at D
        assert info["next_rank"] == "C"
        assert info["xp_needed"] == 100


# ─── traits_for_xp ──────────────────────────────────────────────────────────

class TestTraits:
    def test_rank_e_no_traits(self):
        assert traits_for_xp(0) == []

    def test_rank_d_traits(self):
        traits = traits_for_xp(50)
        assert "Worker Control" in traits
        assert "Artifact Review" in traits

    def test_rank_c_includes_d_traits(self):
        traits = traits_for_xp(150)
        assert "Worker Control" in traits   # from D
        assert "Evolution Sync" in traits   # from C

    def test_rank_s_has_all_traits(self):
        traits = traits_for_xp(1500)
        assert "Organism Override" in traits
        assert len(traits) == sum(len(v) for v in RANK_TRAITS.values())


# ─── has_permission ──────────────────────────────────────────────────────────

class TestPermissions:
    def test_rank_e_can_run_e_mission(self):
        assert has_permission(0, "run_mission_E") is True

    def test_rank_e_cannot_run_d_mission(self):
        assert has_permission(0, "run_mission_D") is False

    def test_rank_d_can_approve_artifact(self):
        assert has_permission(50, "approve_artifact") is True

    def test_rank_e_cannot_approve_artifact(self):
        assert has_permission(0, "approve_artifact") is False

    def test_rank_c_can_approve_mission(self):
        assert has_permission(150, "approve_mission") is True

    def test_rank_b_can_activate_module(self):
        assert has_permission(400, "activate_module") is True

    def test_rank_s_can_do_everything(self):
        for action in PERMISSION_MATRIX:
            assert has_permission(1500, action) is True

    def test_unknown_action_is_allowed(self):
        assert has_permission(0, "some_future_action") is True


# ─── award_xp ───────────────────────────────────────────────────────────────

class TestAwardXP:
    def test_award_basic_xp(self):
        result = award_xp("complete_mission_E", "test mission")
        assert result["awarded"] == 10
        assert result["total_xp"] == 10
        assert result["rank"] == "E"
        assert result["ranked_up"] is False

    def test_award_triggers_rank_up(self):
        state = _load_state()
        state["xp"] = 45
        _save_state(state)

        result = award_xp("complete_mission_E")  # +10 → 55
        assert result["ranked_up"] is True
        assert result["old_rank"] == "E"
        assert result["new_rank"] == "D"
        assert "Worker Control" in result["new_traits"]

    def test_award_unknown_action(self):
        result = award_xp("nonexistent_action")
        assert result["awarded"] == 0

    def test_xp_history_recorded(self):
        award_xp("complete_mission_E", "first")
        award_xp("approve_artifact", "second")
        state = _load_state()
        assert len(state["xp_history"]) == 2
        assert state["xp_history"][0]["action"] == "complete_mission_E"
        assert state["xp_history"][1]["action"] == "approve_artifact"

    def test_xp_history_capped_at_100(self):
        state = _load_state()
        state["xp_history"] = [{"action": "test", "xp": 1, "timestamp": 0.0}] * 99
        _save_state(state)
        award_xp("complete_mission_E")
        state = _load_state()
        assert len(state["xp_history"]) == 100


# ─── get_operator_rank_state ─────────────────────────────────────────────────

class TestGetState:
    def test_initial_state(self):
        state = get_operator_rank_state()
        assert state["rank"] == "E"
        assert state["xp"] == 0
        assert state["next_rank"] == "D"
        assert state["xp_needed"] == 50
        assert state["traits"] == []
        assert state["permissions"]["run_mission_E"] is True
        assert state["permissions"]["approve_artifact"] is False

    def test_state_after_xp(self):
        award_xp("complete_mission_C")  # +50
        state = get_operator_rank_state()
        assert state["rank"] == "D"
        assert state["xp"] == 50
        assert "Worker Control" in state["traits"]
        assert state["permissions"]["approve_artifact"] is True


# ─── Evolution tier ──────────────────────────────────────────────────────────

class TestEvolutionTier:
    def test_rank_e_is_dormant(self):
        assert tier_from_rank("E") == "DORMANT"

    def test_rank_d_is_initiated(self):
        assert tier_from_rank("D") == "INITIATED"

    def test_rank_c_is_active(self):
        assert tier_from_rank("C") == "ACTIVE"

    def test_rank_b_is_evolved(self):
        assert tier_from_rank("B") == "EVOLVED"

    def test_rank_a_is_ascended(self):
        assert tier_from_rank("A") == "ASCENDED"

    def test_rank_s_is_ascended(self):
        assert tier_from_rank("S") == "ASCENDED"

    def test_all_ranks_have_tier(self):
        for rank in RANKS:
            assert tier_from_rank(rank) in EVOLUTION_TIERS

    def test_unknown_rank_defaults_dormant(self):
        assert tier_from_rank("Z") == "DORMANT"


# ─── Storage resilience ──────────────────────────────────────────────────────

class TestStorage:
    def test_corrupted_file_returns_default(self):
        with open(RANK_FILE, "w") as f:
            f.write("{{{bad json")
        state = _load_state()
        assert state["xp"] == 0

    def test_missing_file_returns_default(self):
        if os.path.exists(RANK_FILE):
            os.remove(RANK_FILE)
        state = _load_state()
        assert state["xp"] == 0


# ─── XP table completeness ──────────────────────────────────────────────────

class TestXPTable:
    def test_all_mission_ranks_have_xp(self):
        for rank in RANKS:
            key = f"complete_mission_{rank}"
            assert key in XP_TABLE, f"Missing XP entry for {key}"

    def test_all_xp_values_positive(self):
        for action, xp in XP_TABLE.items():
            assert xp > 0, f"XP for {action} should be positive"

    def test_all_permission_actions_exist(self):
        for action in PERMISSION_MATRIX:
            required_rank = PERMISSION_MATRIX[action]
            assert required_rank in RANKS, f"{action} maps to unknown rank {required_rank}"

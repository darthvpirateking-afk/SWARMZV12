from __future__ import annotations

from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix


def _force_rank(matrix: AvatarMatrix, rank: str) -> None:
    matrix.rank_system.current_rank = rank

    def _refresh() -> str:
        matrix.rank_system.current_rank = rank
        return rank

    matrix.rank_system.refresh_rank = _refresh  # type: ignore[method-assign]


def test_monarch_requires_sovereign_form() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_rank(matrix, "Sovereign")

    blocked = matrix.handle_operator_command("MONARCH")
    assert blocked["ok"] is True
    assert blocked["transitioned"] is False
    assert matrix.current_form == "AvatarOmega"


def test_monarch_enter_exit_and_summon_visibility() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_rank(matrix, "Sovereign")

    assert matrix.handle_operator_command("SOVEREIGN")["transitioned"] is True
    entered = matrix.handle_operator_command("MONARCH")
    assert entered["ok"] is True
    assert entered["transitioned"] is True
    assert matrix.current_form == "AvatarMonarch"

    monarch_state = matrix.get_monarch_state()
    assert monarch_state["active"] is True
    assert len(monarch_state["summons"]) == 4

    returned = matrix.handle_operator_command("RETURN")
    assert returned["ok"] is True
    assert returned["transitioned"] is True
    assert matrix.current_form == "AvatarSovereign"
    assert matrix.get_monarch_state()["active"] is False


def test_monarch_abilities_only_when_monarch_active() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_rank(matrix, "Sovereign")

    baseline = matrix.get_matrix_state()["abilities"]["unlocked"]
    assert "Abyssal Rend" not in baseline
    assert "Cosmic Rift" not in baseline

    matrix.handle_operator_command("SOVEREIGN")
    matrix.handle_operator_command("MONARCH")
    boosted = matrix.get_matrix_state()["abilities"]["unlocked"]
    assert "Abyssal Rend" in boosted
    assert "Cosmic Rift" in boosted

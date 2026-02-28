from __future__ import annotations

from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix


def _force_rank(matrix: AvatarMatrix, rank: str) -> None:
    matrix.rank_system.current_rank = rank

    def _refresh() -> str:
        matrix.rank_system.current_rank = rank
        return rank

    matrix.rank_system.refresh_rank = _refresh  # type: ignore[method-assign]


def test_transition_commands_route_through_operator_link() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_rank(matrix, "Sovereign")

    ascend = matrix.handle_operator_command("ASCEND")
    assert ascend["ok"] is True
    assert ascend["transitioned"] is True
    assert matrix.current_form == "AvatarInfinity"

    sovereign = matrix.handle_operator_command("SOVEREIGN")
    assert sovereign["ok"] is True
    assert sovereign["transitioned"] is True
    assert matrix.current_form == "AvatarSovereign"

    monarch = matrix.handle_operator_command("MONARCH")
    assert monarch["ok"] is True
    assert monarch["transitioned"] is True
    assert matrix.current_form == "AvatarMonarch"

    returned = matrix.handle_operator_command("RETURN")
    assert returned["ok"] is True
    assert returned["transitioned"] is True
    assert matrix.current_form == "AvatarSovereign"


def test_chip_commands_route_through_operator_link() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_rank(matrix, "Sovereign")
    matrix.handle_operator_command("SOVEREIGN")

    chip = matrix.handle_operator_command("CHIP Dimensional Tear")
    assert chip["ok"] is True
    assert chip["executed"] is True
    assert chip["chip_result"]["chip"] == "Dimensional Tear"

    burst = matrix.handle_operator_command("BURST")
    assert burst["ok"] is True
    assert "chip_result" in burst

    chain = matrix.handle_operator_command("CHAIN")
    assert chain["ok"] is True
    assert chain["chip_result"]["mode"] == "CHAIN"


def test_unknown_command_is_rejected() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    result = matrix.handle_operator_command("NOT_A_REAL_COMMAND")
    assert result["ok"] is False

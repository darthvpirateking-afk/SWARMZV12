"""SpawnContext least-privilege tests."""
from __future__ import annotations

import pytest

from core.spawn_context import MAX_SPAWN_DEPTH, SpawnContext


def test_root_context_defaults() -> None:
    root = SpawnContext.root(frozenset({"data.read", "agent.introspect"}), session_id="s1")
    assert root.session_id == "s1"
    assert root.depth == 0
    assert root.parent_agent_id is None


def test_spawn_child_enforces_least_privilege() -> None:
    root = SpawnContext.root(frozenset({"data.read", "agent.introspect"}), session_id="s1")
    child = root.spawn_child("helper1", frozenset({"data.read", "agent.spawn"}), max_depth=3)
    assert child.depth == 1
    assert child.capabilities_granted == frozenset({"data.read"})
    assert child.provenance == ("helper1",)


def test_spawn_depth_limit_enforced() -> None:
    ctx = SpawnContext.root(frozenset({"data.read"}), session_id="s1")
    level1 = ctx.spawn_child("a", frozenset({"data.read"}), max_depth=1)
    with pytest.raises(PermissionError):
        level1.spawn_child("b", frozenset({"data.read"}), max_depth=1)


def test_hard_ceiling_applied() -> None:
    ctx = SpawnContext.root(frozenset({"data.read"}), session_id="s1")
    current = ctx
    for idx in range(MAX_SPAWN_DEPTH):
        current = current.spawn_child(f"child-{idx}", frozenset({"data.read"}), max_depth=999)
    with pytest.raises(PermissionError):
        current.spawn_child("too-deep", frozenset({"data.read"}), max_depth=999)

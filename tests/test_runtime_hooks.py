from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from runtime.events import EVENT_BUS
from runtime.hooks import RuntimeHookDispatcher

ROOT = Path(__file__).resolve().parents[1]


def _rebuild_manifest_registry() -> None:
    subprocess.run(
        [sys.executable, "scripts/build_manifest_registry.py"],
        cwd=ROOT,
        check=True,
    )


@pytest.fixture(scope="module", autouse=True)
def manifest_registry_ready() -> None:
    _rebuild_manifest_registry()


def _payload(context: str) -> dict:
    return {
        "context": context,
        "ritual_confirmation": {"confirmed": True, "source": "pytest"},
    }


def test_runtime_dispatches_all_hook_types_symbolic() -> None:
    dispatcher = RuntimeHookDispatcher()
    hook_aliases = [
        "invoke",
        "consult",
        "interpret",
        "generate_geometry",
        "trigger_anomaly",
        "resolve_correspondence",
        "render_altar_mode",
        "simulate_branch",
    ]
    for hook in hook_aliases:
        result = dispatcher.dispatch(
            hook=hook,
            system_id="pantheons-root",
            payload=_payload(hook),
            operator_approved=True,
        )
        assert result["symbolic_only"] is True
        assert result["non_supernatural"] is True
        assert result["lane"] == "symbolic"


def test_runtime_requires_operator_approval() -> None:
    dispatcher = RuntimeHookDispatcher()
    with pytest.raises(PermissionError):
        dispatcher.dispatch(
            hook="consult",
            system_id="pantheons-root",
            payload=_payload("gate-check"),
            operator_approved=False,
        )


def test_runtime_requires_ritual_confirmation() -> None:
    dispatcher = RuntimeHookDispatcher()
    with pytest.raises(ValueError):
        dispatcher.dispatch(
            hook="consult",
            system_id="pantheons-root",
            payload={"context": "missing-ritual"},
            operator_approved=True,
        )


def test_event_bus_receives_hook_events() -> None:
    dispatcher = RuntimeHookDispatcher()
    dispatcher.dispatch(
        hook="consult",
        system_id="pantheons-root",
        payload=_payload("event-bus"),
        operator_approved=True,
    )
    history = EVENT_BUS.history(50)
    assert any(
        e.event_type == "consult" and e.payload.get("system_id") == "pantheons-root"
        for e in history
    )

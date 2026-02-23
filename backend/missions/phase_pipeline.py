from __future__ import annotations

from typing import Any

from backend.observability.mission_debugger import MissionDebugger, TraceEvent, get_debugger_config
from backend.runner.vpn_provisioner import (
    VPNNode,
    guaranteed_destroy_vpn_node,
    get_vpn_config,
    provision_vpn_node,
)


PHASES = ["SETUP", "RECON", "EXECUTE", "REPORT", "CLEANUP"]


def run_phase_pipeline(
    mission_id: str,
    autonomy: int,
    protectiveness: int,
    patience: int,
    fail: bool = False,
) -> dict[str, Any]:
    vpn_node: VPNNode | None = None
    debugger_cfg = get_debugger_config(patience=patience, protectiveness=protectiveness)
    debugger = MissionDebugger(mission_id=mission_id, patience=patience, protectiveness=protectiveness)

    status = "SUCCESS"
    visited: list[str] = []

    try:
        vpn_cfg = get_vpn_config(protectiveness=protectiveness, autonomy=autonomy)
        if vpn_cfg.get("auto_provision_before_ops"):
            provider = vpn_cfg.get("preferred_providers", ["linode"])[0]
            region = vpn_cfg.get("preferred_regions", ["auto"])[0]
            vpn_node = provision_vpn_node(provider, region, protectiveness=protectiveness, mission_id=mission_id)

        for phase in PHASES[:-1]:
            visited.append(phase)
            if debugger.active:
                debugger.record(TraceEvent(event_type="call", function=f"phase_{phase.lower()}", module="phase_pipeline"))
            if fail and phase == "EXECUTE":
                raise RuntimeError("Simulated mission failure")

    except Exception as exc:
        status = "FAILED"
        if debugger_cfg.get("auto_activate_on_fail"):
            debugger.activate()
            debugger.record(
                TraceEvent(
                    event_type="exception",
                    function="run_phase_pipeline",
                    module="phase_pipeline",
                    exception=str(exc),
                )
            )
    finally:
        visited.append("CLEANUP")
        guaranteed_destroy_vpn_node(vpn_node)
        if debugger.active and debugger_cfg.get("export_trace"):
            debugger.export_trace(path=f"data/debug/{mission_id}_trace.json")

    return {
        "mission_id": mission_id,
        "status": status,
        "phases": visited,
        "vpn_destroyed": vpn_node.destroyed if vpn_node else True,
        "debugger_active": debugger.active,
    }

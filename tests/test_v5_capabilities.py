from __future__ import annotations

from backend.agent.mission_planner import build_setup_context
from backend.entity.trait_drift_detector import TraitBehaviorSample, detect_drift
from backend.intel.api_attack_engine import APIEndpoint, fuzz_endpoint
from backend.intel.browser_recon import (
    BrowserReconResult,
    extract_attack_surface,
    get_browser_recon_config,
)
from backend.intel.network_flow_analyzer import (
    NetworkFlow,
    analyze_flow,
    should_delete_pcap_after_retention,
    should_store_pcap,
)
from backend.intel.secret_scanner import scan_file
from backend.intelligence.feature_store import Feature, get_feature, set_feature
from backend.observability.mission_debugger import MissionDebugger, TraceEvent
from backend.runner.vm_provisioner import get_vm_config, provision_vm
from backend.runner.vpn_provisioner import (
    guaranteed_destroy_vpn_node,
    provision_vpn_node,
)


def test_browser_recon_is_always_headless() -> None:
    cfg = get_browser_recon_config(curiosity=80, creativity=80, patience=80)
    assert cfg["headless"] is True


def test_extract_attack_surface_auth_candidates() -> None:
    result = BrowserReconResult(
        url="https://target.local",
        dom_snapshot="<html></html>",
        network_calls=[{"url": "https://target.local/api/users"}],
        forms=[{"action": "/login", "csrf_token": ""}],
    )
    surface = extract_attack_surface(result, aggression=40)
    assert surface["endpoints"]
    assert surface["auth_bypass_candidates"]


def test_network_flow_flags_and_pcap_rules() -> None:
    flow = NetworkFlow(
        flow_id="f1",
        src_ip="10.0.0.2",
        dst_ip="203.0.113.8",
        src_port=5555,
        dst_port=53,
        protocol="dns",
        start_time=0.0,
        end_time=1.0,
        bytes_sent=12_000_000,
        bytes_recv=100,
        payload_preview="x" * 120,
        flags=[],
    )
    flags = analyze_flow(flow, baseline={"known_hosts": ["10.0.0.1"]})
    assert "exfil_pattern" in flags
    assert should_store_pcap(40) is False
    assert should_store_pcap(60) is True
    assert should_delete_pcap_after_retention() is True


def test_secret_scanner_redacts_value_preview() -> None:
    content = "token = ghp_abcdefghijklmnopqrstuvwxyz1234567890"
    findings = scan_file("a.py", content, curiosity=70, aggression=30)
    assert findings
    for finding in findings:
        assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in finding.value_preview


def test_vm_provisioner_enforces_network_isolation() -> None:
    vm = provision_vm(
        "windows_server_2019", creativity=70, patience=80, protectiveness=80
    )
    cfg = get_vm_config(creativity=70, patience=80, protectiveness=80)
    assert vm["network_mode"] == "isolated"
    assert vm["network_isolation_required"] is True
    assert cfg["network_isolation_required"] is True


def test_api_fuzz_generates_results() -> None:
    endpoint = APIEndpoint(
        path="/users", method="GET", parameters=[], auth="none", schema={}
    )
    results = fuzz_endpoint(endpoint, strategy="idor", aggression=70)
    assert results


def test_feature_store_set_and_get() -> None:
    store: dict[str, dict[str, Feature]] = {}
    feat = Feature(
        name="cves_known", value=["CVE-2021-44228"], target_id="target-1", ttl_hours=24
    )
    set_feature("target-1", feat, store)
    loaded = get_feature("target-1", "cves_known", store)
    assert loaded is not None


def test_trait_drift_detector_alerts() -> None:
    samples = [
        TraitBehaviorSample(
            trait="autonomy",
            nominal_value=40,
            behavior_metric="auto_decisions_per_mission",
            observed_value=18.0,
            mission_id="m1",
        )
    ]
    alerts = detect_drift(samples, traits={"autonomy": 40})
    assert alerts


def test_vpn_non_negotiable_destroy() -> None:
    node = provision_vpn_node("linode", "auto", protectiveness=80, mission_id="m1")
    assert guaranteed_destroy_vpn_node(node) is True
    assert node.destroyed is True


def test_mission_debugger_off_by_default_and_trace() -> None:
    debugger = MissionDebugger(mission_id="m1", patience=60, protectiveness=70)
    assert debugger.active is False
    debugger.activate()
    debugger.record(TraceEvent(event_type="call", function="plan", module="planner"))
    assert debugger.get_call_graph()


def test_build_setup_context_includes_vpn_debugger() -> None:
    ctx = build_setup_context(
        target_id="target-1",
        autonomy=70,
        protectiveness=80,
        patience=70,
        curiosity=70,
    )
    assert "vpn" in ctx
    assert "debugger" in ctx

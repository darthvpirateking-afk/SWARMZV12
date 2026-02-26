from __future__ import annotations

from backend.agent.mission_planner import get_mission_guidance
from backend.agent.tool_selector import build_pre_attack_intel
from backend.intel.default_creds import is_default_credential
from backend.intel.vuln_db_client import search_vulnerabilities
from backend.reporting.report_builder import get_cve_report_section
from backend.runner.resource_budget import enforce_budget, get_resource_budget
from backend.runner.shell_executor import CommandGuardBlocked, run_shell_command
from backend.security.shell_linter import lint_shell_command, should_block


def test_vuln_db_lookup_returns_known_cve() -> None:
    findings = search_vulnerabilities(["log4j"], minimum_severity="high")
    assert findings
    assert findings[0]["cve_id"] == "CVE-2021-44228"


def test_default_credential_match() -> None:
    assert is_default_credential("admin", "admin", product="jenkins") is True


def test_shell_linter_blocks_destructive_pattern() -> None:
    findings = lint_shell_command("rm -rf /")
    assert should_block(findings) is True


def test_shell_executor_raises_when_linter_blocks() -> None:
    try:
        run_shell_command("rm -rf /", protectiveness=20, operator_approved=False)
        assert False, "Expected CommandGuardBlocked"
    except CommandGuardBlocked:
        assert True


def test_pre_attack_intel_builds_expected_sections() -> None:
    intel = build_pre_attack_intel(
        target="example.azurewebsites.net",
        packages=["openssl"],
        services=["jenkins"],
    )
    assert "osint" in intel
    assert "vulnerabilities" in intel
    assert "default_credentials" in intel


def test_planner_guidance_returns_string() -> None:
    guidance = get_mission_guidance("RECON", findings_count=0, protectiveness=80)
    assert isinstance(guidance, str)
    assert guidance


def test_report_builder_cve_section_shape() -> None:
    section = get_cve_report_section(["openssl"], minimum_severity="low")
    assert section["section"] == "cve_intelligence"
    assert "findings" in section


def test_resource_budget_enforcement_detects_violation() -> None:
    budget = get_resource_budget(patience=50, protectiveness=70)
    verdict = enforce_budget(
        current={
            "cpu_seconds": int(budget["cpu_seconds"]) + 1,
            "memory_mb": int(budget["memory_mb"]),
            "network_mb": int(budget["network_mb"]),
            "max_parallel_tasks": int(budget["max_parallel_tasks"]),
        },
        budget=budget,
    )
    assert verdict["ok"] is False
    assert "cpu_seconds" in verdict["violations"]

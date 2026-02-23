from __future__ import annotations

from typing import Any

from backend.intel.archive_vault import archive_and_scan
from backend.intel.browser_recon import (
    BrowserReconResult,
    extract_attack_surface,
    should_run_browser_recon,
)
from backend.intel.secret_scanner import scan_file_dict


def run_firecrawl_pipeline(
    mission_id: str,
    url: str,
    content: str,
    js_detected: bool,
    curiosity: int,
    creativity: int,
    patience: int,
    aggression: int,
) -> dict[str, Any]:
    secret_findings = scan_file_dict(
        path=url,
        content=content,
        curiosity=curiosity,
        aggression=aggression,
    )

    browser_surface: dict[str, Any] = {}
    if should_run_browser_recon(js_detected, curiosity, creativity, patience):
        recon = BrowserReconResult(
            url=url,
            dom_snapshot=content[:2000],
            network_calls=[],
            ws_endpoints=[],
            forms=[],
        )
        browser_surface = extract_attack_surface(recon, aggression=aggression)

    archive_result = archive_and_scan(
        mission_id=mission_id,
        artifact_type="firecrawl_download",
        payload={"url": url, "content_preview": content[:1000]},
        curiosity=curiosity,
        aggression=aggression,
    )

    return {
        "mission_id": mission_id,
        "url": url,
        "secret_findings": secret_findings,
        "attack_surface": browser_surface,
        "archive": archive_result,
    }

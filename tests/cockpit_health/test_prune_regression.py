from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_no_legacy_ui_directories_remain() -> None:
    assert not (ROOT / "ui").exists()
    assert not (ROOT / "web").exists()
    assert not (ROOT / "web_ui").exists()
    assert not (ROOT / "organism").exists()


def test_no_legacy_bridge_scripts_remain() -> None:
    legacy = list(ROOT.rglob("cockpit-canonical-bridge.js"))
    assert not legacy


def test_no_runtime_references_to_legacy_routes() -> None:
    server_text = (ROOT / "swarmz_server.py").read_text(encoding="utf-8", errors="ignore")
    assert 'app.mount("/web"' not in server_text
    assert 'app.mount("/web_ui"' not in server_text
    assert 'FileResponse("web/' not in server_text
    assert "@app.get(\"/organism\")" in server_text
    assert "RedirectResponse(url=\"/cockpit/\", status_code=307)" in server_text

    for file in (ROOT / "cockpit" / "src").rglob("*"):
        if not file.is_file():
            continue
        text = file.read_text(encoding="utf-8", errors="ignore")
        for token in ("/web/", "/web_ui/", "/organism/", "/ui/nexusmon-cockpit.html"):
            assert token not in text, f"{token} found in {file}"

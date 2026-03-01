from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBS_CLEANUP = PROJECT_ROOT / "observatory" / "cleanup"
REPORT_PATH = PROJECT_ROOT / "docs" / "legacy_report.md"


def _latest_cleanup_report() -> Path | None:
    files = sorted(OBS_CLEANUP.glob("cleanup-report-*.json"))
    return files[-1] if files else None


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    latest = _latest_cleanup_report()
    if latest is None:
        REPORT_PATH.write_text(
            "# Legacy Report\n\nNo cleanup report found in `observatory/cleanup/`.\n",
            encoding="utf-8",
        )
        print(str(REPORT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"))
        return 0

    payload = json.loads(latest.read_text(encoding="utf-8-sig"))
    deleted_dirs = payload.get("deleted_dirs", [])
    deleted_files = payload.get("deleted_temp_files", [])
    moved_logs = payload.get("moved_logs", [])
    extras = payload.get("top_level_extras", [])
    notes = payload.get("notes", [])

    lines: list[str] = [
        "# Legacy Report",
        "",
        f"- Generated from: `{str(latest.relative_to(PROJECT_ROOT)).replace(chr(92), '/')}`",
        f"- Timestamp: `{payload.get('generated_at', 'unknown')}`",
        f"- Apply mode: `{payload.get('apply_mode', False)}`",
        "",
        "## Deleted Legacy Folders",
    ]
    if deleted_dirs:
        lines.extend([f"- `{item}`" for item in deleted_dirs])
    else:
        lines.append("- None found matching configured legacy patterns.")

    lines.extend(
        [
            "",
            "## Deleted Legacy Files",
        ]
    )
    if deleted_files:
        lines.extend([f"- `{item}`" for item in deleted_files])
    else:
        lines.append("- None.")

    lines.extend(["", "## Moved Logs"])
    if moved_logs:
        lines.extend([f"- `{item}`" for item in moved_logs])
    else:
        lines.append("- None.")

    lines.extend(["", "## Replacement Mapping"])
    lines.extend(
        [
            "- Legacy or scattered runtime manifests -> `core/manifests/registry.json`",
            "- Scattered telemetry/log files -> `observatory/logs/`",
            "- Non-unified hook paths -> `runtime/hooks.py` + `runtime/events.py`",
            "- Ad-hoc scheduler loops -> `runtime/scheduler.py`",
            "- Symbolic/life API operations -> governed via backend routers and manifest-gated hooks",
        ]
    )

    lines.extend(["", "## Remaining TODOs"])
    if extras:
        lines.append(
            "- Top-level normalization backlog (operator-reviewed; intentionally not auto-moved):"
        )
        lines.extend([f"- `{name}`" for name in extras])
    else:
        lines.append("- No extra top-level folders detected.")

    if notes:
        lines.extend(["", "## Notes"])
        lines.extend([f"- {note}" for note in notes])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REPORT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

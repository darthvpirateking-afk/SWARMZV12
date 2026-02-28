from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_FILES = [
    "docs/ARCHITECTURE.md",
    "docs/CORE_BOUNDARY.md",
    "docs/PLUGIN_CONTRACT.md",
    "docs/PATCHPACK_SCHEMA.md",
    "docs/RUNTIME_INVARIANTS.md",
    "schemas/agent-manifest.v1.json",
]

CORE_GLOBS = [
    "core/*.py",
    "schemas/*.json",
]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _has_adr_reference(text: str) -> bool:
    t = text.lower()
    return "adr-" in t or "docs/adr/" in t


def run_audit(repo_root: Path) -> dict:
    missing_files: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            missing_files.append(rel)

    core_files: list[Path] = []
    for pat in CORE_GLOBS:
        core_files.extend(repo_root.glob(pat))

    core_without_adr: list[str] = []
    for p in core_files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not _has_adr_reference(text):
            core_without_adr.append(str(p.relative_to(repo_root)).replace("\\", "/"))

    return {
        "generated_at": _utc_now(),
        "status": "advisory",
        "missing_required_files": missing_files,
        "core_files_without_adr_marker": core_without_adr,
        "summary": {
            "required_files_ok": len(missing_files) == 0,
            "core_adr_coverage_count": len(core_files) - len(core_without_adr),
            "core_file_count": len(core_files),
        },
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = run_audit(repo_root)
    out_dir = repo_root / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "constitution_audit.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote advisory report: {out}")


if __name__ == "__main__":
    main()

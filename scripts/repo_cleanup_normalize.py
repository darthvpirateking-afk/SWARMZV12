from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBSERVATORY_ROOT = PROJECT_ROOT / "observatory"
OBSERVATORY_LOGS = OBSERVATORY_ROOT / "logs"
OBSERVATORY_CLEANUP = OBSERVATORY_ROOT / "cleanup"

CANONICAL_TOP_LEVEL = {
    "core",
    "life",
    "symbolic",
    "runtime",
    "cockpit",
    "observatory",
    "tests",
    "scripts",
    "docs",
}

LEGACY_DIR_PATTERNS = (
    "proto*",
    "old*",
    "legacy*",
    "test*",
    "tmp*",
    "backup*",
    "copy*",
    "draft*",
    "experimental*",
    "magic_old*",
    "pantheon_test*",
    "sigils_old*",
    "rituals_old*",
    "agents_old*",
    "ui_old*",
    "screens_old*",
    "components_old*",
    "evolution_old*",
    "patcher_old*",
)

TEMP_FILE_EXTS = {".bak", ".tmp", ".copy", ".old"}
PROTECTED_ROOTS = {".git", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


@dataclass
class CleanupReport:
    generated_at: str
    apply_mode: bool
    deleted_dirs: List[str]
    deleted_temp_files: List[str]
    moved_logs: List[str]
    top_level_extras: List[str]
    notes: List[str]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_under_protected(path: Path) -> bool:
    try:
        rel = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return True
    if not rel.parts:
        return True
    return rel.parts[0] in PROTECTED_ROOTS


def _find_legacy_dirs() -> List[Path]:
    out: list[Path] = []
    for directory in PROJECT_ROOT.rglob("*"):
        if not directory.is_dir():
            continue
        if _is_under_protected(directory):
            continue
        if directory.name.startswith("."):
            continue
        try:
            rel = directory.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if not rel.parts:
            continue
        top = rel.parts[0]
        # Safety: only clean inside canonical top-level lanes.
        if top not in CANONICAL_TOP_LEVEL:
            continue
        # Never delete the canonical test suite lane.
        if top == "tests":
            continue
        for pattern in LEGACY_DIR_PATTERNS:
            if directory.match(pattern):
                out.append(directory)
                break
    return sorted(set(out))


def _find_temp_files() -> List[Path]:
    out: list[Path] = []
    for file_path in PROJECT_ROOT.rglob("*"):
        if not file_path.is_file():
            continue
        if _is_under_protected(file_path):
            continue
        if file_path.suffix.lower() in TEMP_FILE_EXTS:
            out.append(file_path)
    return sorted(out)


def _find_logs() -> List[Path]:
    out: list[Path] = []
    for file_path in PROJECT_ROOT.rglob("*.log"):
        if not file_path.is_file():
            continue
        if _is_under_protected(file_path):
            continue
        if OBSERVATORY_ROOT in file_path.parents:
            continue
        out.append(file_path)
    return sorted(out)


def _top_level_extras() -> List[str]:
    extras: list[str] = []
    for item in sorted(PROJECT_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if item.name.startswith("."):
            continue
        if not item.is_dir():
            continue
        if item.name not in CANONICAL_TOP_LEVEL:
            extras.append(item.name)
    return extras


def _remove_empty_dirs(paths: Iterable[Path], apply_mode: bool) -> None:
    for path in sorted(set(paths), key=lambda p: len(p.parts), reverse=True):
        try:
            if path.exists() and path.is_dir() and not any(path.iterdir()):
                if apply_mode:
                    path.rmdir()
        except Exception:
            continue


def run_cleanup(apply_mode: bool = False) -> CleanupReport:
    OBSERVATORY_LOGS.mkdir(parents=True, exist_ok=True)
    OBSERVATORY_CLEANUP.mkdir(parents=True, exist_ok=True)

    deleted_dirs: list[str] = []
    deleted_temp_files: list[str] = []
    moved_logs: list[str] = []
    notes: list[str] = []

    legacy_dirs = _find_legacy_dirs()
    for path in legacy_dirs:
        rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if apply_mode:
            shutil.rmtree(path, ignore_errors=True)
        deleted_dirs.append(rel)

    temp_files = _find_temp_files()
    for path in temp_files:
        rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if apply_mode:
            path.unlink(missing_ok=True)
        deleted_temp_files.append(rel)

    logs = _find_logs()
    emptied_candidates: list[Path] = []
    for path in logs:
        rel = path.relative_to(PROJECT_ROOT)
        rel_text = str(rel).replace("\\", "/")
        destination_name = rel_text.replace("/", "__")
        destination = OBSERVATORY_LOGS / destination_name
        if apply_mode:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
            emptied_candidates.append(path.parent)
        destination_rel = str(destination.relative_to(PROJECT_ROOT)).replace("\\", "/")
        moved_logs.append(f"{rel_text} -> {destination_rel}")

    if apply_mode:
        _remove_empty_dirs(emptied_candidates, apply_mode=True)

    extras = _top_level_extras()
    if extras:
        notes.append(
            "Top-level extras detected; not auto-moved to avoid non-deterministic breakage."
        )
        notes.append(
            "Use this report as an operator-reviewed migration backlog for structural normalization."
        )

    report = CleanupReport(
        generated_at=_utc_iso(),
        apply_mode=apply_mode,
        deleted_dirs=deleted_dirs,
        deleted_temp_files=deleted_temp_files,
        moved_logs=moved_logs,
        top_level_extras=extras,
        notes=notes,
    )
    report_path = OBSERVATORY_CLEANUP / (
        f"cleanup-report-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    report_path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    print(str(report_path.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe repository cleanup and normalization helper.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply cleanup actions (otherwise dry-run style report only).",
    )
    args = parser.parse_args()
    run_cleanup(apply_mode=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

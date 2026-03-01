from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGETS: tuple[str, ...] = (
    "hologram_snapshots",
    "observatory",
    "artifacts/audit",
    ".validation_baseline.json",
)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return
    path.unlink(missing_ok=True)


def run_clean(*, apply: bool) -> int:
    removed = 0
    missing = 0
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[clean-artifacts] mode={mode}")
    for relative in TARGETS:
        target = PROJECT_ROOT / relative
        if not target.exists():
            print(f"[clean-artifacts] missing: {relative}")
            missing += 1
            continue
        kind = "dir" if target.is_dir() else "file"
        if apply:
            _remove_path(target)
            print(f"[clean-artifacts] removed {kind}: {relative}")
        else:
            print(f"[clean-artifacts] would remove {kind}: {relative}")
        removed += 1
    print(
        "[clean-artifacts] summary "
        f"targets={len(TARGETS)} removed_or_would_remove={removed} missing={missing}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean generated repository artifacts.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete known generated artifacts; default mode is dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned removals without deleting files (default).",
    )
    args = parser.parse_args()
    apply = bool(args.apply)
    return run_clean(apply=apply)


if __name__ == "__main__":
    raise SystemExit(main())

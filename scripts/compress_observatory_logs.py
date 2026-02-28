from __future__ import annotations

import argparse
import gzip
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "observatory" / "logs"


def compress_logs(keep_originals: bool = True) -> int:
    if not LOG_DIR.exists():
        return 0
    compressed = 0
    for log_path in sorted(LOG_DIR.glob("*.log")):
        gz_path = log_path.with_suffix(log_path.suffix + ".gz")
        with log_path.open("rb") as source, gzip.open(gz_path, "wb", compresslevel=9) as target:
            shutil.copyfileobj(source, target)
        compressed += 1
        if not keep_originals:
            log_path.unlink(missing_ok=True)
    return compressed


def main() -> int:
    parser = argparse.ArgumentParser(description="Compress observatory logs.")
    parser.add_argument(
        "--remove-originals",
        action="store_true",
        help="Delete original .log files after compression.",
    )
    args = parser.parse_args()
    count = compress_logs(keep_originals=not args.remove_originals)
    print(f"compressed={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

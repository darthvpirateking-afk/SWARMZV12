# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Build BYPASS map from events.

Reads event records and produces a simple markdown report.
"""

import json
from pathlib import Path

from core.bypass_map import build_bypass_map


def main() -> None:
    events_file = Path("data") / "events.jsonl"
    output_file = Path("docs") / "BYPASS_MAP.md"
    rows = []
    if events_file.exists():
        for line in events_file.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    mapped = build_bypass_map(rows)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        "# BYPASS MAP\n\n" + "\n".join(f"- {item}" for item in mapped[:200]),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

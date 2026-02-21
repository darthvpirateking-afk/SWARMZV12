# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Build macros from sequence records."""

import json
from pathlib import Path

from core.macro_builder import build_macros


def main() -> None:
    sequences_file = Path("data") / "sequences.json"
    output_file = Path("data") / "macros.json"
    sequences = []
    if sequences_file.exists():
        try:
            payload = json.loads(
                sequences_file.read_text(encoding="utf-8", errors="replace")
            )
            if isinstance(payload, list):
                sequences = payload
        except Exception:
            sequences = []

    macros = build_macros(sequences)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(macros, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

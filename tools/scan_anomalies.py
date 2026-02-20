# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Scan events for simple anomalies and write anomalies.jsonl."""

import json
from pathlib import Path

from core.anomaly_detector import detect_anomalies


def main() -> None:
	events_file = Path("data") / "events.jsonl"
	out_file = Path("data") / "anomalies.jsonl"

	events = []
	if events_file.exists():
		for line in events_file.read_text(encoding="utf-8", errors="replace").splitlines():
			line = line.strip()
			if not line:
				continue
			try:
				events.append(json.loads(line))
			except json.JSONDecodeError:
				events.append(line)

	anomalies = detect_anomalies(events)
	out_file.parent.mkdir(parents=True, exist_ok=True)
	with out_file.open("w", encoding="utf-8") as handle:
		for row in anomalies:
			handle.write(json.dumps(row) + "\n")


if __name__ == "__main__":
	main()

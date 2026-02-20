# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Mine simple adjacent event sequences from events.jsonl."""

import json
from collections import Counter
from pathlib import Path


def main() -> None:
	events_file = Path("data") / "events.jsonl"
	out_file = Path("data") / "sequences.json"

	event_names = []
	if events_file.exists():
		for line in events_file.read_text(encoding="utf-8", errors="replace").splitlines():
			line = line.strip()
			if not line:
				continue
			try:
				payload = json.loads(line)
			except json.JSONDecodeError:
				continue
			if isinstance(payload, dict) and "event" in payload:
				event_names.append(str(payload["event"]))

	pairs = Counter(zip(event_names, event_names[1:]))
	seq = [
		{"name": f"{left}->{right}", "support": count}
		for (left, right), count in pairs.most_common()
	]

	out_file.parent.mkdir(parents=True, exist_ok=True)
	out_file.write_text(json.dumps(seq, indent=2), encoding="utf-8")


if __name__ == "__main__":
	main()

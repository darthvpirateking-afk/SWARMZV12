# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to validate events in events.jsonl against the canonical schema.
"""

import json
from core.activity_schema import validate_event

def validate_events(file_path):
    with open(file_path, "r") as f:
        for line_number, line in enumerate(f, start=1):
            try:
                event = json.loads(line)
                is_valid, message = validate_event(event)
                if not is_valid:
                    print(f"Line {line_number}: {message}")
            except json.JSONDecodeError:
                print(f"Line {line_number}: Invalid JSON")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate events in events.jsonl")
    parser.add_argument("file", help="Path to events.jsonl")
    args = parser.parse_args()

    validate_events(args.file)

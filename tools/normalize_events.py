# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to normalize events in events.jsonl and write to normalized_events.jsonl.
"""

import json
from core.normalizer import normalize_event


def normalize_events(input_file, output_file):
    with open(input_file, "r") as infile, open(output_file, "a") as outfile:
        for line in infile:
            try:
                event = json.loads(line)
                normalized_event = normalize_event(event)
                outfile.write(json.dumps(normalized_event) + "\n")
            except json.JSONDecodeError:
                print("Invalid JSON, skipping line.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize events in events.jsonl")
    parser.add_argument("input_file", help="Path to events.jsonl")
    parser.add_argument("output_file", help="Path to normalized_events.jsonl")
    args = parser.parse_args()

    normalize_events(args.input_file, args.output_file)

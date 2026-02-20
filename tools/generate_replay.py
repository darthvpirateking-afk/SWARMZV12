# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to generate replay plans for sequences or macros.
"""

import json
from core.replay_simulator import generate_replay_plan

def generate_replay(input_file, output_file):
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        sequence_or_macro = json.load(infile)
        replay_plan = generate_replay_plan(sequence_or_macro)
        outfile.write(json.dumps(replay_plan, indent=4))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate replay plans for sequences or macros.")
    parser.add_argument("input_file", help="Path to sequence or macro JSON file")
    parser.add_argument("output_file", help="Path to output replay plan JSON file")
    args = parser.parse_args()

    generate_replay(args.input_file, args.output_file)

# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to create evidence packs for claims.
"""

import json
from core.evidence_pack import create_evidence_pack

def generate_evidence_pack(claim, filter_criteria, output_file):
    # Placeholder: Load events based on filter_criteria
    events = []  # Replace with actual event filtering logic
    stats = {"example_stat": 42}  # Replace with actual stats computation
    suggested_fix = "Investigate X"

    evidence_pack = create_evidence_pack(claim, events, stats, suggested_fix)
    with open(output_file, "w") as outfile:
        outfile.write(json.dumps(evidence_pack, indent=4))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create evidence packs for claims.")
    parser.add_argument("--claim", required=True, help="Claim text")
    parser.add_argument("--filter", required=True, help="Filter criteria for events")
    parser.add_argument("--output", required=True, help="Output file for evidence pack")
    args = parser.parse_args()

    generate_evidence_pack(args.claim, args.filter, args.output)

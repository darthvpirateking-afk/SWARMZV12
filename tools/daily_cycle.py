# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Runs the full daily SWARMZ operator ritual.
Safe, additive, and non-destructive.
"""

import subprocess


def run(cmd):
    print(f"\n>>> {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=False)
    except Exception as e:
        print(f"[fail-open] {e}")


def main():
    print("SWARMZ DAILY CYCLE START\n")

    # Ritual A
    print("STEP 1 â€” Verifying activity stream...")
    run("python tools/verify_activity_stream.py")

    # Ritual B
    print("\nSTEP 2 â€” Normalizing events...")
    run("python tools/normalize_events.py")

    print("\nSTEP 3 â€” Mining sequences...")
    run("python tools/mine_sequences.py")

    print("\nSTEP 4 â€” Generating value report...")
    run("python tools/value_report.py")

    print("\nDONE. Now open:")
    print("  data/activity/sequences.json")
    print("Pick the top repeated sequence and run:")
    print("  python tools/build_macro.py --sequence <top_id>")

    print("\nSWARMZ DAILY CYCLE COMPLETE.")


if __name__ == "__main__":
    main()

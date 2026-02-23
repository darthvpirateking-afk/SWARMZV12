# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to rotate logs based on size.
"""

from core.log_retention import rotate_logs

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Rotate logs if they exceed the maximum size."
    )
    parser.add_argument("log_file", help="Path to the log file")
    args = parser.parse_args()

    rotate_logs(args.log_file)

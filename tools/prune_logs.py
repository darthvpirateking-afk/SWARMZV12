# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tool to prune logs older than a specified number of days.
"""

from core.log_retention import prune_logs

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prune logs older than a specified number of days.")
    parser.add_argument("log_dir", help="Path to the log directory")
    args = parser.parse_args()

    prune_logs(args.log_dir)

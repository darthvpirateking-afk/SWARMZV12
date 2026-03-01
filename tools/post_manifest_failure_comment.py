"""Post a blocking PR comment for manifest validation failures."""
from __future__ import annotations

import argparse
import os
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description="Post manifest validation failure comment")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--error", required=True)
    parser.add_argument("--suggested-fix", required=True)
    args = parser.parse_args()

    pr_number = os.getenv("PR_NUMBER") or os.getenv("GITHUB_REF_NAME", "")
    body = (
        "### Blocking Manifest Validation Failure\n"
        f"- Manifest: `{args.manifest}`\n"
        f"- Error: `{args.error}`\n"
        f"- Suggested fix: {args.suggested_fix}\n"
    )

    if not pr_number:
        print(body)
        return 0

    cmd = ["gh", "pr", "comment", str(pr_number), "--body", body]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

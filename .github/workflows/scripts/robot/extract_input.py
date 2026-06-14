#!/usr/bin/env python3
"""Step 1: Extract PR metadata and write to a file for the next step.

For PR review, we extract the PR title, body, base/head branches,
and fetch the diff to include in the LLM prompt.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

PR_TITLE = os.environ.get("PR_TITLE", "")
PR_BODY = os.environ.get("PR_BODY", "")
PR_BASE = os.environ.get("PR_BASE", "")
PR_HEAD = os.environ.get("PR_HEAD", "")
PR_DIFF_URL = os.environ.get("PR_DIFF_URL", "")


def fetch_diff(diff_url: str) -> str:
    """Fetch the PR diff from GitHub."""
    if not diff_url:
        return "(No diff URL provided)"
    try:
        resp = requests.get(diff_url, timeout=30)
        resp.raise_for_status()
        diff = resp.text
        # Truncate very large diffs to avoid exceeding LLM context
        if len(diff) > 8000:
            diff = diff[:8000] + "\n... (diff truncated, too large)"
        return diff
    except Exception as e:
        return f"(Failed to fetch diff: {e})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PR metadata")
    parser.add_argument("--output", default="pr_meta.txt", help="File to write PR metadata to")
    args = parser.parse_args()

    if not PR_TITLE:
        print("PR_TITLE environment variable is required")
        sys.exit(1)

    diff = fetch_diff(PR_DIFF_URL)

    meta = f"""PR_TITLE={PR_TITLE}
PR_BASE={PR_BASE}
PR_HEAD={PR_HEAD}
---BODY---
{PR_BODY}
---DIFF---
{diff}
"""

    Path(args.output).write_text(meta)
    print(f"PR metadata extracted ({len(meta)} chars)")


if __name__ == "__main__":
    main()

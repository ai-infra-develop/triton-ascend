#!/usr/bin/env python3
"""Step 1: Extract commit log from the PR and write to a file.

Fetches all commits in the PR via GitHub API and formats them
for LLM review.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

PR_NUMBER = os.environ.get("PR_NUMBER", "")
REPO = os.environ.get("REPO", "")
PR_BASE = os.environ.get("PR_BASE", "")
PR_HEAD = os.environ.get("PR_HEAD", "")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API = os.environ.get("GITHUB_API_URL", "https://api.github.com")


def fetch_commits() -> list[dict]:
    """Fetch all commits in the PR via GitHub API."""
    url = f"{GITHUB_API}/repos/{REPO}/pulls/{PR_NUMBER}/commits"
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    all_commits = []
    page = 1
    while True:
        resp = requests.get(
            url, params={"per_page": 100, "page": page}, headers=headers, timeout=30
        )
        resp.raise_for_status()
        commits = resp.json()
        if not commits:
            break
        all_commits.extend(commits)
        if len(commits) < 100:
            break
        page += 1

    return all_commits


def format_commit_log(commits: list[dict]) -> str:
    """Format commits into a readable log for LLM review."""
    lines = [f"## PR Commit Log ({len(commits)} commits)", ""]

    for i, c in enumerate(commits):
        commit_data = c.get("commit", {})
        sha = c.get("sha", "")[:8]
        message = commit_data.get("message", "").strip()
        author = commit_data.get("author", {}).get("name", "unknown")

        # Split subject line from body
        parts = message.split("\n", 1)
        subject = parts[0]
        body = parts[1] if len(parts) > 1 else ""

        lines.append(f"### Commit {i + 1}: `{sha}`")
        lines.append(f"**Author**: {author}")
        lines.append(f"**Subject**: {subject}")
        if body:
            # Truncate very long bodies
            if len(body) > 500:
                body = body[:500] + "\n... (truncated)"
            lines.append(f"**Body**:")
            lines.append(f"```")
            lines.append(body)
            lines.append(f"```")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PR commit log")
    parser.add_argument("--output", default="commit_log.txt", help="File to write commit log to")
    args = parser.parse_args()

    if not PR_NUMBER or not REPO:
        print("PR_NUMBER and REPO environment variables are required")
        sys.exit(1)

    print(f"Fetching commits for PR #{PR_NUMBER} in {REPO}...")
    commits = fetch_commits()
    print(f"Found {len(commits)} commits")

    log_text = format_commit_log(commits)
    Path(args.output).write_text(log_text)
    print(f"Commit log written ({len(log_text)} chars)")


if __name__ == "__main__":
    main()

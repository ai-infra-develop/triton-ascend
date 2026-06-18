#!/usr/bin/env python3
"""Step 4: Call LLM with assembled commit log review prompt.

Reads system prompt, Conventional Commits spec, and commit log,
calls the vLLM endpoint, and writes the review output to a file.

Usage:
    python call_llm.py --system-prompt system_prompt.txt --template template.txt --commit-log commit_log.txt --output review_output.md
"""

import argparse
import os
import sys
from pathlib import Path

import requests

VLLM_BASE_URL = os.environ["VLLM_BASE_URL"]
VLLM_API_KEY = os.environ["VLLM_API_KEY"]
PR_TITLE = os.environ.get("PR_TITLE", "")


def call_vllm(system_prompt: str, user_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {VLLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "default",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    resp = requests.post(
        f"{VLLM_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Call LLM for commit log review")
    parser.add_argument("--system-prompt", default="system_prompt.txt", help="File containing the system prompt")
    parser.add_argument("--template", default="template.txt", help="File containing the Conventional Commits spec")
    parser.add_argument("--commit-log", default="commit_log.txt", help="File containing the PR commit log")
    parser.add_argument("--output", default="review_output.md", help="File to write the LLM review output to")
    args = parser.parse_args()

    system_prompt_path = Path(args.system_prompt)
    template_path = Path(args.template)
    commit_log_path = Path(args.commit_log)

    for p, name in [(system_prompt_path, "System prompt"), (template_path, "Template"), (commit_log_path, "Commit log")]:
        if not p.exists():
            print(f"{name} file not found: {p}")
            sys.exit(1)

    system_prompt = system_prompt_path.read_text()
    template_text = template_path.read_text()
    commit_log = commit_log_path.read_text()

    user_prompt = f"""## PR Title
{PR_TITLE}

## Conventional Commits Specification
{template_text}

## Commit Log to Review
{commit_log}

Please review the commit messages in this PR against the Conventional Commits specification and provide your feedback in the specified format.
"""

    print("Calling vLLM for commit log review...")
    review = call_vllm(system_prompt, user_prompt)

    output_path = Path(args.output)
    output_path.write_text(review)
    print(f"Review written to {output_path} ({len(review)} chars)")


if __name__ == "__main__":
    main()

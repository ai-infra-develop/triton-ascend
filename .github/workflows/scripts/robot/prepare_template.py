#!/usr/bin/env python3
"""Step 2: Load the Conventional Commits specification template.

Reads the spec from a bundled file and writes it for the LLM prompt.
"""

import argparse
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "commit_review_prompts"


def load_template() -> str:
    path = TEMPLATE_DIR / "conventional_commits_spec.txt"
    if path.exists():
        return path.read_text()
    return "(Conventional Commits specification not found)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Conventional Commits template")
    parser.add_argument("--output", default="template.txt", help="File to write the template to")
    args = parser.parse_args()

    template_text = load_template()
    Path(args.output).write_text(template_text)
    print(f"Template prepared ({len(template_text)} chars)")


if __name__ == "__main__":
    main()

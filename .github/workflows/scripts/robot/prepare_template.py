#!/usr/bin/env python3
"""Step 2: Load the PR template and write it to a file.

For PR review, there is a single PR template (not type-specific).
"""

import argparse
from pathlib import Path

TEMPLATE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "PULL_REQUEST_TEMPLATE.md"


def load_template() -> str:
    if not TEMPLATE_PATH.exists():
        return "(PR template not found)"

    content = TEMPLATE_PATH.read_text()

    lines = ["## PR Template (what the author was asked to fill in)", ""]
    lines.append(content)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare PR template")
    parser.add_argument("--output", default="template.txt", help="File to write the template to")
    args = parser.parse_args()

    template_text = load_template()
    Path(args.output).write_text(template_text)
    print(f"Template prepared ({len(template_text)} chars)")


if __name__ == "__main__":
    main()

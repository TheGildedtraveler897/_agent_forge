#!/usr/bin/env python3
"""prompt-auto-activator: user_prompt_submit advisory hook.

Reads the prompt JSON on stdin, matches against a keyword table, and
prints one advisory line per match. Never blocks.

Cross-platform Python port of auto-activator.sh. Runs natively on
Windows, macOS, and Linux. The .sh wrapper forwards to this script so
legacy hook records keep working on POSIX.
"""

from __future__ import annotations

import json
import re
import sys


ADVISORIES: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"/caveman|caveman\s+mode|/terse|terse\s+mode", re.IGNORECASE),
        "Operator requested terse output; load token-optimizer.",
        "token-optimizer",
    ),
    (
        re.compile(r"/checkpoint|/handoff", re.IGNORECASE),
        "Operator requested checkpoint; load context-engineer.",
        "context-engineer",
    ),
]


def extract_prompt(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        for key in ("prompt", "Prompt", "user_prompt", "text"):
            value = parsed.get(key)
            if isinstance(value, str):
                return value
    match = re.search(r'"prompt"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if match:
        return match.group(1).encode("utf-8").decode("unicode_escape", errors="replace")
    return raw


def main() -> int:
    try:
        raw = sys.stdin.read()
    except (KeyboardInterrupt, OSError):
        return 0

    prompt = extract_prompt(raw)
    if not prompt:
        return 0

    for pattern, advice, skill in ADVISORIES:
        if pattern.search(prompt):
            sys.stdout.write(json.dumps({"advice": advice, "skill": skill}) + "\n")

    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

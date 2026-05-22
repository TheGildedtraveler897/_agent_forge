#!/usr/bin/env python3
"""telemetry-guardian: universal pre-tool-execution guardrail.

Reads one JSON tool invocation on stdin; exits 0 to allow, 1 to block,
2 on self-error. Deny list is fixed-string / short regex patterns; err
toward blocking.

Opt out: AGENT_FORGE_GUARDIAN=off (logged to ~/.agent-forge/guardian.log).

Cross-platform Python port of guardian.sh. Runs natively on Windows,
macOS, and Linux without requiring bash. The .sh wrapper forwards to
this script so legacy hook records keep working on POSIX.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path.home() / ".agent-forge"
LOG_FILE = LOG_DIR / "guardian.log"

DENY_LIST: list[tuple[str, str]] = [
    (
        r"--no-verify(\s|$)",
        "bypassing pre-commit hooks is not allowed",
    ),
    (
        r"(--no-gpg-sign|commit\.gpgsign=false)",
        "bypassing commit signing is not allowed",
    ),
    (
        r"git\s+push\s+.*(--force|--force-with-lease).*(main|master|develop)",
        "force-push to a protected branch is not allowed",
    ),
    (
        r"(main|master|develop).*(--force|--force-with-lease).*git\s+push",
        "force-push to a protected branch is not allowed",
    ),
    (
        r"git\s+reset\s+--hard\s+\S+",
        "git reset --hard against an explicit ref is gated; drop the target or override",
    ),
    (
        r"rm\s+-rf\s+(~|\$HOME|/)(\s|$|/\*)",
        "wildcard root/home deletion is not allowed",
    ),
    (
        r"terraform\s+destroy(\s(-[^t]|[^-])|$)",
        "terraform destroy without -target is not allowed",
    ),
    (
        r"dd\s+.*of=/dev/sd[a-z]",
        "whole-disk dd writes are not allowed",
    ),
    (
        r"chmod\s+-R\s+777\s+(~|\$HOME|/)",
        "recursive 777 on home/root is not allowed",
    ),
]


def emit(verdict: str, reason: str, matched: str = "") -> None:
    payload = {"verdict": verdict, "reason": reason, "matched": matched}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def log_line(verdict: str, command: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\t{verdict}\t{command}\n")
    except OSError:
        pass


def extract_command(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        for key in ("command", "Command", "tool_input", "input"):
            value = parsed.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                inner = value.get("command") or value.get("Command")
                if isinstance(inner, str):
                    return inner
    match = re.search(r'"command"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if match:
        return match.group(1).encode("utf-8").decode("unicode_escape", errors="replace")
    return raw


def main() -> int:
    try:
        raw_input = sys.stdin.read()
    except (KeyboardInterrupt, OSError):
        emit("allow", "stdin read interrupted", "")
        return 0

    command = extract_command(raw_input)

    if os.environ.get("AGENT_FORGE_GUARDIAN", "on") == "off":
        log_line("bypass", command)
        emit("allow", "guardian bypassed via AGENT_FORGE_GUARDIAN=off", "")
        return 0

    for pattern, reason in DENY_LIST:
        if re.search(pattern, command):
            log_line("block", command)
            emit("block", reason, pattern)
            return 1

    emit("allow", "no deny-list match", "")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - guardian must never explode silently
        sys.stderr.write(f"guardian self-error: {exc}\n")
        sys.exit(2)

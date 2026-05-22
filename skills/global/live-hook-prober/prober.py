#!/usr/bin/env python3
"""live-hook-prober: fire a known test command on a target host CLI and
verify whether the seeded pre-tool-execution-guardian hook actually
intercepted it as expected.

Output (stdout): single-line JSON.
Exit codes:
  0 verdict=pass
  1 verdict=fail
  2 verdict=escalated (sandbox/trust block, CLI missing, headless constraint)

Cross-platform Python port of prober.sh. Runs natively on Windows,
macOS, and Linux. The .sh wrapper forwards to this script so legacy
hook records keep working on POSIX.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


VALID_HOSTS = ("claude", "codex", "gemini")
VALID_EXPECTS = ("block", "allow", "available")
VALID_HANDLERS = ("command", "http", "mcp_tool", "prompt", "agent")

SCRIPT_DIR = Path(__file__).resolve().parent
FACTORY_ROOT = SCRIPT_DIR.parent.parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="prober.py",
        description="Live invocation gate for the pre-tool-execution guardian hook.",
    )
    parser.add_argument("--host", required=True, choices=VALID_HOSTS)
    parser.add_argument("--project", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--expect", required=True, choices=VALID_EXPECTS)
    parser.add_argument("--handler-type", default="command", choices=VALID_HANDLERS)
    parser.add_argument("--evidence-root", default=None)
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


def run_cli(
    args: list[str],
    cwd: Path | None,
    timeout: int,
    stdout_file: Path,
    stderr_file: Path,
) -> int:
    try:
        result = subprocess.run(  # noqa: S603
            args,
            cwd=str(cwd) if cwd else None,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_file.write_text(exc.stdout or "")
        stderr_file.write_text((exc.stderr or "") + "\n[prober] timeout expired\n")
        return 124
    except FileNotFoundError:
        stdout_file.write_text("")
        stderr_file.write_text("[prober] CLI binary not found\n")
        return 127

    stdout_file.write_text(result.stdout or "")
    stderr_file.write_text(result.stderr or "")
    return result.returncode


def search_files(pattern: re.Pattern[str], *paths: Path) -> bool:
    for path in paths:
        if not path.exists():
            continue
        try:
            body = path.read_text(errors="replace")
        except OSError:
            continue
        if pattern.search(body):
            return True
    return False


def probe_claude(
    project: Path,
    command: str,
    timeout: int,
    stdout_file: Path,
    stderr_file: Path,
) -> str:
    if not shutil.which("claude"):
        stderr_file.write_text("prober: claude CLI not on PATH\n")
        return "cli_missing"

    prompt = (
        f"Use the Bash tool to run exactly this command: {command}. "
        "Report only ===BLOCKED=== if the tool call was blocked by a hook, "
        "or ===ALLOWED=== if it ran. Do not retry."
    )
    short_timeout = min(timeout, 30)
    rc = run_cli(
        ["claude", "-p", prompt, "--output-format", "text", "--permission-mode", "default"],
        cwd=project,
        timeout=short_timeout,
        stdout_file=stdout_file,
        stderr_file=stderr_file,
    )
    if rc == 124:
        return "headless_permission_constraint"
    if rc == 127:
        return "cli_missing"

    permission_pattern = re.compile(
        r"permission.*denied|requires.*approval|cannot.*run.*without.*approval",
        re.IGNORECASE,
    )
    if search_files(permission_pattern, stdout_file, stderr_file):
        return "headless_permission_constraint"
    if search_files(re.compile(r"===BLOCKED==="), stdout_file):
        return "block"
    if search_files(re.compile(r"===ALLOWED==="), stdout_file):
        return "allow"
    return "error"


def probe_codex(
    project: Path,
    command: str,
    timeout: int,
    stdout_file: Path,
    stderr_file: Path,
) -> str:
    if not shutil.which("codex"):
        stderr_file.write_text("prober: codex CLI not on PATH\n")
        return "cli_missing"

    prompt = (
        f"Use your shell tool to run exactly: {command}. "
        "Then output only ===BLOCKED=== if a hook blocked it, "
        "or ===ALLOWED=== if it ran. Do not retry."
    )
    rc = run_cli(
        ["codex", "exec", prompt],
        cwd=project,
        timeout=timeout,
        stdout_file=stdout_file,
        stderr_file=stderr_file,
    )
    if rc == 127:
        return "cli_missing"

    sandbox_pattern = re.compile(
        r"bwrap: |needs access to create user namespaces|"
        r"shell tool failed before command execution|"
        r"shell tool is blocked by the sandbox"
    )
    if search_files(sandbox_pattern, stdout_file, stderr_file):
        return "sandbox_blocked"
    if search_files(re.compile(r"===BLOCKED==="), stdout_file):
        return "block"
    if search_files(re.compile(r"===ALLOWED==="), stdout_file):
        return "allow"
    return "error"


def probe_gemini(
    project: Path,
    command: str,
    timeout: int,
    stdout_file: Path,
    stderr_file: Path,
) -> str:
    if not shutil.which("gemini"):
        stderr_file.write_text("prober: gemini CLI not on PATH\n")
        return "cli_missing"

    prompt = (
        f"Use the run_shell_command tool to execute exactly: {command}. "
        "Then output only ===BLOCKED=== if a hook blocked it, "
        "or ===ALLOWED=== if it ran. Do not retry."
    )
    rc = run_cli(
        ["gemini", "-p", prompt],
        cwd=project,
        timeout=timeout,
        stdout_file=stdout_file,
        stderr_file=stderr_file,
    )
    if rc == 127:
        return "cli_missing"

    trust_pattern = re.compile(
        r"workspace.*not.*trusted|trust.*required|trust.*folder",
        re.IGNORECASE,
    )
    if search_files(trust_pattern, stdout_file, stderr_file):
        return "trust_blocked"
    if search_files(re.compile(r"===BLOCKED==="), stdout_file):
        return "block"
    if search_files(re.compile(r"===ALLOWED==="), stdout_file):
        return "allow"
    return "error"


def probe_handler_mode(handler_type: str, evidence_dir: Path) -> str:
    if handler_type == "http":
        (evidence_dir / "http-sentinel.json").write_text(
            json.dumps({"handler_type": "http", "sentinel": "available"}) + "\n"
        )
        return "handler_mode_available"
    if handler_type == "mcp_tool":
        return "no_mcp_test_server_available"
    return "headless_handler_probe_unavailable"


def classify(observed: str, expected: str) -> tuple[str, str]:
    if observed in ("block", "allow"):
        if observed == expected:
            return "pass", ""
        if expected == "block" and observed == "allow":
            return "fail", "silent_pass: hook did not fire"
        return "fail", f"observed={observed} but expected={expected}"
    if observed == "handler_mode_available":
        if expected == "available":
            return "pass", ""
        return "fail", "handler mode available but expected=" + expected
    if observed in (
        "sandbox_blocked",
        "trust_blocked",
        "cli_missing",
        "headless_permission_constraint",
        "no_mcp_test_server_available",
        "headless_handler_probe_unavailable",
    ):
        return "escalated", observed
    return "fail", "probe could not determine block/allow"


def main() -> int:
    args = parse_args()

    project = Path(args.project).expanduser()
    if not project.is_dir():
        sys.stderr.write(f"prober: project root not found: {project}\n")
        return 64

    evidence_root = (
        Path(args.evidence_root).expanduser()
        if args.evidence_root
        else FACTORY_ROOT / "runtime" / "validation" / "hook-probe"
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    evidence_dir = evidence_root / stamp / args.host
    evidence_dir.mkdir(parents=True, exist_ok=True)

    stdout_file = evidence_dir / "stdout.txt"
    stderr_file = evidence_dir / "stderr.txt"
    meta_file = evidence_dir / "meta.json"

    if args.handler_type == "command":
        if args.host == "claude":
            observed = probe_claude(project, args.command, args.timeout, stdout_file, stderr_file)
        elif args.host == "codex":
            observed = probe_codex(project, args.command, args.timeout, stdout_file, stderr_file)
        else:
            observed = probe_gemini(project, args.command, args.timeout, stdout_file, stderr_file)
    else:
        observed = probe_handler_mode(args.handler_type, evidence_dir)

    meta = {
        "host": args.host,
        "handler_type": args.handler_type,
        "project": str(project),
        "command": args.command,
        "expected": args.expect,
        "observed": observed,
        "stamp": stamp,
        "ts": time.time(),
    }
    meta_file.write_text(json.dumps(meta) + "\n")

    verdict, reason = classify(observed, args.expect)
    if verdict == "fail" and reason.startswith("silent_pass"):
        reason = f"silent_pass: hook did not fire on {args.host}"
        observed = "silent_pass"

    output = {
        "host": args.host,
        "handler_type": args.handler_type,
        "command": args.command,
        "expected": args.expect,
        "observed": observed,
        "verdict": verdict,
        "evidence_path": str(evidence_dir),
        "reason": reason,
    }
    sys.stdout.write(json.dumps(output) + "\n")
    sys.stdout.flush()

    log_file = evidence_root / "log.jsonl"
    evidence_root.mkdir(parents=True, exist_ok=True)
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**meta, "verdict": verdict, "reason": reason, "evidence": str(evidence_dir)}) + "\n")
    except OSError:
        pass

    if verdict == "pass":
        return 0
    if verdict == "fail":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())

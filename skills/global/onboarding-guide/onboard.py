#!/usr/bin/env python3
"""Onboarding guide for the Agent Forge factory.

This script supports two non-conversational modes:

  check         — non-interactive machine-state report (six probes).
  explain TOPIC — plain-English explainer for a single concept, read
                  from EXPLAINERS.md (single source of truth).

A third subcommand `tour` exists only as a redirect message:
the paced, interactive tour now runs inline in Claude Code, Codex,
or Gemini via the slash command `/onboarding-guide`. The host CLI
reads SKILL.md (sibling file) and the assistant walks the user
through the seven beats directly in chat — no subprocess. The
redirect message exists so a terminal-only operator who tries
`python3 onboard.py tour` is pointed at the right path.

Read-only and observational. Never modifies MEMORY.md,
LESSONS_LEARNED.md, canonical sources, or bootstrap-project.sh.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# The skill lives at <forge>/skills/global/onboarding-guide/onboard.py.
SKILL_ROOT = Path(__file__).resolve().parent
FACTORY_ROOT = SKILL_ROOT.parent.parent.parent
PROJECTS_ROOT = FACTORY_ROOT.parent

REGISTRY_PATH = FACTORY_ROOT / "registry.json"
PROJECTS_PATH = FACTORY_ROOT / "projects.json"
HOOKS_POLICY = FACTORY_ROOT / "policies" / "hooks.json"
MEMORY_POLICY = FACTORY_ROOT / "policies" / "memory.json"
VERIFIER = FACTORY_ROOT / "scripts" / "verify-agent-forge.py"
TRIAD_VALIDATOR = FACTORY_ROOT / "scripts" / "validate-triad-runtime.py"
EXPLAINERS_PATH = SKILL_ROOT / "EXPLAINERS.md"


# ---------------------------------------------------------------------------
# Output helpers — ASCII glyphs only, color optional via ANSI when TTY.
# ---------------------------------------------------------------------------

def _is_tty() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _color(text: str, code: str) -> str:
    if not _is_tty():
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return _color(text, "32")


def yellow(text: str) -> str:
    return _color(text, "33")


def red(text: str) -> str:
    return _color(text, "31")


def bold(text: str) -> str:
    return _color(text, "1")


def dim(text: str) -> str:
    return _color(text, "2")


def hr() -> None:
    print(dim("-" * 72))


def verdict_glyph(verdict: str) -> str:
    return {
        "green": green("[OK]  "),
        "yellow": yellow("[WARN]"),
        "red": red("[FAIL]"),
    }.get(verdict, f"[{verdict.upper()}]")


# ---------------------------------------------------------------------------
# State detection (the six probes)
# ---------------------------------------------------------------------------

def _factory_present() -> tuple[str, str, str]:
    """Probe 1: is _agent_forge deployed with its canonical files?"""
    needed = [
        FACTORY_ROOT / "AGENTS.md",
        HOOKS_POLICY,
        MEMORY_POLICY,
        REGISTRY_PATH,
    ]
    missing = [p.relative_to(FACTORY_ROOT) for p in needed if not p.exists()]
    if not missing:
        return ("green", "Factory present at " + str(FACTORY_ROOT), "")
    return (
        "red",
        f"Factory incomplete; missing: {', '.join(str(m) for m in missing)}",
        f"cd {FACTORY_ROOT} && ./scripts/deploy-factory.sh",
    )


def _verifier_passes() -> tuple[str, str, str]:
    """Probe 2: does verify-agent-forge.py exit 0?"""
    if not VERIFIER.exists():
        return ("red", "verify-agent-forge.py is missing", "Re-deploy the factory.")
    try:
        rc = subprocess.run(
            ["python3", str(VERIFIER)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return (
            "red",
            "verify-agent-forge.py timed out after 60s",
            f"python3 {VERIFIER}  # run manually and read the output",
        )
    if rc.returncode == 0:
        return ("green", "Structural verifier reports no [FAIL] lines.", "")
    fails = [
        line for line in (rc.stdout + rc.stderr).splitlines()
        if "[FAIL]" in line
    ]
    summary = f"Structural verifier exit={rc.returncode}; {len(fails)} failure(s)."
    return ("red", summary, f"python3 {VERIFIER}  # read failures, fix one at a time")


def _clis_on_path() -> tuple[str, str, str]:
    """Probe 3: are the three host CLIs on PATH?"""
    found = {name: shutil.which(name) for name in ("claude", "codex", "gemini")}
    missing = [name for name, path in found.items() if path is None]
    if not missing:
        return ("green", "All three host CLIs are on PATH (claude, codex, gemini).", "")
    if len(missing) < 3:
        return (
            "yellow",
            f"Some host CLIs are missing from PATH: {', '.join(missing)}.",
            f"cd {FACTORY_ROOT} && ./scripts/bootstrap-workstation.sh",
        )
    return (
        "red",
        "No host CLIs are on PATH. Workstation bootstrap has not been run.",
        f"cd {FACTORY_ROOT} && ./scripts/bootstrap-workstation.sh",
    )


def _governed_projects() -> list[dict]:
    if not PROJECTS_PATH.exists():
        return []
    try:
        data = json.loads(PROJECTS_PATH.read_text())
    except Exception:
        return []
    return list(data.get("governed_projects") or [])


def _project_present() -> tuple[str, str, str]:
    """Probe 4: is at least one governed project actually on disk?"""
    projects = _governed_projects()
    if not projects:
        return (
            "red",
            "projects.json has no governed_projects entries.",
            "Edit projects.json to declare a governed project, then run "
            "scripts/bootstrap-project.sh --name <name>.",
        )
    present = []
    for p in projects:
        root = PROJECTS_ROOT / p["root"]
        if root.exists():
            present.append(p["name"])
    if present:
        return (
            "green",
            f"{len(present)} governed project(s) present on disk: {', '.join(present)}.",
            "",
        )
    return (
        "yellow",
        "projects.json declares projects but none are present on disk yet.",
        f"cd {FACTORY_ROOT} && ./scripts/bootstrap-project.sh --name <one-of: " +
        ", ".join(p["name"] for p in projects) + ">",
    )


def _triad_surface_passes() -> tuple[str, str, str]:
    """Probe 5: does validate-triad-runtime.py pass surface check on the first
    available governed project? Surface check only — no --probe-invocations,
    per the 2026-04-26 leftover-subprocess-tree lesson.
    """
    if not TRIAD_VALIDATOR.exists():
        return ("yellow", "validate-triad-runtime.py is missing.", "Re-deploy the factory.")
    projects = _governed_projects()
    candidates = []
    for p in projects:
        if (PROJECTS_ROOT / p["root"]).exists():
            candidates.append(p["name"])
    if not candidates:
        return (
            "yellow",
            "No governed project on disk; cannot run triad validator yet.",
            "Bootstrap a project first (see Probe 4 fix).",
        )
    target = candidates[0]
    try:
        rc = subprocess.run(
            ["python3", str(TRIAD_VALIDATOR), "--project", target],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return (
            "red",
            f"Triad validator timed out on project '{target}'.",
            f"python3 {TRIAD_VALIDATOR} --project {target}  # run manually",
        )
    if rc.returncode == 0:
        return (
            "green",
            f"All three host CLIs see what the factory shipped to '{target}'.",
            "",
        )
    return (
        "yellow",
        f"Triad surface check failed on '{target}'. "
        "This often means a host CLI is unauthed or a sandbox is blocking inspection.",
        f"python3 {TRIAD_VALIDATOR} --project {target}  # read which host failed and why",
    )


def _user_home_surfaces() -> tuple[str, str, str]:
    """Probe 6: are user-home host directories populated?"""
    home = Path.home()
    surfaces = {
        "claude": home / ".claude" / "agents",
        "codex": home / ".agents" / "skills",
        "gemini": home / ".gemini" / "agents",
    }
    found = {name: path.exists() and any(path.iterdir()) for name, path in surfaces.items() if path.exists()}
    populated = [name for name, ok in found.items() if ok]
    missing = [name for name in surfaces if name not in populated]
    if len(populated) == 3:
        return ("green", "User-home host directories are populated for all three hosts.", "")
    if populated:
        return (
            "yellow",
            f"User-home host directories populated for: {', '.join(populated)}; missing: {', '.join(missing)}.",
            f"cd {FACTORY_ROOT} && python3 scripts/omni_factory.py sync-claude --project <name>  "
            "(repeat for sync-codex / sync-gemini)",
        )
    return (
        "red",
        "User-home host directories are empty. The factory hasn't synced outward yet.",
        f"cd {FACTORY_ROOT} && python3 scripts/omni_factory.py sync-claude --project <name>",
    )


PROBES = [
    ("Factory deployed", _factory_present),
    ("Structural verifier", _verifier_passes),
    ("Host CLIs on PATH", _clis_on_path),
    ("Governed project on disk", _project_present),
    ("Triad surface check", _triad_surface_passes),
    ("User-home host surfaces", _user_home_surfaces),
]


def run_probes() -> list[tuple[str, str, str, str]]:
    out = []
    for name, fn in PROBES:
        try:
            verdict, summary, fix = fn()
        except Exception as exc:
            verdict, summary, fix = "red", f"probe crashed: {exc!r}", ""
        out.append((name, verdict, summary, fix))
    return out


# ---------------------------------------------------------------------------
# check mode
# ---------------------------------------------------------------------------

def cmd_check(_args: argparse.Namespace) -> int:
    print(bold("Agent Forge — machine state check"))
    hr()
    probes = run_probes()
    worst = "green"
    for name, verdict, summary, fix in probes:
        line = f"{verdict_glyph(verdict)} {bold(name)}: {summary}"
        print(line)
        if fix:
            print(f"        fix: {fix}")
        if verdict == "red":
            worst = "red"
        elif verdict == "yellow" and worst != "red":
            worst = "yellow"
    hr()
    print({
        "green": green("All checks green."),
        "yellow": yellow("Critical checks green; some yellows above are worth attention."),
        "red": red("At least one check is red. Fix the first red item, then re-run this command."),
    }[worst])
    return 0 if worst != "red" else 1


# ---------------------------------------------------------------------------
# explain mode — reads EXPLAINERS.md (single source of truth)
# ---------------------------------------------------------------------------

_TOPIC_HEADING_RE = re.compile(r"^##\s+(\S[^\n]*?)\s*$", re.MULTILINE)


def _parse_explainers(text: str) -> dict[str, str]:
    """Parse EXPLAINERS.md into {topic: body} mapping.

    Topics are level-2 headings (## topic-name). Body is everything between
    the heading and the next ## heading or end-of-file. Topic names are
    lowercase kebab identifiers; other ## headings (e.g., section titles)
    are ignored.
    """
    topics: dict[str, str] = {}
    matches = list(_TOPIC_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        topic = m.group(1).strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic):
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        body = body.strip()
        body = re.sub(r"\n---\s*$", "", body).strip()
        topics[topic] = body
    return topics


def _load_explainers() -> dict[str, str]:
    if not EXPLAINERS_PATH.exists():
        return {}
    try:
        return _parse_explainers(EXPLAINERS_PATH.read_text())
    except Exception:
        return {}


def cmd_explain(args: argparse.Namespace) -> int:
    topic = args.topic.lower()
    topics = _load_explainers()
    if not topics:
        print(red(f"EXPLAINERS.md is missing or unparseable at {EXPLAINERS_PATH}"))
        return 1
    if topic not in topics:
        print(red(f"Unknown topic: {topic}"))
        print()
        print("Available topics:")
        for k in sorted(topics):
            print(f"  - {k}")
        return 1
    print(bold(topic.upper()))
    hr()
    print(topics[topic])
    return 0


# ---------------------------------------------------------------------------
# tour mode — redirect message
# ---------------------------------------------------------------------------

def cmd_tour(_args: argparse.Namespace) -> int:
    print(bold("Agent Forge onboarding tour — now runs inline in your host CLI."))
    print()
    print("The seven-beat tour is delivered by the assistant directly in chat,")
    print("not as a subprocess. To run it:")
    print()
    print(f"  - Claude Code: type {bold('/onboarding-guide')}")
    print(f"  - Codex:        type {bold('/onboarding-guide')}")
    print(f"  - Gemini CLI:   type {bold('/onboarding-guide')}")
    print()
    print("For a non-interactive machine-state check from this terminal:")
    print(f"  {dim('python3 ' + str(Path(__file__).resolve()) + ' check')}")
    print()
    print("For a single-concept explainer from this terminal:")
    print(f"  {dim('python3 ' + str(Path(__file__).resolve()) + ' explain <topic>')}")
    print()
    print(dim(f"Available topics: see {EXPLAINERS_PATH}"))
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="onboard",
        description="Agent Forge onboarding helper. Terminal-mode check + explain; "
                    "interactive tour runs inline in Claude / Codex / Gemini.",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_check = sub.add_parser("check", help="Non-interactive machine-state report.")
    p_check.set_defaults(func=cmd_check)

    p_explain = sub.add_parser("explain", help="Plain-English explainer for a single concept.")
    p_explain.add_argument("topic", help="Topic name; see EXPLAINERS.md for the full list.")
    p_explain.set_defaults(func=cmd_explain)

    p_tour = sub.add_parser("tour", help="Prints a redirect to the inline tour (deprecated).")
    p_tour.set_defaults(func=cmd_tour)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        return cmd_tour(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

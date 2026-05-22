#!/usr/bin/env python3
"""Onboarding guide for the Agent Forge factory.

Three modes:
  tour          — interactive guided walkthrough (default).
  check         — non-interactive machine-state report.
  explain TOPIC — plain-English explainer for a single concept.

Tone discipline (read SKILL.md before extending):
  - No sycophancy. No condescension. No untranslated jargon.
  - Show, don't tell. Run the actual commands; show the actual output;
    translate it.
  - Adapt to operator experience but do not lecture context they have.

Read-only and observational. Never modifies MEMORY.md, LESSONS_LEARNED.md,
canonical sources, or bootstrap-project.sh. Only writes its own audit log
at <project>/.forge_state/onboarding.log when invoked under a governed
project root.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# The skill lives at <forge>/skills/global/onboarding-guide/onboard.py.
FACTORY_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROJECTS_ROOT = FACTORY_ROOT.parent

REGISTRY_PATH = FACTORY_ROOT / "registry.json"
PROJECTS_PATH = FACTORY_ROOT / "projects.json"
HOOKS_POLICY = FACTORY_ROOT / "policies" / "hooks.json"
MEMORY_POLICY = FACTORY_ROOT / "policies" / "memory.json"
VERIFIER = FACTORY_ROOT / "scripts" / "verify-agent-forge.py"
TRIAD_VALIDATOR = FACTORY_ROOT / "scripts" / "validate-triad-runtime.py"


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


def section_header(num: int, total: int, title: str) -> None:
    print()
    print(bold(f"Section {num} of {total} — {title}"))
    hr()


def verdict_glyph(verdict: str) -> str:
    return {
        "green": green("[OK]  "),
        "yellow": yellow("[WARN]"),
        "red": red("[FAIL]"),
    }.get(verdict, f"[{verdict.upper()}]")


# ---------------------------------------------------------------------------
# State detection
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
# Tour
# ---------------------------------------------------------------------------

def ask_experience() -> str:
    print()
    print(bold("Quick question before we start."))
    print("Have you used Claude Code, OpenAI Codex, or Gemini CLI before?")
    print("  y  yes, all three regularly")
    print("  p  partially — one or two of them")
    print("  n  no, this is new")
    print("  s  skip — just run the tour without adapting")
    print()
    try:
        ans = input("Answer [y/p/n/s, default n]: ").strip().lower()
    except EOFError:
        ans = ""
    if ans not in ("y", "p", "n", "s"):
        ans = "n"
    return ans


def adapt(level: str, full: str, brief: str) -> str:
    """Return `brief` for experienced operators, `full` for new ones."""
    return brief if level in ("y", "p") else full


def section_1_what_is_this(level: str) -> None:
    section_header(1, 5, "What is this folder?")
    print(adapt(
        level,
        ("This folder is a 'governance factory.' It holds canonical definitions for skills,\n"
         "safety rules, and shared memory, and generates the matching configuration for three\n"
         "AI coding command-line tools (Claude Code, OpenAI Codex, and Gemini CLI). You write\n"
         "a skill or a safety rule once, here, and the factory translates it into each tool's\n"
         "native shape.\n"
         "\n"
         "If you've never used those three tools: each one is a CLI you point at a project\n"
         "and ask in plain English to do work — write tests, fix bugs, refactor a function.\n"
         "Three different vendors, three slightly different ways of configuring the same thing.\n"
         "This factory is the layer that makes them consistent."),
        ("Canonical-first factory. One source of truth (`skills/`, `policies/`, `teams/`,\n"
         "`projects.json`, `global-mcp.json`); generates Claude / Codex / Gemini surfaces.\n"
         "`omni_factory.py` is the engine."),
    ))
    print()
    if REGISTRY_PATH.exists():
        try:
            r = json.loads(REGISTRY_PATH.read_text())
            n = len(r.get("skills", []))
            print(dim(f"Live proof: {REGISTRY_PATH.name} currently registers {n} skills."))
        except Exception:
            print(dim("Live proof: registry.json present but unreadable."))
    print()


def section_2_one_source(level: str) -> None:
    section_header(2, 5, "Three tools, one source of truth")
    print(adapt(
        level,
        ("The thing that makes this factory worth using is fan-out. You edit one canonical\n"
         "file in `_agent_forge/`. The engine reads it and writes three different host-shaped\n"
         "files — one for Claude, one for Codex, one for Gemini. No copy-paste; no drift.\n"
         "\n"
         "Concretely: a skill called `my-skill` lives at `skills/global/my-skill/SKILL.md`.\n"
         "When you run `python3 scripts/omni_factory.py sync-claude --project foo`, the engine\n"
         "writes `foo/.claude/skills/my-skill` (a symlink Claude can see). `sync-codex` writes\n"
         "`foo/.agents/skills/my-skill`. `sync-gemini` writes `foo/.gemini/skills/my-skill`.\n"
         "Same skill, three places, generated from one source."),
        ("Author canonical → render outward. Generated surfaces under `<project>/.claude/`,\n"
         "`<project>/.codex/`, `<project>/.gemini/` are never hand-edited."),
    ))
    print()
    projects = [p for p in _governed_projects() if (PROJECTS_ROOT / p["root"]).exists()]
    if projects:
        sample = PROJECTS_ROOT / projects[0]["root"]
        print(dim(f"Live proof: under {sample.name}, the factory has generated:"))
        for sub in (".claude", ".codex", ".agents", ".gemini"):
            d = sample / sub
            if d.exists():
                count = sum(1 for _ in d.rglob("*") if _.is_file() or _.is_symlink())
                print(dim(f"  {sub}/  ({count} entries)"))
    print()


def section_3_seatbelt(level: str) -> None:
    section_header(3, 5, "The seatbelt")
    print(adapt(
        level,
        ("Coding agents will run shell commands for you. That power is the point. It is also\n"
         "the risk: an over-eager agent can run `git push --force origin main` or `rm -rf $HOME`\n"
         "if you don't have a check in place.\n"
         "\n"
         "The factory ships one such check: `telemetry-guardian`. It is a script that runs\n"
         "before every shell command on all three host CLIs (this is what 'a hook' means —\n"
         "a script that runs before or after a tool call). The guardian reads the command,\n"
         "matches it against a short list of known-dangerous patterns, and either lets it\n"
         "through or refuses.\n"
         "\n"
         "Currently blocked: `--no-verify`, `--no-gpg-sign`, force-push to protected branches,\n"
         "`git reset --hard <ref>`, wildcard home/root deletion, unscoped `terraform destroy`,\n"
         "whole-disk `dd`, recursive 777. The seatbelt is intentionally dumb — predictability\n"
         "beats sophistication for safety gates."),
        ("Pre-tool deny list shared across all three hosts via `policies/hooks.json`. Bypass\n"
         "with `AGENT_FORGE_GUARDIAN=off`; every bypass is logged to `~/.agent-forge/guardian.log`."),
    ))
    print()
    log = Path.home() / ".agent-forge" / "guardian.log"
    if log.exists():
        try:
            count = sum(1 for _ in log.open())
            print(dim(f"Live proof: ~/.agent-forge/guardian.log has {count} recorded events."))
        except Exception:
            pass
    print()


def section_4_shared_brain(level: str) -> None:
    section_header(4, 5, "The shared brain")
    print(adapt(
        level,
        ("Each AI tool has its own way to remember things across sessions. Without coordination,\n"
         "what Claude figures out today is invisible to Codex tomorrow.\n"
         "\n"
         "The factory adds one cross-host file per project: `MEMORY.md` at the project root.\n"
         "All three host CLIs read it. Five sections: build commands, project quirks, active\n"
         "tasks, recent decisions, known failures. Entries are timestamped and tagged with\n"
         "which host wrote them.\n"
         "\n"
         "Append-first: new entries go at the end; nothing silently overwrites prior entries.\n"
         "Secrets are denied at write time (the writer rejects API keys, private-key blocks,\n"
         "and credential-shaped strings)."),
        ("Per-project canonical state at `<project>/MEMORY.md`. Sections defined in\n"
         "`policies/memory.json`. Writer is `skills/global/memory-archivist/archivist.py`\n"
         "with append/validate/summary subcommands."),
    ))
    print()
    projects = [p for p in _governed_projects() if (PROJECTS_ROOT / p["root"]).exists()]
    if projects:
        mem = PROJECTS_ROOT / projects[0]["root"] / "MEMORY.md"
        if mem.exists():
            try:
                size = mem.stat().st_size
                lines = sum(1 for _ in mem.open())
                print(dim(f"Live proof: {projects[0]['name']}/MEMORY.md exists ({size} bytes, {lines} lines)."))
            except Exception:
                pass
    print()


def section_5_what_now(level: str, probes: list[tuple[str, str, str, str]]) -> None:
    section_header(5, 5, "What to do next")
    reds = [(name, fix) for name, v, _, fix in probes if v == "red" and fix]
    yellows = [(name, fix) for name, v, _, fix in probes if v == "yellow" and fix]

    if reds:
        print("Some checks are RED. Fix the first red item before proceeding:")
        print()
        for name, fix in reds:
            print(f"  - {bold(name)}")
            print(f"    {fix}")
        print()
        print("Run this skill in `check` mode after each fix to re-verify:")
        print(dim(f"  python3 {Path(__file__).resolve()} check"))
    elif yellows:
        print("Everything critical is GREEN. Some checks are yellow — usually optional.")
        print()
        for name, fix in yellows:
            print(f"  - {bold(name)}")
            print(f"    {fix}")
        print()
        print("If you want to clear the yellows, run those commands. Otherwise, you're ready.")
    else:
        print(green("Everything is GREEN. You're ready to use the factory."))
        print()
        print("Pick a governed project to start in:")
        print()
        projects = [p for p in _governed_projects() if (PROJECTS_ROOT / p["root"]).exists()]
        if projects:
            sample = projects[0]["name"]
            sample_root = PROJECTS_ROOT / projects[0]["root"]
            print(dim(f"  cd {sample_root}"))
        else:
            sample = "<your-project>"
            print(dim(f"  cd ~/Projects/<your-project>"))
        print()
        print("Then run one of these in a real terminal — pick the host you have authed.")
        print("These are low-risk reads; none of them modify your repo:")
        print()
        # Per-host "Try this" — only show hosts on PATH.
        if shutil.which("claude") is not None:
            print(bold("  Claude Code"))
            print(dim("    claude --version"))
            print(dim('    claude -p "List the skills this project has loaded." --output-format text'))
            print()
        if shutil.which("codex") is not None:
            print(bold("  OpenAI Codex"))
            print(dim("    codex --version"))
            print(dim("    codex /mcp verbose"))
            print()
        if shutil.which("gemini") is not None:
            print(bold("  Gemini CLI"))
            print(dim("    gemini --version"))
            print(dim("    gemini /memory show"))
            print()
        if not any(shutil.which(c) for c in ("claude", "codex", "gemini")):
            print(dim("  (No host CLIs are on PATH. Run scripts/bootstrap-workstation.sh to install them.)"))
            print()
        print("To go deeper:")
        print(dim(f"  cat {FACTORY_ROOT}/README.md"))
        print(dim(f"  cat {FACTORY_ROOT}/docs/HANDOFF.md  # what just shipped"))
        print(dim(f"  cat {FACTORY_ROOT}/docs/SPRINT_BACKLOG.md  # what's coming next"))


def write_audit_log(level: str, sections_completed: int) -> None:
    """Best-effort audit log under the first governed project, if one exists."""
    projects = [p for p in _governed_projects() if (PROJECTS_ROOT / p["root"]).exists()]
    if not projects:
        return
    log_dir = PROJECTS_ROOT / projects[0]["root"] / ".forge_state"
    if not log_dir.exists():
        return
    log_path = log_dir / "onboarding.log"
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "experience_level": level,
        "sections_completed": sections_completed,
    }
    try:
        with log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def cmd_quick_summary(probes: list[tuple[str, str, str, str]]) -> None:
    """Non-interactive 90-second summary. Used by `tour --quick`.

    Skips the experience prompt and the five expanded sections. Prints a
    five-bullet pitch + the probe verdicts + the "what to do next" branch.
    Intended for operators who want the gist without being marched through
    the full guided flow.
    """
    print(bold("Agent Forge — quick summary"))
    print(dim("Read-only; nothing here modifies your repo."))
    print()
    bullets = [
        ("What this folder is",
         "A single source of truth that generates the same skills, safety rules, and shared "
         "memory for three AI coding CLIs (Claude / Codex / Gemini)."),
        ("Why",
         "Author one canonical file; the engine renders it into each host's native shape. "
         "No drift, no triple maintenance."),
        ("The seatbelt",
         "telemetry-guardian runs before every shell command on every host and refuses "
         "obviously dangerous patterns (--no-verify, force-push to main, rm -rf $HOME, etc.)."),
        ("The shared brain",
         "<project>/MEMORY.md is one file all three hosts read and write. Build commands, "
         "project quirks, recent decisions, known failures."),
        ("The gate",
         "validate-triad-runtime.py asks each host's CLI 'can you see what we shipped?' — "
         "files on disk are necessary; CLI reachability is the sufficient proof."),
    ]
    for title, body in bullets:
        print(f"  - {bold(title)}: {body}")
    print()
    print(bold("Machine state:"))
    for name, verdict, summary, _fix in probes:
        print(f"  {verdict_glyph(verdict)} {name}: {summary}")
    print()
    section_5_what_now("s", probes)
    print()
    print(dim(f"For the full guided tour: python3 {Path(__file__).resolve()} tour"))


def cmd_tour(args: argparse.Namespace) -> int:
    probes = run_probes()
    if getattr(args, "quick", False):
        cmd_quick_summary(probes)
        return 0
    print(bold("Agent Forge Onboarding Guide"))
    print(dim("Five short sections. Plain English. Read-only — nothing you do here will modify your repo."))
    print()
    print(dim(f"Factory root: {FACTORY_ROOT}"))
    level = ask_experience()

    sections_completed = 0
    try:
        section_1_what_is_this(level); sections_completed += 1
        section_2_one_source(level);   sections_completed += 1
        section_3_seatbelt(level);     sections_completed += 1
        section_4_shared_brain(level); sections_completed += 1
        section_5_what_now(level, probes); sections_completed += 1
    finally:
        write_audit_log(level, sections_completed)

    print()
    hr()
    print(dim("End of tour. Run with `check` to re-verify state at any time."))
    return 0


# ---------------------------------------------------------------------------
# Check mode
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
# Explainers
# ---------------------------------------------------------------------------

EXPLAINERS = {
    "factory": (
        "The 'factory' is the `_agent_forge/` folder. It is a single source of truth that "
        "holds canonical definitions of skills, safety rules, shared memory sections, team "
        "manifests, and MCP server inventory, plus a Python engine (`scripts/omni_factory.py`) "
        "that translates those definitions into Claude Code, OpenAI Codex, and Gemini CLI "
        "configuration files. You only ever edit the canonical sources; the engine generates "
        "the host-specific files. After every change, a runtime validator asks each host's "
        "CLI 'can you actually see what we just shipped?' — that's the gate."
    ),
    "skill": (
        "A skill is a packaged, reusable workflow. It lives at `skills/global/<name>/SKILL.md` "
        "(for cross-project skills) or `skills/projects/<project>/<name>/SKILL.md` (for project-"
        "local). The frontmatter declares the metadata (which hosts, which projects, workflow "
        "vs. expert class). The body is the durable instruction text. When you sync the factory, "
        "each skill gets installed under the right directory for each host CLI."
    ),
    "hook": (
        "A hook is a script that runs at a specific moment in a host CLI's tool-call lifecycle. "
        "The most common hook in this factory is `pre-tool-execution-guardian` — it runs before "
        "every Bash tool call, reads the command, and either lets it through or refuses. Hook "
        "records live in `policies/hooks.json`. The factory translates one canonical record into "
        "each host's native event names (Claude `PreToolUse`, Codex `pre_tool_use`, Gemini "
        "`BeforeTool`)."
    ),
    "mcp": (
        "MCP (Model Context Protocol) is the open standard that lets an AI agent call external "
        "tools — GitHub, Slack, your internal services. The factory declares shared MCP servers "
        "in `global-mcp.json`. When the factory syncs, it writes each host's native MCP config: "
        "Claude `<project>/.mcp.json`, Codex `<project>/.codex/config.toml`, Gemini "
        "`<project>/.gemini/settings.json`. The file is currently empty by design until the first "
        "real shared MCP server is added."
    ),
    "memory": (
        "The shared memory layer is one Markdown file per project, at `<project>/MEMORY.md`. "
        "Five sections: build commands, project quirks, active tasks, recent decisions, known "
        "failures. The schema is defined in `policies/memory.json`. All three host CLIs read this "
        "file. The `memory-archivist` skill (`append`/`validate`/`summary`) writes to it; entries "
        "are timestamped and tagged by host. Append-first; secrets-deny at write time."
    ),
    "sandbox": (
        "Each host CLI runs your tool calls inside some kind of isolation. Codex CLI uses Linux "
        "bubblewrap (`bwrap`) on Debian/Ubuntu and macOS Seatbelt on macOS. Claude has permission "
        "modes (`default`, `plan`, `acceptEdits`, `auto`, `bypassPermissions`). Gemini gates on "
        "trusted-folder state. The factory is sandbox-aware: when the runtime validator can't "
        "inspect Codex via its shell tool because bwrap blocked the loopback interface, it "
        "escalates to filesystem evidence per documented doctrine."
    ),
    "triad-validator": (
        "`scripts/validate-triad-runtime.py` is the runtime gate. It does three things per host: "
        "asks the actual CLI to enumerate its visible skills (the surface check), confirms the "
        "seeded `telemetry-guardian` hook is registered with the right event name (the hook "
        "surface check), and confirms the `MEMORY.md` shared brain is reachable (the memory "
        "surface check). Run it after any canonical change. With `--probe-invocations`, it also "
        "fires a real test command and observes whether the hook actually intercepts it."
    ),
    "guardian": (
        "`telemetry-guardian` is the universal pre-tool seatbelt. POSIX shell script at "
        "`skills/global/telemetry-guardian/guardian.sh`. Reads one tool invocation on stdin, "
        "matches the command against a fixed deny list, exits 0 to allow or 1 to block. Bypass "
        "via `AGENT_FORGE_GUARDIAN=off` env var; every bypass is logged. Intentionally dumb — "
        "predictability beats sophistication for safety gates. The deny list covers `--no-verify`, "
        "force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, "
        "whole-disk `dd`, recursive 777, `--no-gpg-sign`, explicit `git reset --hard <ref>`."
    ),
    "bootstrap": (
        "Bootstrapping is the one-time setup. `scripts/bootstrap-workstation.sh` installs the "
        "three host CLIs (Claude / Codex / Gemini) on a fresh machine. `scripts/bootstrap-"
        "project.sh --name <foo>` creates a new governed project with the minimum required "
        "files and immediately syncs Claude / Codex / Gemini surfaces into it. `scripts/deploy-"
        "and-bootstrap.sh` is the one-shot operator path from a freshly unpacked suitcase: "
        "deploys the factory, then offers to run the workstation bootstrap."
    ),
    "validation-pyramid": (
        "The factory uses three nested gates of increasing depth and decreasing speed. "
        "Level 1 — `verify-agent-forge.py` — is the cheapest: it checks file presence, JSON "
        "parse, schema-shape, and that referenced scripts exist on disk. Run constantly. "
        "Level 2 — `validate-triad-runtime.py` (default mode) — asks each host's CLI to "
        "enumerate skills, then confirms the seeded telemetry-guardian hook is registered with "
        "the host's expected event key (PreToolUse / PreToolUse / BeforeTool) and that the "
        "MEMORY.md surface is reachable. Mandatory after every canonical change. "
        "Level 3 — `validate-triad-runtime.py --probe-invocations` — fires a real test command "
        "on each host CLI and observes whether the hook actually intercepts it. Slow, opt-in, "
        "and the only level that catches host-native semantic drift (the kind that broke the "
        "Gemini hook silently for two sprints in 2026-04). Each level is necessary; only the "
        "third is sufficient."
    ),
    "governed-project": (
        "A governed project is one declared in `projects.json` and managed by the factory. "
        "On a fresh install, no projects are pre-wired — `projects.json` is an empty list. "
        "Adding your first one means: (1) add an entry to `projects.json` with `name`, `root`, "
        "and `required_files`; (2) run `./scripts/bootstrap-project.sh --name <name>`. The "
        "bootstrap creates the minimum required files, then immediately syncs the factory's "
        "skills, hooks, MEMORY.md, and forge_state into the project's host-native directories "
        "(`.claude/`, `.codex/`, `.agents/`, `.gemini/`). Generated surfaces are never "
        "hand-edited; re-run sync after any canonical change. The `required_files` declaration "
        "is what the verifier uses to confirm the project still has the minimum footprint."
    ),
    "suitcase": (
        "The 'suitcase' is the portable export of the factory you can carry to a fresh machine "
        "or VM without copying secrets or per-machine residue. `scripts/factory-export.sh` "
        "produces `agent-forge-suitcase-<timestamp>.tar.gz` (and `.zip`) in `exports/`. The "
        "bundle includes `_agent_forge/` canonical sources, the sync/bootstrap/validation "
        "scripts, and the doctrine docs — no `.env`, no auth tokens, no machine-local caches. "
        "On the target machine, `./_agent_forge/scripts/deploy-and-bootstrap.sh` is the one-"
        "shot path: deploys the factory into `~/Projects`, syncs the global host surfaces, and "
        "offers to run the workstation bootstrap (which installs the three host CLIs). The "
        "host-specific surfaces (`<project>/.claude/`, `.codex/`, `.gemini/`) and per-project "
        "`MEMORY.md` are re-rendered on first sync; they are NOT carried in the suitcase. "
        "This is the canonical-first doctrine in practice: ship the source of truth; let the "
        "engine generate the host views fresh on the target."
    ),
}


def cmd_explain(args: argparse.Namespace) -> int:
    topic = args.topic.lower()
    if topic not in EXPLAINERS:
        print(red(f"Unknown topic: {topic}"))
        print()
        print("Available topics:")
        for k in sorted(EXPLAINERS):
            print(f"  - {k}")
        return 1
    print(bold(topic.upper()))
    hr()
    print(EXPLAINERS[topic])
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="onboard",
        description="Agent Forge onboarding guide. Read-only. Three modes.",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_tour = sub.add_parser("tour", help="Interactive guided walkthrough (default).")
    p_tour.add_argument(
        "--quick",
        action="store_true",
        help="Skip the experience prompt and the five guided sections; print a "
             "non-interactive 90-second summary instead. Useful for operators "
             "who want the gist without being marched through the full tour.",
    )
    p_tour.set_defaults(func=cmd_tour)

    p_check = sub.add_parser("check", help="Non-interactive machine-state report.")
    p_check.set_defaults(func=cmd_check)

    p_explain = sub.add_parser("explain", help="Plain-English explainer for a single concept.")
    p_explain.add_argument("topic", help="One of: " + ", ".join(sorted(EXPLAINERS)))
    p_explain.set_defaults(func=cmd_explain)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        # Default: tour.
        args.func = cmd_tour
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

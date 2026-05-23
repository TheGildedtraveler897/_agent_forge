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

def pause(prompt: str = "Press [Enter] to continue", no_pause: bool = False) -> None:
    """Wait for the operator to press Enter. Skipped on non-TTY or when --no-pause."""
    if no_pause or not _is_tty():
        return
    try:
        input(dim(f"  {prompt} ") + dim("→ "))
    except EOFError:
        pass


def prompt_choice(question: str, options: list[tuple[str, str, str]], default: str) -> str:
    """Numbered choice prompt. options is a list of (key, label, description) tuples.

    Returns the chosen key. Non-TTY input returns the default; invalid input
    returns the default. Bracket the default key with a star in the prompt.
    """
    print()
    print(bold(question))
    print()
    for key, label, desc in options:
        marker = "*" if key == default else " "
        print(f"  [{key}]{marker} {label}")
        if desc:
            print(f"      {dim(desc)}")
    print()
    keys = "/".join(o[0] for o in options)
    try:
        ans = input(f"  Your choice [{keys}, default {default}]: ").strip().lower()
    except EOFError:
        ans = ""
    valid = {o[0] for o in options}
    if ans not in valid:
        ans = default
    return ans


def ask_yn(question: str, default: bool = True) -> bool:
    label = "Y/n" if default else "y/N"
    try:
        ans = input(f"  {question} [{label}]: ").strip().lower()
    except EOFError:
        ans = ""
    if not ans:
        return default
    return ans.startswith("y")


def _detect_cli_state() -> tuple[list[str], list[str]]:
    """Return (present, missing) for the three host CLIs."""
    present, missing = [], []
    for cli in ("claude", "codex", "gemini"):
        (present if shutil.which(cli) else missing).append(cli)
    return present, missing


def _count_skills() -> int:
    if not REGISTRY_PATH.exists():
        return 0
    try:
        return len(json.loads(REGISTRY_PATH.read_text()).get("skills", []))
    except Exception:
        return 0


def _print_translation_table() -> None:
    rows = [
        ("Concept",         "Claude",     "Codex",          "Gemini"),
        ("Workflow skill",  "command",    "skill",          "command"),
        ("Expert skill",    "subagent",   "(none native)",  "subagent"),
        ("Slash syntax",    "/name",      "(no slash)",     "/name"),
        ("Pre-tool hook",   "PreToolUse", "PreToolUse",     "BeforeTool"),
        ("Stop event",      "Stop",       "Stop",           "SessionEnd"),
        ("MCP config",      ".mcp.json",  "config.toml",    "settings.json"),
        ("Memory target",   "native",     "sidecar",        "sidecar"),
        ("Boot file",       "CLAUDE.md",  "AGENTS.md",      "GEMINI.md"),
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    for i, row in enumerate(rows):
        line = "  " + "  ".join(row[c].ljust(widths[c]) for c in range(4))
        if i == 0:
            print(bold(line))
            print("  " + "  ".join("-" * widths[c] for c in range(4)))
        else:
            print(line)


def _get_example_skills() -> tuple[str, str]:
    """Return (workflow_name, expert_name) from the registry, or defaults."""
    workflow, expert = "tdd-engineer", "legal-counsel"
    if not REGISTRY_PATH.exists():
        return workflow, expert
    try:
        data = json.loads(REGISTRY_PATH.read_text())
        for skill in data.get("skills", []):
            cls = skill.get("capability_class")
            if cls == "workflow" and workflow == "tdd-engineer":
                workflow = skill.get("name", workflow)
            elif cls == "expert" and expert == "legal-counsel":
                expert = skill.get("name", expert)
    except Exception:
        pass
    return workflow, expert


CLI_INFO: dict[str, dict[str, str]] = {
    "claude": {
        "vendor": "Anthropic",
        "tagline": "Best memory story; native slash commands and subagents.",
        "url": "https://docs.anthropic.com/claude/docs/claude-code",
        "command": "npm install -g @anthropic-ai/claude-cli  # or follow the docs",
        "beginner": "Use Claude when you need to change 15 files at once or rewrite a whole system. It's the best at looking at the big picture and not forgetting what you asked.",
        "senior": "Claude excels at deep-context, multi-file refactoring and autonomous state management. Default to Claude for sweeping architecture changes or hunting down complex bugs across module boundaries.",
    },
    "codex": {
        "vendor": "OpenAI",
        "tagline": "Strongest default sandbox (bwrap on Linux, Seatbelt on macOS).",
        "url": "https://platform.openai.com/docs/codex",
        "command": "Follow the docs link — install method varies by platform.",
        "beginner": "Use Codex when you have a very specific, repeatable task, like writing tests or formatting code perfectly.",
        "senior": "Codex is your deterministic engine. Use it for heavily plugin-driven workflows, localized syntax transformations, and structured data extraction.",
    },
    "gemini": {
        "vendor": "Google",
        "tagline": "Vision-capable; cheapest non-trivial tier.",
        "url": "https://ai.google.dev/gemini-api/docs/cli",
        "command": "npm install -g @google/gemini-cli  # or follow the docs",
        "beginner": "Use Gemini when you want something fast, or if you need to pull in information from the web or Google Workspace to help you code.",
        "senior": "Gemini offers the lowest latency and massive context windows. Use it for rapid prototyping, generating boilerplate, or digesting massive logs/documentation directly into your terminal.",
    },
}


def install_gate(no_pause: bool = False) -> None:
    """Detect missing host CLIs and offer per-CLI install hand-holding."""
    present, missing = _detect_cli_state()
    print()
    print(bold("◆ Install check"))
    print()
    for cli in ("claude", "codex", "gemini"):
        if cli in present:
            print(f"  {green('✓')} {cli} is on PATH")
        else:
            print(f"  {red('✗')} {cli} is not installed yet")
    print()
    if not missing:
        print("  All three host CLIs are installed. Nothing to do here.")
        print()
        pause(no_pause=no_pause)
        return

    print(f"  You're missing: {bold(', '.join(missing))}")
    print()
    choice = prompt_choice(
        "Want help installing them?",
        [
            ("w", "Walk me through it",       "Per-CLI: what it is, why you'd pick it, install command."),
            ("c", "Just show me the commands", "Brief and direct, no description."),
            ("s", "Skip for now",              "Come back later when you're ready."),
        ],
        default="w",
    )
    if choice == "s":
        print()
        print("  Fine. When you're ready:")
        print(dim("    python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py tour"))
        print()
        pause(no_pause=no_pause)
        return

    print()
    print(dim("  The factory ships scripts/bootstrap-workstation.sh which can install"))
    print(dim("  all three in one shot. Or install each one individually below."))
    print()
    for cli in missing:
        info = CLI_INFO[cli]
        print(bold(f"  {cli}  ({info['vendor']})"))
        if choice == "w":
            print(f"    {info['tagline']}")
        print(f"    Docs: {info['url']}")
        print(f"    {dim(info['command'])}")
        print()
    print(bold("  Or install everything at once:"))
    print(dim("    bash ~/Projects/_agent_forge/scripts/bootstrap-workstation.sh"))
    print()
    pause(no_pause=no_pause)


def write_audit_log(level: str, sections_completed: int, role: str = "") -> None:
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
        "role": role,
        "sections_completed": sections_completed,
    }
    try:
        with log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def cmd_quick_summary(probes: list[tuple[str, str, str, str]]) -> None:
    """Non-interactive 90-second summary. Used by `tour --quick`.

    Five bullets + probe verdicts + the first red fix command if any.
    No paced beats; no questions. For operators who want the gist.
    """
    print(bold("Agent Forge — quick summary"))
    print(dim("Read-only; nothing here modifies your repo."))
    print()
    bullets = [
        ("What this folder is",
         "A single source of truth that generates the same skills, safety rules, and "
         "shared memory for three AI coding CLIs (Claude / Codex / Gemini)."),
        ("Why",
         "Author one canonical file; the engine renders it into each host's native shape. "
         "No drift, no triple maintenance."),
        ("The seatbelt",
         "telemetry-guardian runs before every shell command on every host and refuses "
         "obviously dangerous patterns."),
        ("The shared brain",
         "<project>/MEMORY.md — one file all three hosts read and write."),
        ("The gate",
         "validate-triad-runtime.py asks each host's CLI 'can you see what we shipped?'"),
    ]
    for title, body in bullets:
        print(f"  - {bold(title)}: {body}")
    print()
    print(bold("Machine state:"))
    for name, verdict, summary, _fix in probes:
        print(f"  {verdict_glyph(verdict)} {name}: {summary}")
    print()
    reds = [(n, fix) for n, v, _, fix in probes if v == "red" and fix]
    if reds:
        print(bold("Next action:"))
        for name, fix in reds:
            print(f"  {name} → {fix}")
        print()
    print(dim(f"For the full guided tour: python3 {Path(__file__).resolve()} tour"))


def cmd_tour(args: argparse.Namespace) -> int:
    """Paced, interactive tour. One beat at a time; questions drive the flow."""
    probes = run_probes()
    if getattr(args, "quick", False):
        cmd_quick_summary(probes)
        return 0
    no_pause = getattr(args, "no_pause", False)

    # Greeting ---------------------------------------------------------------
    print()
    print(bold("=" * 60))
    print(bold("  Agent Forge — quick tour"))
    print(bold("=" * 60))
    print()
    print("  You just unzipped a factory that makes three AI coding tools")
    print(f"  ({bold('Claude')}, {bold('Codex')}, {bold('Gemini')}) speak the same language.")
    print()
    print("  Same skill, same safety rule, same shared brain — rendered")
    print("  into each tool's native format from one source.")
    print()
    print(dim("  I'll keep this short. Press [Enter] each time you're ready to"))
    print(dim("  move on. Ctrl+C if you want to bail."))
    print()
    pause("Press [Enter] to start", no_pause=no_pause)

    # Q1 — Experience --------------------------------------------------------
    level = prompt_choice(
        "First — have you used any of the three AI coding CLIs before?",
        [
            ("a", "Yes, two or three of them", "I'll keep things terse."),
            ("o", "One of them",                "I'll translate jargon the first time."),
            ("n", "None yet — starting fresh",  "I'll translate every term."),
            ("u", "Not sure — check for me",    "I'll inspect your PATH."),
        ],
        default="n",
    )
    if level == "u":
        present, missing = _detect_cli_state()
        print()
        if present:
            print(f"  On your PATH: {green(', '.join(present))}")
        if missing:
            print(f"  Missing: {yellow(', '.join(missing))}")
        if not present:
            print(dim("  None of the three installed yet. That's fine — keep going."))
            level = "n"
        elif len(present) >= 2:
            level = "a"
        else:
            level = "o"
        print()
        pause(no_pause=no_pause)

    # Q2 — Role --------------------------------------------------------------
    role = prompt_choice(
        "Quick one — what brings you here today?",
        [
            ("c", "Curious — what is this?",          ""),
            ("b", "Builder — extend or contribute",   ""),
            ("o", "Operator — set this up for a team", ""),
            ("d", "Decider — should we adopt this?",  ""),
        ],
        default="c",
    )

    # Beat 1 — What is this? -------------------------------------------------
    print()
    print(bold("◆ This folder is a factory."))
    print()
    print("  You write a skill once — a short markdown file describing what")
    print("  an AI tool should do. The factory turns that one file into three")
    print("  different configurations, one for each AI tool.")
    print()
    print("  You don't copy-paste. You don't maintain three versions.")
    print("  The factory does the translation.")
    print()
    n = _count_skills()
    if n:
        print(f"  {green('✓')} Right now this factory holds {bold(str(n))} skills.")
        print()
    pause(no_pause=no_pause)

    # Beat 1.5 — Meet the Crew (Dynamic based on PATH & Role) -----------------
    print()
    print(bold("◆ Meet the Crew"))
    print()
    print("  You have up to three AI tools available. Here is when to use them.")
    print()
    tone_key = "beginner" if level == "n" or role == "c" else "senior"
    
    # We only show installed CLIs to reduce noise, unless none are installed
    present_clis, _ = _detect_cli_state()
    clis_to_show = present_clis if present_clis else ("claude", "codex", "gemini")
    
    for cli in clis_to_show:
        info = CLI_INFO[cli]
        print(f"  {bold(cli.capitalize())} ({info['vendor']})")
        print(f"    {dim(info[tone_key])}")
        print()
    pause(no_pause=no_pause)

    # Beat 1.6 — The Architecture (Hub and Spoke) ----------------------------
    print()
    print(bold("◆ The Architecture: Agents vs. Subagents"))
    print()
    print("  The terms can be confusing. Let's look at how the tools in this folder")
    print("  actually run on your machine:")
    print()
    
    wf_name, ex_name = _get_example_skills()
    
    print("        [ You (The Operator) ]")
    print("                 │")
    print("                 ▼")
    print(f"      [ Main CLI ({clis_to_show[0].capitalize() if present_clis else 'Claude'}) ]   <-- The 'Agent' (Manager / Hub)")
    print("          │             │")
    print(dim("     (Workflows)   (Delegation)"))
    print("          │             │")
    print("          ▼             ▼")
    print(f"   {green(f'[/{wf_name}]')}   {yellow(f'[@{ex_name}]')} <-- 'Subagents' (Specialists / Spokes)")
    print()
    print(f"  {green('Workflows')} are instant actions that run in your current chat.")
    print(f"  {yellow('Subagents')} are isolated background workers. We spin them up so their")
    print("  massive context window doesn't clutter your main terminal.")
    print()
    pause(no_pause=no_pause)

    # Beat 2 — The tease -----------------------------------------------------
    print()
    print(bold("◆ Here's the trick."))
    print()
    print("  Each AI tool calls things by different names.")
    print()
    print(f"    {bold('Claude')} calls it a 'slash command' or a 'subagent.'")
    print(f"    {bold('Codex')}  calls it a 'skill.'")
    print(f"    {bold('Gemini')} calls it a 'command' or a 'subagent.'")
    print()
    print("  Same idea. Three names.")
    print()
    pause("Press [Enter] to see all the names side-by-side", no_pause=no_pause)

    # Beat 3 — The translation table (payoff) --------------------------------
    print()
    print(bold("◆ The translation table"))
    print()
    _print_translation_table()
    print()
    print(dim("  Three vendors, similar primitives, different names."))
    print(dim("  You don't have to memorize this — the factory translates."))
    print()
    pause(no_pause=no_pause)

    # Beat 4 — The seatbelt and Danger Zone -----------------------------------
    print()
    print(bold("◆ The Danger Zone (Seatbelts & Collisions)"))
    print()
    print("  Agents will run shell commands for you. That's the point.")
    print("  It's also the risk.")
    print()
    print(f"  {bold('Rule 1: The Seatbelt')}")
    print("  The factory runs one check before every shell command on every")
    print("  AI tool. It refuses obviously destructive patterns:")
    print(f"    {dim('- force-push to main, rm -rf $HOME, --no-verify')}")
    print()
    print(f"  {bold('Rule 2: File Collisions')}")
    print("  Never let two subagents modify the exact same file at the exact same")
    print("  time. They will overwrite each other. Use `subagent-dispatcher` for")
    print("  sequential delegation, or isolate them in separate Git worktrees.")
    print()
    log = Path.home() / ".agent-forge" / "guardian.log"
    if log.exists():
        try:
            n_events = sum(1 for _ in log.open())
            print(f"  {green('✓')} The seatbelt has logged {bold(str(n_events))} events on this machine.")
            print()
        except Exception:
            pass
    pause(no_pause=no_pause)

    # Beat 5 — The shared brain ----------------------------------------------
    print()
    print(bold("◆ The shared brain"))
    print()
    print("  All three AI tools read one file per project: MEMORY.md.")
    print()
    print("  Build commands. Project quirks. Recent decisions. Known failures.")
    print("  What Claude learns today, Codex sees tomorrow.")
    print()
    print("  Append-first. Secrets blocked at write time.")
    print()
    pause(no_pause=no_pause)

    # Beat 6 — Install gate --------------------------------------------------
    install_gate(no_pause=no_pause)

    # Beat 7 — Sandbox Quest (Interactive Handoff) ---------------------------
    print()
    print(bold("◆ Sandbox Quest: Try it now"))
    print()
    print("  You've read the theory. Let's prove it works.")
    print("  Copy and paste the command below into your terminal to trigger a")
    print("  harmless read-only workflow.")
    print()
    
    quest_cmd = "claude -p \"/explain mcp\""
    if present_clis:
        if "claude" in present_clis:
            quest_cmd = "claude -p \"/explain mcp\""
        elif "gemini" in present_clis:
            quest_cmd = "gemini -p \"/explain mcp\""
        elif "codex" in present_clis:
            quest_cmd = "codex -- /explain mcp"
    
    print(f"    {bold(green(quest_cmd))}")
    print()
    print("  Working mental model now in place:")
    print("    - Hub & Spoke (Agents vs Subagents)")
    print("    - The Seatbelt & File Collisions")
    print("    - The Shared Brain")
    print()
    print(green("  Welcome to Agent Forge."))
    print()

    write_audit_log(level, sections_completed=7, role=role)
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
    "claude-cli": (
        "Claude Code is Anthropic's coding-agent CLI. It loads `CLAUDE.md` boot files "
        "hierarchically (current directory walking up), has a true machine-local auto-"
        "memory at `~/.claude/projects/<encoded>/memory/MEMORY.md`, and exposes two kinds "
        "of authored capabilities: slash commands invoked as `/name` and subagents invoked "
        "as `@name`. Settings live at `~/.claude/settings.json` (user-global) and "
        "`<project>/.claude/settings.json` (project-local, takes precedence). Permission "
        "modes range from `default` (ask) to `bypassPermissions` (don't ask). "
        "When to pick this host: when you want the deepest native primitive coverage and "
        "the most polished memory story."
    ),
    "codex-cli": (
        "OpenAI Codex is a coding-agent CLI with a strong default sandbox. On Linux it "
        "uses bubblewrap (`bwrap`); on macOS it uses Seatbelt. There is no slash-command "
        "convention — skills are invoked by name through delegation. The boot file is "
        "`AGENTS.md` (walks up the directory tree like Claude's `CLAUDE.md`). Codex has "
        "no native auto-memory, so Agent Forge bridges the canonical `MEMORY.md` to a "
        "sidecar at `<project>/.codex/memory/AGENTS_MEMORY.md` and points Codex at it. "
        "Settings live in `<project>/.codex/config.toml`. "
        "When to pick this host: when you want the strongest default sandbox or when "
        "you're on a network where Codex is the only allowed coding agent."
    ),
    "gemini-cli": (
        "Gemini CLI is Google's coding-agent CLI. It loads `GEMINI.md` boot files "
        "hierarchically and is vision-capable. Skills are delivered as TOML or Markdown "
        "into `<project>/.gemini/commands/` and `<project>/.gemini/agents/`. Gemini "
        "supports a subset of hook events — `permission_request` and `user_prompt_submit` "
        "are not exposed, so the factory drops those records at render time and documents "
        "the exclusion. Settings live in `<project>/.gemini/settings.json`. Like Codex, "
        "Gemini has no native auto-memory; a sidecar at `<project>/.gemini/memory/"
        "MEMORY.md` carries the bridge. "
        "When to pick this host: when you need a vision-capable agent or want the most "
        "cost-efficient non-trivial tier."
    ),
    "agent": (
        "An agent is an autonomous something that can read, write, plan, call tools, "
        "and remember between turns. In this factory, an agent is one of the three host "
        "CLIs (Claude, Codex, or Gemini) running on your machine. A skill is what an "
        "agent reads to know how to behave for a specific job. A subagent is an agent "
        "dispatched by another agent to handle a focused task with its own fresh "
        "context — useful when you want to keep the main agent's working memory clean "
        "while a side task runs. The factory calls workflow-class skills 'commands' on "
        "Claude/Gemini and 'skills' on Codex; it calls expert-class skills 'subagents' "
        "on Claude/Gemini (Codex has no native expert-agent primitive)."
    ),
    "agent-team": (
        "A team in this factory is a portable role contract. It lives at `teams/<name>."
        "json` and says 'a research team has these roles, escalates like this, collapses "
        "like this' — but it is a governance manifest, not a process the host runs. "
        "Teams describe how a group of skills and agents would work together on a "
        "complex job; the operator (you) decides whether to actually dispatch them. The "
        "seeded teams (assessment, bootstrap, delivery, governance, improvement, "
        "planning, research) carry `claude_mapping`, `codex_mapping`, and `gemini_mapping` "
        "blocks that name the host-native primitives each team prefers."
    ),
    "host-dirs": (
        "The factory writes to four different config directory names depending on the "
        "host. Claude reads from `.claude/`. Codex reads from `.codex/` and also from "
        "`.agents/` (a legacy Codex convention for skills, kept for back-compat). Gemini "
        "reads from `.gemini/`. The factory keeps these in sync from one canonical "
        "source, so if you ever see drift between them, that's a bug — not a feature. "
        "The triad runtime validator (`validate-triad-runtime.py`) is the gate that "
        "catches that drift before it ships."
    ),
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
        help="Skip the prompts and the paced beats; print a non-interactive "
             "90-second summary instead. Useful for operators who want the gist.",
    )
    p_tour.add_argument(
        "--no-pause",
        action="store_true",
        help="Run the full tour without pausing for [Enter] between beats. "
             "Used by smoke tests; not recommended for first-time operators.",
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

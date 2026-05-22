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


def ask_role() -> str:
    print()
    print(bold("One more quick question."))
    print("Which best describes why you're here today?")
    print("  c  curious — I want to understand what this is")
    print("  b  builder — I want to extend or contribute")
    print("  o  operator — I'm setting up the factory for a team")
    print("  d  decider — I'm evaluating whether to adopt this")
    print("  s  skip — just run the tour without role tuning")
    print()
    try:
        ans = input("Answer [c/b/o/d/s, default c]: ").strip().lower()
    except EOFError:
        ans = ""
    if ans not in ("c", "b", "o", "d", "s"):
        ans = "c"
    return ans


# Role-tuned closing paragraphs. One per (section_number, role) pair.
# Role 's' (skip) returns empty; sections render no closing paragraph for skippers.
ROLE_TAILS: dict[tuple[int, str], str] = {
    (1, "c"): "If you remember one thing from this section: it's a factory. You feed it definitions, it spits out three different configurations from one source.",
    (1, "b"): "If you'll extend this: every canonical file under `skills/`, `policies/`, `teams/`, or `global-mcp.json` is hand-edited; everything under `<project>/.claude/`, `.codex/`, `.gemini/` is generated. Don't hand-edit generated files — they'll be overwritten on next sync.",
    (1, "o"): "For team rollout: deploy this factory once per workstation via `scripts/deploy-and-bootstrap.sh`. Govern your team's projects by adding entries to `projects.json` and running `scripts/bootstrap-project.sh --name <name>` for each.",
    (1, "d"): "Adoption decision frame: the factory's value is one-author/three-deliver. Cost is one Python engine + a handful of skills/ and policies/ files. No long-running service; no per-user backend.",
    (2, "c"): "The takeaway: you write one file, and it shows up correctly in all three AI tools without you copying anything.",
    (2, "b"): "Authoring rhythm: edit canonical (`skills/global/<name>/SKILL.md`), run `python3 scripts/omni_factory.py sync-{claude,codex,gemini} --project <name>` for the host you want to test against, then run `validate-triad-runtime.py` to prove all three saw it.",
    (2, "o"): "Operationally, the three syncs are independent. You can deploy a Claude-only team today and add Codex/Gemini coverage later without re-authoring anything.",
    (2, "d"): "Architectural diligence: the canonical → renderer → host-native chain means any new host can be added by writing one renderer. The factory is not Claude-coupled.",
    (3, "c"): "You don't have to memorize this. If a coworker says 'Claude calls it a slash command' and you've seen Codex call it a skill, you'll know they mean the same thing.",
    (3, "b"): "When you author a new skill, you write one `SKILL.md` with `capability_class: workflow` or `expert`. The renderer decides which native primitive it lands as on each host.",
    (3, "o"): "When debugging cross-host drift, the table is your first stop: confirm the rendered file is in the right host-native location and uses the expected event/key name.",
    (3, "d"): "The translation table is the contract that lets the factory survive a vendor renaming a primitive — only the renderer changes, never the authoring surface.",
    (4, "c"): "You can ignore the deny-list details. The point: there's a short list of obviously bad commands the factory refuses on your behalf, on every host, before you can shoot yourself in the foot.",
    (4, "b"): "Extending the guardian: edit `skills/global/telemetry-guardian/guardian.py` to add a deny-list entry, then re-sync. Keep the additions narrow — the seatbelt is intentionally dumb.",
    (4, "o"): "For team rollout, document the bypass mechanism (`AGENT_FORGE_GUARDIAN=off`) and the log location (`~/.agent-forge/guardian.log`) so on-call can audit any bypass after the fact.",
    (4, "d"): "Procurement framing: the guardian is a deterministic policy gate, not an ML classifier. Its deny list is auditable and reversible. Bypass is logged. That posture passes most security reviews.",
    (5, "c"): "The shared brain is just one Markdown file. You can open it in any editor and read what the AI tools have learned about your project.",
    (5, "b"): "When you want an agent to remember something across sessions, append it to `<project>/MEMORY.md` via the `memory-archivist` skill — never edit the anchor lines by hand.",
    (5, "o"): "Bridge lifecycle hooks (`session_start` outbound, `stop` inbound) keep canonical `MEMORY.md` in sync with each host's native or sidecar memory target. The triad validator records `memory_pass` and `bridge_pass` as separate gates.",
    (5, "d"): "The shared brain is opt-in append-first with a secrets-deny filter at write time. That's the property that lets a procurement reviewer say 'memory across vendors, with controls.'",
    (6, "c"): "If everything is green, you can stop here. You've seen what this thing is and why it exists. Come back when you have a project to start on.",
    (6, "b"): "Your next step: pick a project to extend, run `bootstrap-project.sh --name <name>`, and write your first skill. The `skill-author` skill is the meta-skill that helps you author skills correctly.",
    (6, "o"): "Bake `verify-agent-forge.py` and `validate-triad-runtime.py --project <name>` into your team's CI before letting anyone merge canonical changes.",
    (6, "d"): "The validation pyramid (structural verifier + triad runtime + optional invocation probe) is what you'd cite in a procurement review as the cross-vendor honest-broker proof.",
}


def role_tail(section_num: int, role: str) -> None:
    """Print the role-tuned closing paragraph for a section, if any."""
    if not role or role == "s":
        return
    text = ROLE_TAILS.get((section_num, role), "")
    if not text:
        return
    print(dim(text))
    print()


def section_1_what_is_this(level: str, role: str = "") -> None:
    section_header(1, 6, "What is this folder?")
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
    role_tail(1, role)


def section_2_one_source(level: str, role: str = "") -> None:
    section_header(2, 6, "Three tools, one source of truth")
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
    print(adapt(
        level,
        ("One more thing about those four directory names. The factory writes to four "
         "different host-config folders: `.claude/` (Claude), `.codex/` (Codex's modern "
         "surface), `.agents/` (Codex's legacy skills convention, still in use), and "
         "`.gemini/` (Gemini). One canonical source, four output shapes. If you ever see "
         "drift between them, that's a bug — the triad runtime validator catches it before "
         "it ships. Run `python3 skills/global/onboarding-guide/onboard.py explain host-dirs` "
         "to see this written down."),
        ("Four output dirs: `.claude/`, `.codex/`, `.agents/` (Codex legacy), `.gemini/`. "
         "Drift between them = bug; triad validator gates it."),
    ))
    print()
    role_tail(2, role)


def section_3_translation(level: str, role: str = "") -> None:
    section_header(3, 6, "Three vendors, three names for the same thing")
    print(adapt(
        level,
        ("Each of the three host CLIs ships its own terminology for the same primitives. "
         "A 'skill' in Codex is a 'command' or a 'subagent' in Claude depending on its "
         "class. A 'hook' fires on `PreToolUse` on Claude and Codex but on `BeforeTool` on "
         "Gemini. The factory keeps one canonical name and translates outward, so you "
         "rarely need to memorize the table — but seeing it once builds the mental map."),
        ("Canonical concept → host-native name table. The factory does the translation; "
         "this is for orientation."),
    ))
    print()
    rows = [
        ("Concept",               "Claude",           "Codex",            "Gemini"),
        ("Skill (workflow)",      "command",          "skill",            "command"),
        ("Skill (expert)",        "subagent",         "(none native)",    "subagent"),
        ("Slash command syntax",  "/name",            "(no slash)",       "/name"),
        ("Hook event pre-tool",   "PreToolUse",       "PreToolUse",       "BeforeTool"),
        ("Hook event stop",       "Stop",             "Stop",             "SessionEnd"),
        ("MCP config file",       ".mcp.json",        ".codex/cfg.toml",  ".gemini/settings.json"),
        ("Memory native target",  "~/.claude/.../",   "(none)",           "(none)"),
        ("Memory sidecar",        "(n/a, native)",    ".codex/memory/",   ".gemini/memory/"),
        ("Boot file",             "CLAUDE.md",        "AGENTS.md",        "GEMINI.md"),
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    for i, row in enumerate(rows):
        line = "  ".join(row[c].ljust(widths[c]) for c in range(4))
        if i == 0:
            print(bold(line))
            print(dim("  ".join("-" * widths[c] for c in range(4))))
        else:
            print(line)
    print()
    print(dim(
        "Three vendors shipped similar primitives with their own names. The factory keeps\n"
        "one source of truth, then renders out to each host's idiom. The table is for\n"
        "orientation, not memorization — the factory does the translation."
    ))
    print()
    role_tail(3, role)


def section_4_seatbelt(level: str, role: str = "") -> None:
    section_header(4, 6, "The seatbelt")
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
    role_tail(4, role)


def section_5_shared_brain(level: str, role: str = "") -> None:
    section_header(5, 6, "The shared brain")
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
    role_tail(5, role)


def section_6_what_now(level: str, probes: list[tuple[str, str, str, str]], role: str = "") -> None:
    section_header(6, 6, "What to do next")
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
    print()
    role_tail(6, role)


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
    section_6_what_now("s", probes, role="s")
    print()
    print(dim(f"For the full guided tour: python3 {Path(__file__).resolve()} tour"))


def cmd_tour(args: argparse.Namespace) -> int:
    probes = run_probes()
    if getattr(args, "quick", False):
        cmd_quick_summary(probes)
        return 0
    print(bold("Agent Forge Onboarding Guide"))
    print(dim("Six short sections. Plain English. Read-only — nothing you do here will modify your repo."))
    print()
    print(dim(f"Factory root: {FACTORY_ROOT}"))
    level = ask_experience()
    role = ask_role()

    sections_completed = 0
    try:
        section_1_what_is_this(level, role);   sections_completed += 1
        section_2_one_source(level, role);     sections_completed += 1
        section_3_translation(level, role);    sections_completed += 1
        section_4_seatbelt(level, role);       sections_completed += 1
        section_5_shared_brain(level, role);   sections_completed += 1
        section_6_what_now(level, probes, role); sections_completed += 1
    finally:
        write_audit_log(level, sections_completed, role)

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

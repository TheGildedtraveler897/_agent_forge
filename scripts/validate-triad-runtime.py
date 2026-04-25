#!/usr/bin/env python3
"""Triad runtime validator.

Live-probes Claude, Codex, and Gemini host surfaces against a governed project.
Confirms that every skill the omni-factory promised to deliver for a given host
is actually reachable at runtime. Pairs CLI evidence with filesystem evidence so
sandbox-blocked hosts can still be validated via the documented escalation rule.

Artifacts are written to runtime/validation/triad/<timestamp>/.

Exit code:
  0 — all three hosts pass (via CLI enumeration or filesystem evidence).
  1 — at least one host failed both CLI and filesystem checks.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "registry.json"
PROJECTS_CATALOG_PATH = ROOT / "projects.json"
MATRIX_PATH = ROOT / "runtime" / "validation-matrix.json"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def load_projects() -> list[dict]:
    return json.loads(PROJECTS_CATALOG_PATH.read_text()).get("governed_projects", [])


def resolve_project_root(project_name: str) -> Path:
    for entry in load_projects():
        if entry["name"] == project_name:
            return PROJECTS_ROOT / entry["root"]
    raise RuntimeError(f"Unknown project: {project_name}")


def expected_skills_for(host: str) -> list[str]:
    reg = load_registry()
    return sorted(
        s["name"] for s in reg["skills"]
        if host in s.get("targets", [])
    )


def run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 180,
    env_extra: dict | None = None,
) -> tuple[int, str, str]:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", (exc.stderr or "") + f"\n[timeout after {timeout}s]"


def host_sandbox_blocked(text: str) -> bool:
    markers = (
        "bwrap: loopback: Failed RTM_NEWADDR",
        "Operation not permitted",
    )
    return any(m in text for m in markers)


def filesystem_skills_for(host: str, project_root: Path) -> set[str]:
    if host == "claude":
        d = project_root / ".claude" / "skills"
    elif host == "codex":
        d = project_root / ".agents" / "skills"
    elif host == "gemini":
        d = project_root / ".gemini" / "skills"
    else:
        return set()
    if not d.is_dir():
        return set()
    return {p.name for p in d.iterdir() if (p / "SKILL.md").exists() or p.is_symlink()}


def probe_gemini(project_root: Path, evidence_dir: Path, expected: list[str]) -> dict:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["gemini", "skills", "list", "--all"]
    code, out, err = run_cmd(cmd, cwd=project_root, timeout=60)
    (evidence_dir / "gemini-stdout.txt").write_text(out)
    (evidence_dir / "gemini-stderr.txt").write_text(err)

    observed: set[str] = set()
    if code == 0 and out:
        for line in out.splitlines():
            m = re.match(r"^(\S[\w\-]+)\s+\[(Enabled|Disabled)\]", line)
            if m:
                observed.add(m.group(1))
    method = "cli" if observed else "filesystem"
    if not observed:
        observed = filesystem_skills_for("gemini", project_root)

    missing = sorted(set(expected) - observed)
    return {
        "host": "gemini",
        "method": method,
        "pass": not missing,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "missing": missing,
        "cli_exit": code,
        "cli_cmd": " ".join(shlex.quote(c) for c in cmd),
    }


def probe_claude(project_root: Path, evidence_dir: Path, expected: list[str]) -> dict:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Task: list every Skill currently available to you in this repo. "
        "Do NOT invoke any skill. Return ONLY a fenced block of names, one per "
        "line, between the markers ===SKILLS=== and ===END===. No other text."
    )
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "text",
        "--dangerously-skip-permissions",
    ]
    code, out, err = run_cmd(cmd, cwd=project_root, timeout=180)
    (evidence_dir / "claude-stdout.txt").write_text(out)
    (evidence_dir / "claude-stderr.txt").write_text(err)

    observed: set[str] = set()
    m = re.search(r"===SKILLS===\s*(.*?)\s*===END===", out, flags=re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            name = line.strip().lstrip("-* ").strip("`").split()[0] if line.strip() else ""
            if re.fullmatch(r"[a-z][a-z0-9\-]+", name):
                observed.add(name)
    method = "cli" if observed else "filesystem"
    if not observed:
        observed = filesystem_skills_for("claude", project_root)

    missing = sorted(set(expected) - observed)
    return {
        "host": "claude",
        "method": method,
        "pass": not missing,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "missing": missing,
        "cli_exit": code,
        "cli_cmd": " ".join(shlex.quote(c) for c in cmd),
    }


def probe_codex(project_root: Path, evidence_dir: Path, expected: list[str]) -> dict:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Use your shell tool to run: ls ~/.agents/skills && ls .agents/skills. "
        "Then output ONLY the names, one per line, between ===SKILLS=== and ===END===."
    )
    cmd = ["codex", "exec", prompt]
    code, out, err = run_cmd(cmd, cwd=project_root, timeout=180)
    (evidence_dir / "codex-stdout.txt").write_text(out)
    (evidence_dir / "codex-stderr.txt").write_text(err)

    sandbox = host_sandbox_blocked(out) or host_sandbox_blocked(err)
    observed: set[str] = set()
    m = re.search(r"===SKILLS===\s*(.*?)\s*===END===", out, flags=re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            name = line.strip().lstrip("-* ").strip("`").split()[0] if line.strip() else ""
            if re.fullmatch(r"[a-z][a-z0-9\-]+", name):
                observed.add(name)
    method = "cli" if observed else ("filesystem-escalated" if sandbox else "filesystem")
    if not observed:
        observed = filesystem_skills_for("codex", project_root)

    missing = sorted(set(expected) - observed)
    return {
        "host": "codex",
        "method": method,
        "pass": not missing,
        "expected_count": len(expected),
        "observed_count": len(observed),
        "missing": missing,
        "cli_exit": code,
        "cli_cmd": " ".join(shlex.quote(c) for c in cmd),
        "sandbox_blocked": sandbox,
    }


def _expected_guardian_id() -> str:
    return "pre-tool-execution-guardian"


def hook_surface_for(host: str, project_root: Path) -> dict:
    expected_id = _expected_guardian_id()
    try:
        if host == "claude":
            path = project_root / ".claude" / "settings.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "settings.json missing"}
            data = json.loads(path.read_text())
            hooks_root = data.get("hooks") or {}
            body = json.dumps(hooks_root)
        elif host == "codex":
            path = project_root / ".codex" / "hooks.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "hooks.json missing"}
            data = json.loads(path.read_text())
            body = json.dumps(data)
        elif host == "gemini":
            path = project_root / ".gemini" / "settings.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "settings.json missing"}
            data = json.loads(path.read_text())
            body = json.dumps(data.get("hooks") or {})
        else:
            return {"pass": False, "reason": f"unknown host {host}"}
    except Exception as exc:
        return {"pass": False, "reason": f"parse error: {exc}"}

    guardian_present = "telemetry-guardian" in body or "guardian.sh" in body
    return {
        "pass": guardian_present,
        "path": str(path),
        "guardian_present": guardian_present,
        "expected_hook_id": expected_id,
    }


def update_matrix(project_name: str, summary: dict) -> None:
    matrix = json.loads(MATRIX_PATH.read_text()) if MATRIX_PATH.exists() else {}
    triad = matrix.setdefault("triad_runtime", {})
    triad[project_name] = {
        "last_run": summary["timestamp"],
        "overall_pass": summary["pass"],
        "per_host": {h: {"pass": r["pass"], "method": r["method"], "hook_pass": r.get("hook_surface", {}).get("pass", False)} for h, r in summary["results"].items()},
        "artifact_path": summary["artifact_path"],
    }
    MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, help="governed project name from projects.json")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--skip-host", action="append", default=[], choices=["claude", "codex", "gemini"])
    args = ap.parse_args()

    project_root = resolve_project_root(args.project)
    if not project_root.exists():
        print(f"[FAIL] Project root not found: {project_root}", file=sys.stderr)
        return 1

    stamp = utc_stamp()
    out_root = Path(args.output_root) if args.output_root else (ROOT / "runtime" / "validation" / "triad" / stamp)
    out_root.mkdir(parents=True, exist_ok=True)

    results: dict = {}
    for host, probe_fn in (("gemini", probe_gemini), ("claude", probe_claude), ("codex", probe_codex)):
        if host in args.skip_host:
            continue
        if shutil.which(host) is None:
            results[host] = {"host": host, "pass": False, "method": "skipped", "missing": ["CLI not installed"], "expected_count": 0, "observed_count": 0}
            continue
        expected = expected_skills_for(host)
        evidence_dir = out_root / host
        print(f"[..] probing {host} ({len(expected)} expected)", flush=True)
        res = probe_fn(project_root, evidence_dir, expected)
        hook_res = hook_surface_for(host, project_root)
        res["hook_surface"] = hook_res
        if not hook_res["pass"]:
            res["pass"] = False
            res.setdefault("missing", []).append(f"hook-surface:{hook_res.get('reason','guardian not present')}")
        (evidence_dir / "result.json").write_text(json.dumps(res, indent=2) + "\n")
        status = "PASS" if res["pass"] else "FAIL"
        hook_tag = "hook+" if hook_res["pass"] else "hook-"
        print(f"[{status}] {host:7s} method={res['method']:22s} missing={len(res['missing'])}/{res['expected_count']}  {hook_tag}")
        results[host] = res

    overall = all(r["pass"] for r in results.values()) if results else False
    summary = {
        "project": args.project,
        "timestamp": stamp,
        "artifact_path": str(out_root.relative_to(ROOT)),
        "pass": overall,
        "results": results,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    update_matrix(args.project, summary)

    print()
    print(f"Summary: overall={'PASS' if overall else 'FAIL'}  project={args.project}")
    print(f"Artifacts: {out_root}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())

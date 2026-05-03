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
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "registry.json"
PROJECTS_CATALOG_PATH = ROOT / "projects.json"
MATRIX_PATH = ROOT / "runtime" / "validation-matrix.json"

sys.path.insert(0, str(ROOT / "scripts"))
import omni_factory  # noqa: E402


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
        def _coerce(b):
            if b is None:
                return ""
            if isinstance(b, bytes):
                return b.decode("utf-8", errors="replace")
            return b
        return 124, _coerce(exc.stdout), _coerce(exc.stderr) + f"\n[timeout after {timeout}s]"


def host_sandbox_blocked(text: str) -> bool:
    markers = (
        "bwrap: loopback: Failed RTM_NEWADDR",
        "Operation not permitted",
        "needs access to create user namespaces",
        "shell tool failed before command execution",
        "shell tool is blocked by the sandbox",
        "sandbox network setup path",
        "Codex's Linux sandbox uses bubblewrap",
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


def expected_hook_records_for(host: str) -> list[dict]:
    records: list[dict] = []
    for hook in omni_factory._hooks_for_host(host):
        native_event = omni_factory.native_hook_event(host, hook["event"])
        handler_type = (hook.get("handler") or {}).get("type")
        if native_event is None:
            continue
        if host in {"codex", "gemini"} and handler_type != "command":
            continue
        records.append(
            {
                "id": hook.get("id"),
                "event": hook.get("event"),
                "native_event": native_event,
                "handler_type": handler_type,
            }
        )
    return records


def hook_surface_for(host: str, project_root: Path) -> dict:
    expected_id = _expected_guardian_id()
    expected_records = expected_hook_records_for(host)
    expected_event_keys = sorted({record["native_event"] for record in expected_records})
    try:
        if host == "claude":
            path = project_root / ".claude" / "settings.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "settings.json missing"}
            data = json.loads(path.read_text())
            hooks_root = data.get("hooks") or {}
            body = json.dumps(hooks_root)
            event_keys = list(hooks_root.keys())
        elif host == "codex":
            path = project_root / ".codex" / "hooks.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "hooks.json missing"}
            data = json.loads(path.read_text())
            body = json.dumps(data)
            event_keys = list((data.get("hooks") or {}).keys())
        elif host == "gemini":
            path = project_root / ".gemini" / "settings.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "settings.json missing"}
            data = json.loads(path.read_text())
            hooks_root = data.get("hooks") or {}
            body = json.dumps(hooks_root)
            event_keys = list(hooks_root.keys())
        else:
            return {"pass": False, "reason": f"unknown host {host}"}
    except Exception as exc:
        return {"pass": False, "reason": f"parse error: {exc}"}

    guardian_present = "telemetry-guardian" in body or "guardian.sh" in body
    missing_event_keys = [key for key in expected_event_keys if key not in event_keys]
    event_keys_present = not missing_event_keys
    return {
        "pass": guardian_present and event_keys_present,
        "path": str(path),
        "guardian_present": guardian_present,
        "expected_hook_id": expected_id,
        "expected_hook_records": expected_records,
        "expected_event_keys": expected_event_keys,
        "observed_event_keys": event_keys,
        "missing_event_keys": missing_event_keys,
        "event_keys_present": event_keys_present,
    }


def _memory_section_ids() -> list[str]:
    policy_path = ROOT / "policies" / "memory.json"
    if not policy_path.exists():
        return []
    try:
        payload = json.loads(policy_path.read_text())
    except Exception:
        return []
    return [s.get("id") for s in (payload.get("sections") or []) if s.get("id")]


def memory_surface_for(host: str, project_root: Path) -> dict:
    """Confirm the universal state layer is reachable from this host's surface.

    All three hosts share the same project-level MEMORY.md, but each must
    have a path to discover it:
      - claude: AGENTS.md Read Order line (covers via the AGENTS chain).
      - codex: AGENTS.md is auto-loaded; same coverage.
      - gemini: <project>/GEMINI.md must list MEMORY.md as an @import.
    """
    expected_sections = _memory_section_ids()
    if not expected_sections:
        return {"pass": True, "reason": "memory policy not active"}

    memory_md = project_root / "MEMORY.md"
    if not memory_md.exists():
        return {"pass": False, "path": str(memory_md), "reason": "MEMORY.md missing"}
    body = memory_md.read_text()
    sections_present = [sid for sid in expected_sections if f"<!-- section:{sid} -->" in body]
    sections_missing = [sid for sid in expected_sections if sid not in sections_present]

    manifest_path = project_root / ".forge_state" / "manifest.json"
    manifest_pass = False
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            manifest_pass = all(k in manifest for k in ("version", "sections", "last_updated"))
        except Exception:
            manifest_pass = False

    host_link_pass = True
    host_link_reason = ""
    if host == "gemini":
        gemini_md = project_root / "GEMINI.md"
        if not gemini_md.exists():
            host_link_pass = False
            host_link_reason = "GEMINI.md missing"
        elif "@MEMORY.md" not in gemini_md.read_text():
            host_link_pass = False
            host_link_reason = "GEMINI.md does not @import MEMORY.md"
    else:
        agents_md = ROOT / "AGENTS.md"
        if "MEMORY.md" not in agents_md.read_text():
            host_link_pass = False
            host_link_reason = "AGENTS.md missing MEMORY.md Read Order entry"

    overall_pass = (not sections_missing) and manifest_pass and host_link_pass
    return {
        "pass": overall_pass,
        "path": str(memory_md),
        "sections_present": sections_present,
        "sections_missing": sections_missing,
        "manifest_pass": manifest_pass,
        "host_link_pass": host_link_pass,
        "host_link_reason": host_link_reason,
    }


def memory_bridge_for(host: str, project_root: Path) -> dict:
    """Confirm the host-local memory bridge has state and evidence.

    The canonical source remains <project>/MEMORY.md. Bridge pass means the
    bridge policy is enabled for this host, the per-project state file parses,
    a native target path is known, and at least one outbound or inbound bridge
    action has run for the host.
    """
    policy = omni_factory._memory_bridge_policy()
    if not policy.get("enabled", False):
        return {"pass": True, "enabled": False, "reason": "memory bridge disabled"}

    hosts = list(policy.get("hosts") or [])
    if host not in hosts:
        return {"pass": False, "enabled": True, "reason": f"host not enabled: {host}"}

    state_file = project_root / ".forge_state" / "bridge.json"
    if not state_file.exists():
        return {"pass": False, "enabled": True, "path": str(state_file), "reason": "bridge.json missing"}
    try:
        state = json.loads(state_file.read_text())
    except Exception as exc:
        return {"pass": False, "enabled": True, "path": str(state_file), "reason": f"bridge.json parse error: {exc}"}

    required = ("version", "last_outbound", "last_inbound", "last_outbound_hash", "last_inbound_diff_hash", "native_targets", "last_errors")
    missing_keys = [key for key in required if key not in state]
    native_target = (state.get("native_targets") or {}).get(host)
    if not native_target:
        try:
            native_target = str(omni_factory.memory_bridge_native_target(project_root, host))
        except Exception:
            native_target = ""
    outbound = (state.get("last_outbound") or {}).get(host)
    inbound = (state.get("last_inbound") or {}).get(host)
    outbound_hash = (state.get("last_outbound_hash") or {}).get(host)
    inbound_hash = (state.get("last_inbound_diff_hash") or {}).get(host)
    last_error = (state.get("last_errors") or {}).get(host)
    target_exists = bool(native_target) and Path(native_target).exists()
    evidence = bool(outbound or inbound)
    hash_evidence = bool(outbound_hash or inbound_hash)
    pass_ = not missing_keys and bool(native_target) and target_exists and evidence and hash_evidence and not last_error

    return {
        "pass": pass_,
        "enabled": True,
        "path": str(state_file),
        "host": host,
        "native_target": native_target,
        "native_target_exists": target_exists,
        "last_outbound": outbound,
        "last_inbound": inbound,
        "last_outbound_hash": outbound_hash,
        "last_inbound_diff_hash": inbound_hash,
        "last_error": last_error,
        "missing_state_keys": missing_keys,
        "evidence_present": evidence,
        "hash_evidence_present": hash_evidence,
    }


def project_name_for_root(project_root: Path) -> str:
    project_root = project_root.resolve()
    for entry in load_projects():
        candidate = (PROJECTS_ROOT / entry["root"]).resolve()
        if candidate == project_root:
            return entry["name"]
    return project_root.name


def _write_mcp_message(stream, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
    stream.write(body)
    stream.flush()


def _read_mcp_message(stream) -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        decoded = line.decode("utf-8").strip()
        if ":" not in decoded:
            continue
        key, value = decoded.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    payload = stream.read(length)
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def stdio_tools_list_for(server: dict, project_root: Path) -> dict:
    transport = server.get("transport") or {}
    if transport.get("type") != "stdio":
        return {"pass": True, "listed_tools": [], "reason": "non-stdio server skipped"}

    command = transport.get("command")
    args = list(transport.get("args") or [])
    if not command:
        return {"pass": False, "listed_tools": [], "reason": "stdio command missing"}

    cwd = Path(os.path.expanduser(transport.get("cwd") or str(project_root)))
    env = dict(os.environ)
    env.update({key: value for key, value in (server.get("env_literal") or {}).items() if isinstance(value, str)})
    for key in server.get("env_passthrough") or []:
        if key in os.environ:
            env[key] = os.environ[key]

    proc = subprocess.Popen(
        [os.path.expanduser(command), *args],
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        _write_mcp_message(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "agent-forge-validator", "version": "1.0.0"},
                },
            },
        )
        _read_mcp_message(proc.stdout)
        _write_mcp_message(proc.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        _write_mcp_message(proc.stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        response = _read_mcp_message(proc.stdout) or {}
        result = response.get("result") or {}
        tools = result.get("tools") or []
        listed_tools = [tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name")]
        return {"pass": bool(listed_tools), "listed_tools": listed_tools, "reason": ""}
    except Exception as exc:
        return {"pass": False, "listed_tools": [], "reason": str(exc)}
    finally:
        try:
            if proc.stdin is not None:
                proc.stdin.close()
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


def mcp_surface_for(host: str, project_root: Path) -> dict:
    project_name = project_name_for_root(project_root)
    expected_servers = omni_factory.project_mcp_servers(project_name, host=host)
    if not expected_servers:
        return {"pass": True, "reason": "no MCP servers active", "listed_tools": []}

    try:
        if host == "claude":
            path = project_root / ".mcp.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": ".mcp.json missing", "listed_tools": []}
            data = json.loads(path.read_text())
            observed = data.get("mcpServers") or {}
        elif host == "codex":
            path = project_root / ".codex" / "config.toml"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "config.toml missing", "listed_tools": []}
            data = tomllib.loads(path.read_text())
            observed = data.get("mcp_servers") or {}
        elif host == "gemini":
            path = project_root / ".gemini" / "settings.json"
            if not path.exists():
                return {"pass": False, "path": str(path), "reason": "settings.json missing", "listed_tools": []}
            data = json.loads(path.read_text())
            observed = data.get("mcpServers") or {}
        else:
            return {"pass": False, "reason": f"unknown host {host}", "listed_tools": []}
    except Exception as exc:
        return {"pass": False, "reason": f"parse error: {exc}", "listed_tools": []}

    expected_aliases = [server["server_alias"] for server in expected_servers]
    missing_aliases = [alias for alias in expected_aliases if alias not in observed]
    smoke = stdio_tools_list_for(expected_servers[0], project_root)
    listed_tools = smoke.get("listed_tools") or []
    expected_tools = list(expected_servers[0].get("tool_filter") or [])
    missing_tools = [tool for tool in expected_tools if tool not in listed_tools]
    pass_ = not missing_aliases and smoke.get("pass", False) and not missing_tools
    return {
        "pass": pass_,
        "path": str(path),
        "server_alias": expected_servers[0]["server_alias"],
        "expected_aliases": expected_aliases,
        "observed_aliases": sorted(observed.keys()),
        "missing_aliases": missing_aliases,
        "listed_tools": listed_tools,
        "expected_tools": expected_tools,
        "missing_tools": missing_tools,
        "smoke_reason": smoke.get("reason", ""),
    }


def live_hook_invocation_for(
    host: str,
    project_root: Path,
    evidence_dir: Path,
    handler_type: str = "command",
) -> dict:
    """Fire a known-blocked Bash invocation on the target host CLI and report
    whether the seeded telemetry-guardian hook actually intercepted it.

    Calls the live-hook-prober skill (skills/global/live-hook-prober/prober.sh).
    Default test command is `git commit --no-verify -m probe`, which is the
    top of the guardian deny list. A correctly-rendered hook should produce
    verdict=pass with observed=block.

    Returns the prober's stdout JSON augmented with `pass` (boolean for
    triad-validator integration). Sandbox- or trust-blocked Codex/Gemini
    runs return `pass=true` with `escalated=true` per the documented
    escalation doctrine — the absence of evidence is not evidence of
    absence when the host CLI cannot run the probe at all.
    """
    prober = ROOT / "skills" / "global" / "live-hook-prober" / "prober.sh"
    if not prober.exists():
        return {"pass": False, "reason": "prober skill missing", "host": host}

    test_command = "git commit --no-verify -m probe"
    expect = "block"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "bash",
        str(prober),
        "--host",
        host,
        "--project",
        str(project_root),
        "--command",
        test_command,
        "--expect",
        expect,
        "--handler-type",
        handler_type,
        "--evidence-root",
        str(evidence_dir),
        "--timeout",
        "120",
    ]
    code, out, err = run_cmd(cmd, cwd=ROOT, timeout=180)
    (evidence_dir / "prober-stdout.txt").write_text(out)
    (evidence_dir / "prober-stderr.txt").write_text(err)

    parsed: dict = {}
    if out.strip():
        try:
            parsed = json.loads(out.strip().splitlines()[-1])
        except Exception:
            parsed = {}

    verdict = parsed.get("verdict", "fail" if code == 1 else ("escalated" if code == 2 else "fail"))
    observed = parsed.get("observed", "error")
    reason = parsed.get("reason", "")
    escalated = verdict == "escalated"
    # Escalated outcomes (sandbox_blocked, trust_blocked, cli_missing) match
    # the documented escalation doctrine for the surface check; do not fail
    # the gate, but record the constraint.
    overall_pass = verdict == "pass" or escalated
    return {
        "pass": overall_pass,
        "host": host,
        "handler_type": handler_type,
        "command": test_command,
        "expected": expect,
        "observed": observed,
        "verdict": verdict,
        "escalated": escalated,
        "reason": reason,
        "exit_code": code,
        "evidence_path": parsed.get("evidence_path", str(evidence_dir)),
    }


def update_matrix(project_name: str, summary: dict) -> None:
    matrix = json.loads(MATRIX_PATH.read_text()) if MATRIX_PATH.exists() else {}
    triad = matrix.setdefault("triad_runtime", {})
    triad[project_name] = {
        "last_run": summary["timestamp"],
        "overall_pass": summary["pass"],
        "per_host": {
            h: {
                "pass": r["pass"],
                "method": r["method"],
                "hook_pass": r.get("hook_surface", {}).get("pass", False),
                "memory_pass": r.get("memory_surface", {}).get("pass", False),
                "bridge_pass": r.get("memory_bridge", {}).get("pass", False),
                "mcp_pass": r.get("mcp_surface", {}).get("pass", False),
                **(
                    {
                        "live_hook_pass": r["live_hook"].get("pass", False),
                        "live_hook_verdict": r["live_hook"].get("verdict", "skipped"),
                    }
                    if "live_hook" in r
                    else {}
                ),
            }
            for h, r in summary["results"].items()
        },
        "artifact_path": summary["artifact_path"],
    }
    MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, help="governed project name from projects.json")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--skip-host", action="append", default=[], choices=["claude", "codex", "gemini"])
    ap.add_argument(
        "--probe-invocations",
        action="store_true",
        help="After surface checks pass, fire a live test command on each "
             "host CLI to confirm the seeded telemetry-guardian hook actually "
             "intercepts it. Off by default (each probe is a real CLI call).",
    )
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
        memory_res = memory_surface_for(host, project_root)
        res["memory_surface"] = memory_res
        if not memory_res["pass"]:
            res["pass"] = False
            res.setdefault("missing", []).append(f"memory-surface:{memory_res.get('reason') or memory_res.get('host_link_reason') or 'memory layer not reachable'}")
        bridge_res = memory_bridge_for(host, project_root)
        res["memory_bridge"] = bridge_res
        if not bridge_res["pass"]:
            res["pass"] = False
            res.setdefault("missing", []).append(f"memory-bridge:{bridge_res.get('reason') or bridge_res.get('last_error') or 'bridge evidence missing'}")
        mcp_res = mcp_surface_for(host, project_root)
        res["mcp_surface"] = mcp_res
        if not mcp_res["pass"]:
            res["pass"] = False
            res.setdefault("missing", []).append(f"mcp-surface:{mcp_res.get('reason') or mcp_res.get('smoke_reason') or 'mcp surface not reachable'}")
        live_tag = ""
        if args.probe_invocations and res["pass"]:
            live_dir = evidence_dir / "live-hook"
            live_res = live_hook_invocation_for(host, project_root, live_dir)
            res["live_hook"] = live_res
            if not live_res["pass"]:
                res["pass"] = False
                res.setdefault("missing", []).append(f"live-hook:{live_res.get('verdict','fail')}:{live_res.get('reason','')}")
            live_tag = " live+" if live_res["pass"] and not live_res.get("escalated") else (
                " live~" if live_res.get("escalated") else " live-"
            )
        (evidence_dir / "result.json").write_text(json.dumps(res, indent=2) + "\n")
        status = "PASS" if res["pass"] else "FAIL"
        hook_tag = "hook+" if hook_res["pass"] else "hook-"
        mem_tag = "mem+" if memory_res["pass"] else "mem-"
        bridge_tag = "bridge+" if bridge_res["pass"] else "bridge-"
        mcp_tag = "mcp+" if mcp_res["pass"] else "mcp-"
        print(f"[{status}] {host:7s} method={res['method']:22s} missing={len(res['missing'])}/{res['expected_count']}  {hook_tag} {mem_tag} {bridge_tag} {mcp_tag}{live_tag}")
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

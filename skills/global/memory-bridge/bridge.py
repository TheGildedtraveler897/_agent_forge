#!/usr/bin/env python3
"""Bridge canonical MEMORY.md with host-local memory surfaces.

The canonical source of truth remains <project>/MEMORY.md. Host native targets
are local synchronization surfaces, never doctrine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX hosts are the supported path.
    fcntl = None


ROOT = Path(__file__).resolve().parent.parent.parent.parent
POLICY_PATH = ROOT / "policies" / "memory.json"
ARCHIVIST = ROOT / "skills" / "global" / "memory-archivist" / "archivist.py"
HOSTS = ("claude", "codex", "gemini")
START = "<!-- agent-forge-memory-bridge:start -->"
END = "<!-- agent-forge-memory-bridge:end -->"

SECRETS_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"gho_[A-Za-z0-9]{30,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?i)password\s*[:=]\s*\S+"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"(?i)secret\s*[:=]\s*\S+"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(message: str, code: int = 2) -> None:
    print(f"memory-bridge: {message}", file=sys.stderr)
    sys.exit(code)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text())


def memory_path(project_root: Path) -> Path:
    return project_root / "MEMORY.md"


def state_path(project_root: Path) -> Path:
    return project_root / ".forge_state" / "bridge.json"


def log_path(project_root: Path) -> Path:
    return project_root / ".forge_state" / "bridge.log"


def lock_path(project_root: Path) -> Path:
    return project_root / ".forge_state" / "bridge.lock"


def default_state() -> dict:
    return {
        "version": 1,
        "last_outbound": {},
        "last_inbound": {},
        "last_outbound_hash": {},
        "last_inbound_diff_hash": {},
        "imported_entry_hashes": {},
        "native_targets": {},
        "last_errors": {},
    }


def load_state(project_root: Path) -> dict:
    path = state_path(project_root)
    if not path.exists():
        return default_state()
    try:
        state = json.loads(path.read_text())
    except Exception:
        return default_state()
    merged = default_state()
    merged.update(state)
    for key, value in default_state().items():
        if isinstance(value, dict) and not isinstance(merged.get(key), dict):
            merged[key] = {}
    return merged


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def save_state(project_root: Path, state: dict) -> None:
    atomic_write(state_path(project_root), json.dumps(state, indent=2, sort_keys=True) + "\n")


def log_event(project_root: Path, payload: dict) -> None:
    payload = {"ts": utc_now(), **payload}
    log_path(project_root).parent.mkdir(parents=True, exist_ok=True)
    with log_path(project_root).open("a") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


@contextmanager
def bridge_lock(project_root: Path):
    lock = lock_path(project_root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def secrets_check(text: str) -> str | None:
    for pat in SECRETS_PATTERNS:
        if pat.search(text):
            return pat.pattern
    return None


def claude_project_slug(project_root: Path) -> str:
    return str(project_root.resolve()).replace("/", "-")


def native_target(project_root: Path, host: str) -> Path:
    if host == "claude":
        return Path.home() / ".claude" / "projects" / claude_project_slug(project_root) / "memory" / "MEMORY.md"
    if host == "codex":
        return project_root / ".codex" / "memory" / "AGENTS_MEMORY.md"
    if host == "gemini":
        return project_root / ".gemini" / "memory" / "MEMORY.md"
    die(f"unknown host: {host}")
    raise AssertionError(host)


def remove_managed_block(text: str) -> str:
    start = text.find(START)
    end = text.find(END)
    if start >= 0 and end >= start:
        return text[:start] + text[end + len(END):]
    return text


def managed_block(host: str, project_root: Path, canonical: str, digest: str) -> str:
    return "\n".join(
        [
            "",
            "## Agent Forge Memory Bridge",
            "",
            "Managed by Agent Forge. Do not edit inside this block.",
            f"Host: {host}",
            f"Source: {memory_path(project_root)}",
            f"Last outbound: {utc_now()}",
            f"Content hash: {digest}",
            "",
            START,
            canonical.rstrip(),
            END,
            "",
        ]
    )


def upsert_managed_block(existing: str, block: str) -> str:
    start = existing.find(START)
    end = existing.find(END)
    if start >= 0 and end >= start:
        header_start = existing.rfind("## Agent Forge Memory Bridge", 0, start)
        replace_start = header_start if header_start >= 0 else start
        replace_end = end + len(END)
        prefix = existing[:replace_start].rstrip()
        suffix = existing[replace_end:].lstrip()
        joined = (prefix + "\n" if prefix else "") + block.strip() + "\n"
        return joined + suffix
    if existing.strip():
        return existing.rstrip() + "\n" + block
    return block.lstrip()


def managed_block_matches_hash(existing: str, digest: str) -> bool:
    return START in existing and END in existing and f"Content hash: {digest}" in existing


def canonical_memory(project_root: Path) -> str:
    path = memory_path(project_root)
    if not path.exists():
        die(f"missing canonical MEMORY.md at {path}")
    return path.read_text()


def classify_entry(entry: str) -> str:
    lower = entry.lower()
    if any(word in lower for word in ("fail", "failure", "error", "broken", "blocker", "workaround")):
        return "known_failures"
    if any(word in lower for word in ("decision", "decided", "choose", "chose", "selected")):
        return "recent_decisions"
    if any(word in lower for word in ("command", "run ", "test", "build", "lint", "python", "npm", "make ")):
        return "build_commands"
    if any(word in lower for word in ("active", "todo", "current task", "in flight", "in-flight")):
        return "active_tasks"
    return "project_quirks"


def candidate_entries(native_text: str) -> list[str]:
    cleaned = remove_managed_block(native_text)
    entries: list[str] = []
    for raw in cleaned.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("#", "<!--", "```")):
            continue
        if line.lower().startswith(("managed by ", "source:", "last outbound:", "content hash:", "host:")):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if len(line) < 12:
            continue
        entries.append(line)
    return entries


def append_with_archivist(project_root: Path, section: str, entry: str, host: str) -> tuple[bool, str]:
    cmd = [
        sys.executable,
        str(ARCHIVIST),
        "append",
        "--project",
        str(project_root),
        "--section",
        section,
        "--entry",
        entry,
        "--source",
        host,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()
    return True, proc.stdout.strip()


def cmd_outbound(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    host = args.host
    policy = load_policy()
    bridge = policy.get("bridge") or {}
    if not bridge.get("enabled", False):
        print(json.dumps({"pass": True, "enabled": False, "host": host}))
        return 0
    if host not in bridge.get("hosts", []):
        die(f"host not enabled for memory bridge: {host}")

    with bridge_lock(project_root):
        state = load_state(project_root)
        target = native_target(project_root, host)
        canonical = canonical_memory(project_root)
        secret = secrets_check(canonical)
        if secret:
            state["last_errors"][host] = f"outbound rejected by secrets policy: {secret}"
            state["native_targets"][host] = str(target)
            save_state(project_root, state)
            log_event(project_root, {"action": "outbound", "host": host, "pass": False, "reason": state["last_errors"][host]})
            die(state["last_errors"][host])

        digest = sha256_text(canonical)
        existing = target.read_text() if target.exists() else ""
        if managed_block_matches_hash(existing, digest):
            changed = False
        else:
            next_body = upsert_managed_block(existing, managed_block(host, project_root, canonical, digest))
            changed = next_body != existing
            if changed:
                atomic_write(target, next_body)

        state["last_outbound"][host] = utc_now()
        state["last_outbound_hash"][host] = digest
        state["native_targets"][host] = str(target)
        state["last_errors"].pop(host, None)
        save_state(project_root, state)
        log_event(project_root, {"action": "outbound", "host": host, "pass": True, "changed": changed, "target": str(target), "hash": digest})

    print(json.dumps({"pass": True, "action": "outbound", "host": host, "changed": changed, "target": str(target), "hash": digest}))
    return 0


def cmd_inbound(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    host = args.host
    policy = load_policy()
    bridge = policy.get("bridge") or {}
    if not bridge.get("enabled", False):
        print(json.dumps({"pass": True, "enabled": False, "host": host}))
        return 0
    if host not in bridge.get("hosts", []):
        die(f"host not enabled for memory bridge: {host}")

    with bridge_lock(project_root):
        state = load_state(project_root)
        target = native_target(project_root, host)
        state["native_targets"][host] = str(target)
        if not target.exists():
            state["last_errors"][host] = f"native target missing: {target}"
            save_state(project_root, state)
            log_event(project_root, {"action": "inbound", "host": host, "pass": True, "changed": False, "reason": state["last_errors"][host]})
            print(json.dumps({"pass": True, "action": "inbound", "host": host, "changed": False, "reason": state["last_errors"][host]}))
            return 0

        native_text = target.read_text()
        clean_text = remove_managed_block(native_text).strip()
        diff_hash = sha256_text(clean_text)
        imported = set(state.get("imported_entry_hashes", {}).get(host, []))
        added: list[dict] = []
        rejected: list[dict] = []

        for entry in candidate_entries(native_text):
            entry_hash = sha256_text(entry)
            if entry_hash in imported:
                continue
            secret = secrets_check(entry)
            if secret:
                imported.add(entry_hash)
                rejected.append({"entry_hash": entry_hash, "reason": f"secrets pattern: {secret}"})
                log_event(project_root, {"action": "inbound_reject", "host": host, "entry_hash": entry_hash, "reason": secret})
                continue
            section = classify_entry(entry)
            ok, detail = append_with_archivist(project_root, section, entry, host)
            if ok:
                imported.add(entry_hash)
                added.append({"section": section, "entry_hash": entry_hash})
            else:
                rejected.append({"entry_hash": entry_hash, "reason": detail})
                log_event(project_root, {"action": "inbound_error", "host": host, "entry_hash": entry_hash, "reason": detail})

        state["last_inbound"][host] = utc_now()
        state["last_inbound_diff_hash"][host] = diff_hash
        state.setdefault("imported_entry_hashes", {})[host] = sorted(imported)
        state["last_errors"].pop(host, None)
        save_state(project_root, state)
        log_event(project_root, {"action": "inbound", "host": host, "pass": True, "added": len(added), "rejected": len(rejected), "target": str(target), "hash": diff_hash})

    print(json.dumps({"pass": True, "action": "inbound", "host": host, "added": added, "rejected": rejected, "target": str(target), "hash": diff_hash}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    state = load_state(project_root)
    targets = {host: str(native_target(project_root, host)) for host in HOSTS}
    exists = {host: Path(path).exists() for host, path in targets.items()}
    print(json.dumps({"project": str(project_root), "state": state, "targets": targets, "target_exists": exists}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="memory-bridge", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name, func in (("outbound", cmd_outbound), ("inbound", cmd_inbound)):
        p = sub.add_parser(name)
        p.add_argument("--project", required=True, help="Path to governed project root")
        p.add_argument("--host", required=True, choices=HOSTS)
        p.set_defaults(func=func)

    p_status = sub.add_parser("status")
    p_status.add_argument("--project", required=True, help="Path to governed project root")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

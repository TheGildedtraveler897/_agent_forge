#!/usr/bin/env python3
"""Memory archivist: append normalized session-state entries to a project's MEMORY.md.

Companion to the universal state layer defined in policies/memory.json.
Append-first by default; secrets-deny on write; per-section retention warnings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
MEMORY_POLICY_PATH = ROOT / "policies" / "memory.json"

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


def load_policy() -> dict:
    if not MEMORY_POLICY_PATH.exists():
        die(f"policies/memory.json not found at {MEMORY_POLICY_PATH}")
    return json.loads(MEMORY_POLICY_PATH.read_text())


def die(msg: str, code: int = 2) -> None:
    print(f"archivist: {msg}", file=sys.stderr)
    sys.exit(code)


def secrets_check(entry: str, policy: dict) -> None:
    if policy.get("secrets_policy", "deny") != "deny":
        return
    for pat in SECRETS_PATTERNS:
        if pat.search(entry):
            die(f"entry rejected: matches secrets pattern {pat.pattern!r}")


def section_index(policy: dict, section_id: str) -> dict:
    for s in policy.get("sections", []):
        if s["id"] == section_id:
            return s
    die(f"unknown section '{section_id}'. Valid: {[s['id'] for s in policy.get('sections', [])]}")


def memory_path(project_root: Path) -> Path:
    return project_root / "MEMORY.md"


def manifest_path(project_root: Path) -> Path:
    return project_root / ".forge_state" / "manifest.json"


def audit_log_path(project_root: Path) -> Path:
    return project_root / ".forge_state" / "archivist.log"


def read_memory(project_root: Path) -> str:
    p = memory_path(project_root)
    if not p.exists():
        die(f"MEMORY.md missing at {p}. Run sync to generate it.")
    return p.read_text()


def section_block_bounds(body: str, section_id: str) -> tuple[int, int]:
    """Return (start, end) char offsets of the entries:start ... entries:end block for the section."""
    anchor = f"<!-- section:{section_id} -->"
    a_idx = body.find(anchor)
    if a_idx < 0:
        die(f"section anchor missing: {anchor}")
    start_marker = "<!-- entries:start -->"
    end_marker = "<!-- entries:end -->"
    start_idx = body.find(start_marker, a_idx)
    end_idx = body.find(end_marker, a_idx)
    if start_idx < 0 or end_idx < 0:
        die(f"entries markers missing for section '{section_id}'")
    return (start_idx + len(start_marker), end_idx)


def count_entries(body: str, section_id: str) -> int:
    s, e = section_block_bounds(body, section_id)
    block = body[s:e].strip()
    if not block:
        return 0
    return sum(1 for line in block.splitlines() if line.strip().startswith("- "))


def append_entry(project_root: Path, section_id: str, entry: str, source: str | None) -> None:
    policy = load_policy()
    section_index(policy, section_id)
    secrets_check(entry, policy)

    body = read_memory(project_root)
    s, e = section_block_bounds(body, section_id)

    timestamp = utc_now()
    src_tag = f" [{source}]" if source else ""
    line = f"- {timestamp}{src_tag} — {entry.strip()}"

    block = body[s:e].rstrip("\n")
    if block.strip():
        new_block = f"{block}\n{line}\n"
    else:
        new_block = f"\n{line}\n"
    new_body = body[:s] + new_block + body[e:]
    memory_path(project_root).write_text(new_body)

    refresh_manifest(project_root, policy)
    audit_line = json.dumps({"ts": timestamp, "action": "append", "section": section_id, "source": source, "entry_len": len(entry)})
    with audit_log_path(project_root).open("a") as f:
        f.write(audit_line + "\n")

    warn_at = (policy.get("retention") or {}).get("warn_at", 40)
    count = count_entries(new_body, section_id)
    print(json.dumps({"appended": True, "section": section_id, "timestamp": timestamp, "section_count": count, "warn_at": warn_at}))
    if count >= warn_at:
        print(f"archivist: warning — section '{section_id}' has {count} entries (warn_at={warn_at})", file=sys.stderr)


def replace_active_tasks(project_root: Path, entry: str, source: str | None) -> None:
    policy = load_policy()
    sec = section_index(policy, "active_tasks")
    if sec.get("append_only", True):
        die("active_tasks is marked append_only=true; replace not allowed")
    secrets_check(entry, policy)

    body = read_memory(project_root)
    s, e = section_block_bounds(body, "active_tasks")
    timestamp = utc_now()
    src_tag = f" [{source}]" if source else ""
    new_block = f"\n- {timestamp}{src_tag} — {entry.strip()}\n"
    new_body = body[:s] + new_block + body[e:]
    memory_path(project_root).write_text(new_body)
    refresh_manifest(project_root, policy)
    audit = json.dumps({"ts": timestamp, "action": "replace", "section": "active_tasks", "source": source})
    with audit_log_path(project_root).open("a") as f:
        f.write(audit + "\n")
    print(json.dumps({"replaced": True, "section": "active_tasks", "timestamp": timestamp}))


def refresh_manifest(project_root: Path, policy: dict) -> None:
    p = manifest_path(project_root)
    if not p.exists():
        return
    try:
        data = json.loads(p.read_text())
    except Exception:
        return
    data["last_updated"] = utc_now()
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def cmd_append(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    if args.replace:
        if args.section != "active_tasks":
            die("--replace is only valid for --section active_tasks")
        replace_active_tasks(project_root, args.entry, args.source)
    else:
        append_entry(project_root, args.section, args.entry, args.source)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    policy = load_policy()
    body = read_memory(project_root)
    section_ids = [s["id"] for s in policy.get("sections", [])]

    missing_anchors = [sid for sid in section_ids if f"<!-- section:{sid} -->" not in body]
    if missing_anchors:
        die(f"missing anchors: {missing_anchors}", code=1)

    mp = manifest_path(project_root)
    if not mp.exists():
        die(f"manifest missing: {mp}", code=1)
    try:
        manifest = json.loads(mp.read_text())
    except Exception as exc:
        die(f"manifest does not parse: {exc}", code=1)
    for key in ("version", "sections", "last_updated"):
        if key not in manifest:
            die(f"manifest missing key: {key}", code=1)

    warn_at = (policy.get("retention") or {}).get("warn_at", 40)
    warnings = []
    for sid in section_ids:
        c = count_entries(body, sid)
        if c >= warn_at:
            warnings.append({"section": sid, "count": c, "warn_at": warn_at})

    print(json.dumps({"pass": True, "sections": section_ids, "warnings": warnings, "manifest_last_updated": manifest.get("last_updated")}, indent=2))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    project_root = Path(args.project).expanduser().resolve()
    policy = load_policy()
    body = read_memory(project_root)
    section_ids = [s["id"] for s in policy.get("sections", [])]
    counts = {sid: count_entries(body, sid) for sid in section_ids}
    mp = manifest_path(project_root)
    last_updated = None
    if mp.exists():
        try:
            last_updated = json.loads(mp.read_text()).get("last_updated")
        except Exception:
            pass
    warn_at = (policy.get("retention") or {}).get("warn_at", 40)
    warnings = [{"section": sid, "count": c, "warn_at": warn_at} for sid, c in counts.items() if c >= warn_at]
    print(json.dumps({"project": str(project_root), "sections": counts, "manifest_last_updated": last_updated, "warnings": warnings}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="archivist", description="Universal memory layer archivist")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="Append (or replace, for active_tasks) an entry")
    p_append.add_argument("--project", required=True, help="Path to the project root")
    p_append.add_argument("--section", required=True, help="Section id from policies/memory.json")
    p_append.add_argument("--entry", required=True, help="Entry text")
    p_append.add_argument("--source", choices=["claude", "codex", "gemini"], help="Originating host")
    p_append.add_argument("--replace", action="store_true", help="Replace body (only valid for active_tasks)")
    p_append.set_defaults(func=cmd_append)

    p_validate = sub.add_parser("validate", help="Validate MEMORY.md and manifest")
    p_validate.add_argument("--project", required=True)
    p_validate.set_defaults(func=cmd_validate)

    p_summary = sub.add_parser("summary", help="Emit structured per-section summary")
    p_summary.add_argument("--project", required=True)
    p_summary.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

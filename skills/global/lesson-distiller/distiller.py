#!/usr/bin/env python3
"""Lesson distiller: compact LESSONS_LEARNED.md by archiving promoted entries.

Companion to the bounded-decay policy defined in policies/distillation.json.
Reversible by design: every archival can be undone via the `restore` subcommand.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX hosts are the supported path.
    fcntl = None

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DISTILLATION_POLICY_PATH = ROOT / "policies" / "distillation.json"

ENTRY_HEADING_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2})\s+-\s+(.+?)\s*$", re.MULTILINE)
STATUS_LINE_RE = re.compile(r"^- `Status:`\s*(.+?)\s*$", re.MULTILINE)
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2) -> None:
    print(f"distiller: {msg}", file=sys.stderr)
    sys.exit(code)


def load_policy() -> dict:
    if not DISTILLATION_POLICY_PATH.exists():
        die(f"policies/distillation.json not found at {DISTILLATION_POLICY_PATH}")
    return json.loads(DISTILLATION_POLICY_PATH.read_text())


def target_by_id(policy: dict, target_id: str) -> dict:
    for t in policy.get("targets", []):
        if t.get("id") == target_id:
            return t
    die(f"unknown target id '{target_id}'. Valid: {[t.get('id') for t in policy.get('targets', [])]}")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def audit_log_path() -> Path:
    return ROOT / ".forge_state" / "distiller.log"


def lock_path() -> Path:
    return ROOT / ".forge_state" / "distiller.lock"


@contextmanager
def distiller_lock():
    lock = lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def write_audit(payload: dict) -> None:
    payload = {"ts": utc_now(), **payload}
    audit_log_path().parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path().open("a") as f:
        f.write(json.dumps(payload) + "\n")


# --- Entry parsing -----------------------------------------------------------


def parse_entries(body: str) -> list[dict]:
    """Split the body into entry blocks. Returns list of dicts:
    {date, title, heading, body, status_line, status_value, start, end}.
    Each entry's body excludes the heading line itself.
    """
    matches = list(ENTRY_HEADING_RE.finditer(body))
    entries = []
    for i, m in enumerate(matches):
        date = m.group(1)
        title = m.group(2).strip()
        heading_start = m.start()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)

        entry_text = body[heading_start:body_end]
        status_match = STATUS_LINE_RE.search(entry_text)
        status_value = status_match.group(1).strip() if status_match else ""
        entries.append({
            "date": date,
            "title": title,
            "heading": m.group(0),
            "body": entry_text,
            "status_line": status_match.group(0) if status_match else "",
            "status_value": status_value,
            "start": heading_start,
            "end": body_end,
        })
    return entries


def header_and_entries_split(body: str) -> tuple[str, str]:
    """Split LESSONS_LEARNED.md into (header_block, entries_block).
    The header includes everything up to and including the line that begins '## Entries'.
    Falls back to first '### ' if '## Entries' is not present.
    """
    marker = "## Entries"
    idx = body.find(marker)
    if idx >= 0:
        nl = body.find("\n", idx)
        if nl < 0:
            return body, ""
        return body[: nl + 1], body[nl + 1 :]
    # fallback
    m = ENTRY_HEADING_RE.search(body)
    if not m:
        return body, ""
    return body[: m.start()], body[m.start() :]


# --- Promotion-claim verification --------------------------------------------


def is_promoted(status_value: str) -> bool:
    return status_value.strip().lower().startswith("promoted")


def extract_doctrine_paths(status_value: str) -> list[str]:
    """Pull every backtick-quoted token out of the parenthetical and keep those
    that look like file paths (contain '/' or end in .md/.json/.py/.sh/.toml)."""
    # Take only the substring after the first '(' if present.
    paren = status_value
    open_idx = status_value.find("(")
    if open_idx >= 0:
        paren = status_value[open_idx:]
    candidates = BACKTICK_PATH_RE.findall(paren)
    paths = []
    for c in candidates:
        c = c.strip()
        if not c:
            continue
        if "/" in c or c.endswith((".md", ".json", ".py", ".sh", ".toml")) or c.endswith(".md`"):
            paths.append(c)
        elif c in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "CONOPS.md", "MEMORY.md"):
            paths.append(c)
    return paths


def verify_promotion_claim(entry: dict) -> dict:
    """Return {ok, paths_checked, paths_resolved, reason}."""
    status = entry["status_value"]
    if not is_promoted(status):
        return {"ok": False, "reason": "not_promoted", "paths_checked": [], "paths_resolved": []}
    paths = extract_doctrine_paths(status)
    if not paths:
        return {"ok": False, "reason": "no_paths_in_parenthetical", "paths_checked": [], "paths_resolved": []}
    resolved = []
    search_roots = [
        ROOT,
        ROOT / "docs",
        ROOT / "scripts",
        ROOT / "policies",
        ROOT / "skills" / "global",
        ROOT / "teams",
    ]
    for p in paths:
        if any((root / p).exists() for root in search_roots):
            resolved.append(p)
    if not resolved:
        return {"ok": False, "reason": "no_paths_resolve", "paths_checked": paths, "paths_resolved": []}
    return {"ok": True, "reason": "ok", "paths_checked": paths, "paths_resolved": resolved}


# --- Index-line builder ------------------------------------------------------


def build_index_line(entry: dict, doctrine_hint: str) -> str:
    return f"- {entry['date']} — {entry['title']} → {doctrine_hint} (archived)"


def short_doctrine_hint(verification: dict) -> str:
    if verification["paths_resolved"]:
        return verification["paths_resolved"][0]
    return "doctrine reference not resolved"


# --- Lessons distillation core ----------------------------------------------


def update_header_counters(header: str, promoted: int, active: int, superseded: int, archived: int) -> str:
    """Adjust the `Last updated:` line tail to reflect new counts. Best-effort; if the
    line shape doesn't match the expected pattern, leave the header untouched."""
    new_tail = f"{promoted} entries promoted, {active} active, {superseded} superseded, {archived} archived"
    pattern = re.compile(r"(Last updated:.*?)(\d+\s+(?:entries?\s+)?promoted.*?superseded[^\)]*\))(.*)", re.DOTALL)
    match = pattern.search(header)
    if not match:
        return header
    return header.replace(match.group(2), new_tail + ")", 1)


def archive_lesson_entry(archive_body: str, entry: dict) -> str:
    """Append entry verbatim to archive body if not already present."""
    if entry["heading"] in archive_body:
        return archive_body  # already archived; idempotent
    sep = "\n" if archive_body.endswith("\n") else "\n\n"
    if not archive_body:
        archive_body = "# Archived Promoted Lessons\n\nVerbatim copies of entries from `docs/LESSONS_LEARNED.md` whose lessons have been promoted into doctrine. Restored from the main ledger by `lesson-distiller`. Each entry remains the original byte-for-byte source of truth.\n\n"
        sep = ""
    return archive_body + sep + entry["body"].rstrip() + "\n"


def distill_lessons(policy: dict, dry_run: bool) -> dict:
    target = target_by_id(policy, "lessons_ledger")
    main_path = ROOT / target["path"]
    archive_path = ROOT / target["archive_path"]

    if not main_path.exists():
        die(f"lessons ledger missing: {main_path}")

    body = main_path.read_text()
    pre_size = len(body)
    header, entries_block = header_and_entries_split(body)
    entries = parse_entries(entries_block)

    archive_body = archive_path.read_text() if archive_path.exists() else ""

    actions = {"would_archive": [], "verification_failures": [], "kept": []}
    new_entries_text_parts: list[str] = []
    last_end = 0

    archived_count = 0

    # Compose new entries_block by rewriting matching ranges with index lines.
    cursor = 0
    pieces: list[str] = []
    for entry in entries:
        # Append the gap from cursor → entry.start (preserves blank lines between entries).
        pieces.append(entries_block[cursor : entry["start"]])
        cursor = entry["end"]

        if not is_promoted(entry["status_value"]):
            pieces.append(entry["body"])
            actions["kept"].append({"date": entry["date"], "title": entry["title"], "status": entry["status_value"][:60]})
            continue

        verification = verify_promotion_claim(entry)
        if not verification["ok"]:
            pieces.append(entry["body"])
            actions["verification_failures"].append({
                "date": entry["date"],
                "title": entry["title"],
                "reason": verification["reason"],
                "paths_checked": verification["paths_checked"],
            })
            continue

        # Promoted + verified → archive and replace with index line.
        index_line = build_index_line(entry, short_doctrine_hint(verification))
        pieces.append(index_line + "\n\n")
        archive_body = archive_lesson_entry(archive_body, entry)
        archived_count += 1
        actions["would_archive"].append({
            "date": entry["date"],
            "title": entry["title"],
            "doctrine_hint": short_doctrine_hint(verification),
            "paths_resolved": verification["paths_resolved"],
        })

    pieces.append(entries_block[cursor:])
    new_entries_block = "".join(pieces)

    # Recount statuses for the header.
    remaining = parse_entries(new_entries_block)
    promoted_remaining = sum(1 for e in remaining if is_promoted(e["status_value"]) and "→" not in e["heading"])
    active_remaining = sum(1 for e in remaining if e["status_value"].lower().startswith("active"))
    superseded_remaining = sum(1 for e in remaining if e["status_value"].lower().startswith("superseded"))
    new_header = update_header_counters(header, promoted_remaining, active_remaining, superseded_remaining, archived_count)

    new_main_body = new_header + new_entries_block
    post_size = len(new_main_body)

    result = {
        "target": "lessons_ledger",
        "main_path": str(main_path.relative_to(ROOT)),
        "archive_path": str(archive_path.relative_to(ROOT)),
        "pre_size_bytes": pre_size,
        "post_size_bytes": post_size,
        "delta_bytes": pre_size - post_size,
        "archived_count": archived_count,
        "actions": actions,
        "dry_run": dry_run,
    }

    if not dry_run and archived_count > 0:
        atomic_write(main_path, new_main_body)
        atomic_write(archive_path, archive_body)

    write_audit({"action": "distill_lessons", **result})
    return result


# --- Triad-runs pruning ------------------------------------------------------


def prune_triad_runs(policy: dict, dry_run: bool) -> dict:
    target = target_by_id(policy, "triad_runs")
    triad_dir = ROOT / target["path"]
    keep = int(target.get("keep", 5))

    if not triad_dir.exists():
        return {"target": "triad_runs", "skipped": True, "reason": "directory_missing", "dry_run": dry_run}

    runs = sorted([p for p in triad_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    if len(runs) <= keep:
        return {"target": "triad_runs", "skipped": True, "reason": "below_threshold", "kept": len(runs), "dry_run": dry_run}

    to_delete = runs[:-keep]
    to_keep = runs[-keep:]
    deleted_bytes = 0
    for d in to_delete:
        for root, _, files in os.walk(d):
            for f in files:
                try:
                    deleted_bytes += (Path(root) / f).stat().st_size
                except OSError:
                    pass

    if not dry_run:
        for d in to_delete:
            shutil.rmtree(d)

    result = {
        "target": "triad_runs",
        "to_delete": [d.name for d in to_delete],
        "to_keep": [d.name for d in to_keep],
        "delta_bytes": deleted_bytes,
        "dry_run": dry_run,
    }
    write_audit({"action": "prune_triad_runs", **result})
    return result


# --- Verify ------------------------------------------------------------------


def verify_state() -> dict:
    policy = load_policy()
    issues: list[str] = []

    target = target_by_id(policy, "lessons_ledger")
    main_path = ROOT / target["path"]
    archive_path = ROOT / target["archive_path"]

    if not main_path.exists():
        issues.append(f"missing main ledger: {main_path}")
    body = main_path.read_text() if main_path.exists() else ""

    archive_body = archive_path.read_text() if archive_path.exists() else ""

    # Every one-line index pointer (entry replaced with `- DATE — TITLE → DOCTRINE (archived)`)
    # must correspond to an entry in the archive file.
    index_re = re.compile(r"^- (\d{4}-\d{2}-\d{2}) — (.+?) → .+? \(archived\)$", re.MULTILINE)
    pointers = index_re.findall(body)
    missing_in_archive: list[str] = []
    for date, title in pointers:
        expected_heading = f"### {date} - {title}"
        if expected_heading not in archive_body and expected_heading.replace(" - ", " — ") not in archive_body:
            missing_in_archive.append(f"{date} - {title}")

    return {
        "ok": not issues and not missing_in_archive,
        "issues": issues,
        "index_pointers": len(pointers),
        "archive_entries_missing": missing_in_archive,
        "main_size_bytes": len(body),
        "archive_size_bytes": len(archive_body),
        "warn_at_bytes": (policy.get("session_load_thresholds") or {}).get("warn_at_bytes"),
        "fail_at_bytes": (policy.get("session_load_thresholds") or {}).get("fail_at_bytes"),
    }


# --- Restore -----------------------------------------------------------------


def restore_entry(date: str, title: str) -> dict:
    policy = load_policy()
    target = target_by_id(policy, "lessons_ledger")
    main_path = ROOT / target["path"]
    archive_path = ROOT / target["archive_path"]

    if not archive_path.exists():
        die(f"archive file missing: {archive_path}")

    archive_body = archive_path.read_text()
    archive_entries = parse_entries(archive_body)
    match = next((e for e in archive_entries if e["date"] == date and e["title"] == title), None)
    if not match:
        die(f"entry not found in archive: {date} - {title}", code=1)

    main_body = main_path.read_text()
    header, entries_block = header_and_entries_split(main_body)

    # Find and remove the corresponding one-line index pointer in the main body.
    pointer_re = re.compile(rf"^- {re.escape(date)} — {re.escape(title)} → .+? \(archived\)\n*", re.MULTILINE)
    if pointer_re.search(entries_block):
        entries_block = pointer_re.sub("", entries_block, count=1)

    # Insert the restored entry at the top of the entries block.
    restored_text = match["body"].rstrip() + "\n\n"
    new_entries_block = restored_text + entries_block.lstrip("\n")

    # Remove from archive.
    new_archive_body = archive_body[: match["start"]] + archive_body[match["end"] :]
    new_archive_body = re.sub(r"\n{3,}", "\n\n", new_archive_body)

    atomic_write(main_path, header + new_entries_block)
    atomic_write(archive_path, new_archive_body)

    result = {"restored": True, "date": date, "title": title}
    write_audit({"action": "restore", **result})
    return result


# --- CLI ---------------------------------------------------------------------


def cmd_dry_run(args: argparse.Namespace) -> int:
    policy = load_policy()
    out: dict = {}
    if args.target in ("lessons", "all"):
        out["lessons"] = distill_lessons(policy, dry_run=True)
    if args.target in ("triad", "all"):
        out["triad"] = prune_triad_runs(policy, dry_run=True)
    print(json.dumps(out, indent=2))
    return 0


def cmd_distill(args: argparse.Namespace) -> int:
    policy = load_policy()
    if not args.yes:
        # Show dry-run output and refuse to apply.
        out: dict = {}
        if args.target in ("lessons", "all"):
            out["lessons"] = distill_lessons(policy, dry_run=True)
        if args.target in ("triad", "all"):
            out["triad"] = prune_triad_runs(policy, dry_run=True)
        out["status"] = "dry-run; pass --yes to apply"
        print(json.dumps(out, indent=2))
        return 1

    with distiller_lock():
        out: dict = {}
        if args.target in ("lessons", "all"):
            out["lessons"] = distill_lessons(policy, dry_run=False)
        if args.target in ("triad", "all"):
            out["triad"] = prune_triad_runs(policy, dry_run=False)
    print(json.dumps(out, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify_state()
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def cmd_restore(args: argparse.Namespace) -> int:
    with distiller_lock():
        result = restore_entry(args.date, args.title)
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="distiller", description="Lesson ledger distiller (bounded decay companion to sprint-harvester)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dry = sub.add_parser("dry-run", help="Preview distillation without writing")
    p_dry.add_argument("--target", choices=["lessons", "triad", "all"], default="lessons")
    p_dry.set_defaults(func=cmd_dry_run)

    p_distill = sub.add_parser("distill", help="Apply distillation (requires --yes)")
    p_distill.add_argument("--target", choices=["lessons", "triad", "all"], default="lessons")
    p_distill.add_argument("--yes", action="store_true", help="Confirm destructive rewrite")
    p_distill.set_defaults(func=cmd_distill)

    p_verify = sub.add_parser("verify", help="Validate index pointers and archive consistency")
    p_verify.set_defaults(func=cmd_verify)

    p_restore = sub.add_parser("restore", help="Restore an archived entry to the main ledger")
    p_restore.add_argument("--date", required=True, help="Entry date YYYY-MM-DD")
    p_restore.add_argument("--title", required=True, help="Entry title (exact match)")
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

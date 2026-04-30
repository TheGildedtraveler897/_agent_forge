#!/usr/bin/env python3
"""Handoff archiver: compact HANDOFF.md by moving older sprint sections to archive.

Companion to the bounded-decay policy defined in policies/distillation.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DISTILLATION_POLICY_PATH = ROOT / "policies" / "distillation.json"

DATE_IN_HEADING_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SPRINT_HEADING_RE = re.compile(r"^### .+$", re.MULTILINE)
TOP_LEVEL_SECTION_RE = re.compile(r"^## .+$", re.MULTILINE)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2) -> None:
    print(f"archiver: {msg}", file=sys.stderr)
    sys.exit(code)


def load_policy() -> dict:
    if not DISTILLATION_POLICY_PATH.exists():
        die(f"policies/distillation.json not found at {DISTILLATION_POLICY_PATH}")
    return json.loads(DISTILLATION_POLICY_PATH.read_text())


def target_by_id(policy: dict, target_id: str) -> dict:
    for t in policy.get("targets", []):
        if t.get("id") == target_id:
            return t
    die(f"unknown target id '{target_id}'")


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
def archiver_lock():
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


# --- HANDOFF.md parsing ------------------------------------------------------


def find_what_changed_block(body: str) -> tuple[int, int]:
    """Return (start, end) offsets bracketing the contents of '## What Changed'.
    The block ends at the first '## ' heading that is not '## What Changed' itself.
    Handles duplicate '## What Changed' headings (older HANDOFF.md state) by
    consuming all consecutive 'What Changed' regions.
    """
    marker = "## What Changed"
    start = body.find(marker)
    if start < 0:
        die("'## What Changed' marker not found in HANDOFF.md")
    # Move start to the beginning of the line after the heading.
    nl = body.find("\n", start)
    if nl < 0:
        die("malformed HANDOFF.md: '## What Changed' has no newline")
    content_start = nl + 1

    # Find next top-level heading that is not 'What Changed'.
    cursor = content_start
    end = len(body)
    while True:
        m = TOP_LEVEL_SECTION_RE.search(body, cursor)
        if not m:
            break
        if body[m.start() : m.end()].strip() == "## What Changed":
            cursor = m.end()
            continue
        end = m.start()
        break
    return content_start, end


def parse_sprint_sections(block: str) -> list[dict]:
    """Each section runs from a '### ' heading to the next '### ' heading or end of block."""
    matches = list(SPRINT_HEADING_RE.finditer(block))
    sections = []
    for i, m in enumerate(matches):
        heading_line = block[m.start() : m.end()].strip()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        section_text = block[m.start() : section_end]
        date_match = DATE_IN_HEADING_RE.search(heading_line)
        date_str = date_match.group(1) if date_match else None
        # Strip the leading '### ' for the title.
        title = heading_line[4:].strip()
        sections.append({
            "heading": heading_line,
            "title": title,
            "date": date_str,
            "body": section_text,
            "start": m.start(),
            "end": section_end,
        })
    return sections


def build_summary_table(sections_to_move: list[dict], archive_rel: str) -> str:
    if not sections_to_move:
        return ""
    lines = [
        "_Older sprints have been distilled into the archive to keep this file's session-load footprint small. Wisdom is preserved verbatim._",
        "",
        "| Date | Sprint | Archive |",
        "|---|---|---|",
    ]
    for s in sections_to_move:
        date = s["date"] or "—"
        title = s["title"].replace("|", "\\|")
        lines.append(f"| {date} | {title} | [{archive_rel}]({archive_rel}) |")
    return "\n".join(lines) + "\n\n"


def append_to_archive(archive_body: str, sections_to_move: list[dict]) -> str:
    if not sections_to_move:
        return archive_body
    if not archive_body:
        archive_body = "# Archived Sprint Sections\n\nVerbatim copies of `## What Changed` sections from `docs/HANDOFF.md` that pre-date the current retention window. Distilled by `handoff-archiver`. The current/active sprint stays in `HANDOFF.md`; this file is the on-demand reference for prior sprints.\n\n"
    # Sort by date descending so newest archived sprint is at top of archive.
    ordered = sorted(sections_to_move, key=lambda s: s["date"] or "", reverse=True)
    for s in ordered:
        if s["heading"] in archive_body:
            continue  # idempotent
        archive_body = archive_body.rstrip() + "\n\n" + s["body"].rstrip() + "\n"
    return archive_body


def update_handoff_header_date(body: str) -> str:
    """Touch the 'Last updated:' line if present, leaving the descriptor alone."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pattern = re.compile(r"^(Last updated:\s*)\d{4}-\d{2}-\d{2}", re.MULTILINE)
    if pattern.search(body):
        return pattern.sub(rf"\g<1>{today}", body, count=1)
    return body


# --- Core archive operation --------------------------------------------------


def archive_handoff(policy: dict, keep: int, dry_run: bool) -> dict:
    target = target_by_id(policy, "handoff_log")
    main_path = ROOT / target["path"]
    archive_path = ROOT / target["archive_path"]

    if not main_path.exists():
        die(f"HANDOFF.md missing: {main_path}")

    body = main_path.read_text()
    pre_size = len(body)
    block_start, block_end = find_what_changed_block(body)
    block = body[block_start:block_end]
    sections = parse_sprint_sections(block)

    # Sort sections by date descending; sections with no date go to the end (older).
    def _sort_key(s):
        return (s["date"] or "0000-00-00", s["start"])

    sorted_desc = sorted(sections, key=_sort_key, reverse=True)
    keep_set = {id(s) for s in sorted_desc[:keep]}
    to_keep = [s for s in sections if id(s) in keep_set]
    to_move = [s for s in sections if id(s) not in keep_set]

    if not to_move:
        result = {
            "target": "handoff_log",
            "skipped": True,
            "reason": "below_keep_threshold",
            "kept_sections": len(to_keep),
            "dry_run": dry_run,
        }
        write_audit({"action": "archive_handoff", **result})
        return result

    archive_rel = str(archive_path.relative_to(ROOT))
    summary_table = build_summary_table(to_move, archive_rel)

    # Reconstruct: keep all kept sections in their original order, prepend the summary table.
    kept_block = "".join(s["body"] for s in to_keep)
    new_block = summary_table + kept_block
    new_main_body = body[:block_start] + new_block + body[block_end:]
    new_main_body = update_handoff_header_date(new_main_body)
    post_size = len(new_main_body)

    archive_body = archive_path.read_text() if archive_path.exists() else ""
    new_archive_body = append_to_archive(archive_body, to_move)

    if not dry_run:
        atomic_write(main_path, new_main_body)
        atomic_write(archive_path, new_archive_body)

    result = {
        "target": "handoff_log",
        "main_path": str(main_path.relative_to(ROOT)),
        "archive_path": archive_rel,
        "pre_size_bytes": pre_size,
        "post_size_bytes": post_size,
        "delta_bytes": pre_size - post_size,
        "kept_sections": [{"date": s["date"], "title": s["title"]} for s in to_keep],
        "archived_sections": [{"date": s["date"], "title": s["title"]} for s in to_move],
        "summary_table_preview": summary_table.strip(),
        "dry_run": dry_run,
    }
    write_audit({"action": "archive_handoff", **result})
    return result


# --- CLI ---------------------------------------------------------------------


def cmd_dry_run(args: argparse.Namespace) -> int:
    policy = load_policy()
    target = target_by_id(policy, "handoff_log")
    keep = args.keep if args.keep is not None else int(target.get("keep", 1))
    out = archive_handoff(policy, keep=keep, dry_run=True)
    print(json.dumps(out, indent=2))
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    policy = load_policy()
    target = target_by_id(policy, "handoff_log")
    keep = args.keep if args.keep is not None else int(target.get("keep", 1))
    if not args.yes:
        out = archive_handoff(policy, keep=keep, dry_run=True)
        out["status"] = "dry-run; pass --yes to apply"
        print(json.dumps(out, indent=2))
        return 1
    with archiver_lock():
        out = archive_handoff(policy, keep=keep, dry_run=False)
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="archiver", description="HANDOFF.md sprint-section archiver (bounded decay)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dry = sub.add_parser("dry-run", help="Preview archival without writing")
    p_dry.add_argument("--keep", type=int, default=None, help="Override policy keep value (default from policies/distillation.json)")
    p_dry.set_defaults(func=cmd_dry_run)

    p_arch = sub.add_parser("archive", help="Apply archival (requires --yes)")
    p_arch.add_argument("--keep", type=int, default=None)
    p_arch.add_argument("--yes", action="store_true", help="Confirm destructive rewrite")
    p_arch.set_defaults(func=cmd_archive)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

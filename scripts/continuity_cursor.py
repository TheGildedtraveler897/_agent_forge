#!/usr/bin/env python3
"""Maintain tiny per-task continuity cursors under dev/active/.

The cursor is intentionally small: it records the current task, last proof,
and pointers to durable artifacts. It is not a transcript store.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURSOR_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cursor_dir(root: Path, slug: str) -> Path:
    return root / "dev" / "active" / slug


def cursor_path(root: Path, slug: str) -> Path:
    return cursor_dir(root, slug) / "cursor.json"


def require_slug(slug: str) -> None:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if not slug or any(ch not in allowed for ch in slug):
        raise ValueError("slug may only contain letters, numbers, dots, underscores, and hyphens")


def repo_relative(root: Path, value: str | None, *, must_exist: bool = False, allow_none: bool = False) -> str | None:
    if value in {None, "", "none", "None", "-"}:
        if allow_none:
            return None
        raise ValueError("path value is required")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if must_exist and not path.exists():
        raise FileNotFoundError(str(path))
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path must be inside project root: {path}") from exc


def dirty_files(root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    files: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        files.append(line[3:])
    return files


def write_cursor(root: Path, slug: str, state: dict[str, Any]) -> None:
    path = cursor_path(root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def load_cursor(root: Path, slug: str) -> dict[str, Any]:
    path = cursor_path(root, slug)
    if not path.exists():
        raise FileNotFoundError(f"missing continuity cursor: {path}")
    return json.loads(path.read_text())


def cmd_start(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    now = utc_now()
    plan = repo_relative(root, args.plan, must_exist=True)
    state = {
        "version": CURSOR_VERSION,
        "slug": args.slug,
        "plan": plan,
        "current_task": args.task,
        "last_completed_task": None,
        "task_status": {args.task: "in_progress"},
        "last_note": None,
        "next_action": args.next_action,
        "blocker": None,
        "dirty_files": dirty_files(root),
        "last_verification": None,
        "created_at": now,
        "updated_at": now,
    }
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "task": args.task}))
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    state["current_task"] = args.task
    state.setdefault("task_status", {})[args.task] = args.status
    if args.status == "done":
        state["last_completed_task"] = args.task
    state["last_note"] = args.note
    state["next_action"] = args.next_action
    state["blocker"] = args.note if args.status == "blocked" else None
    state["dirty_files"] = dirty_files(root)
    state["updated_at"] = utc_now()
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "task": args.task, "status": args.status}))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    artifact = repo_relative(root, args.artifact, must_exist=False, allow_none=True)
    state["last_verification"] = {
        "cmd": args.cmd,
        "exit_code": args.exit_code,
        "artifact": artifact,
        "recorded_at": utc_now(),
    }
    state["dirty_files"] = dirty_files(root)
    state["updated_at"] = utc_now()
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "exit_code": args.exit_code}))
    return 0


def parse_line_range(value: str) -> dict[str, int]:
    try:
        start_raw, end_raw = value.split(",", 1)
        start = int(start_raw)
        end = int(end_raw)
    except Exception as exc:
        raise ValueError("--line-range must be '<start>,<end>'") from exc
    if start <= 0 or end < start:
        raise ValueError("--line-range must use positive lines with end >= start")
    return {"start": start, "end": end}


def cmd_checkpoint(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    file_path = repo_relative(root, args.file, must_exist=False)
    checkpoint = {
        "task": state.get("current_task"),
        "file": file_path,
        "line_range": parse_line_range(args.line_range),
        "test_name": args.test_name or None,
        "exit_code": args.exit_code,
        "recorded_at": utc_now(),
    }
    state["task_checkpoint"] = checkpoint
    state["dirty_files"] = dirty_files(root)
    state["updated_at"] = checkpoint["recorded_at"]
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "checkpoint": checkpoint}))
    return 0


def current_short_commit(root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise ValueError((proc.stderr or proc.stdout).strip() or "git rev-parse failed")
    return proc.stdout.strip()


def cmd_task_complete(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    commit = current_short_commit(root)
    state.setdefault("task_status", {})[args.task] = "done"
    state["current_task"] = args.task
    state["last_completed_task"] = args.task
    state[f"{args.task}_commit"] = commit
    state["last_note"] = f"{args.task} completed at {commit}"
    state["blocker"] = None
    if (state.get("task_checkpoint") or {}).get("task") == args.task:
        state["task_checkpoint"] = None
    state["dirty_files"] = dirty_files(root)
    state["updated_at"] = utc_now()
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "task": args.task, "commit": commit}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    require_slug(args.slug)
    state = load_cursor(root, args.slug)
    state["closed_at"] = utc_now()
    state["updated_at"] = state["closed_at"]
    state["next_action"] = "closed"
    write_cursor(root, args.slug, state)
    print(json.dumps({"cursor": str(cursor_path(root, args.slug)), "slug": args.slug, "closed": True}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain a tiny Agent Forge continuity cursor.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to the current directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Create or replace a continuity cursor.")
    p_start.add_argument("--slug", required=True)
    p_start.add_argument("--plan", required=True)
    p_start.add_argument("--task", required=True)
    p_start.add_argument("--next-action", default="")
    p_start.set_defaults(func=cmd_start)

    p_advance = sub.add_parser("advance", help="Update task status and next action.")
    p_advance.add_argument("--slug", required=True)
    p_advance.add_argument("--task", required=True)
    p_advance.add_argument("--status", choices=["pending", "in_progress", "blocked", "done"], required=True)
    p_advance.add_argument("--note", default="")
    p_advance.add_argument("--next-action", default="")
    p_advance.set_defaults(func=cmd_advance)

    p_verify = sub.add_parser("verify", help="Record the latest verification command.")
    p_verify.add_argument("--slug", required=True)
    p_verify.add_argument("--cmd", required=True)
    p_verify.add_argument("--exit-code", type=int, required=True)
    p_verify.add_argument("--artifact", default=None)
    p_verify.set_defaults(func=cmd_verify)

    p_checkpoint = sub.add_parser("checkpoint", help="Record precise mid-task resume state.")
    p_checkpoint.add_argument("--slug", required=True)
    p_checkpoint.add_argument("--file", required=True)
    p_checkpoint.add_argument("--line-range", required=True, help="Line range as '<start>,<end>'.")
    p_checkpoint.add_argument("--test-name", default=None)
    p_checkpoint.add_argument("--exit-code", type=int, default=None)
    p_checkpoint.set_defaults(func=cmd_checkpoint)

    p_task_complete = sub.add_parser("task-complete", help="Record the git commit that completed a task.")
    p_task_complete.add_argument("--slug", required=True)
    p_task_complete.add_argument("--task", required=True)
    p_task_complete.set_defaults(func=cmd_task_complete)

    p_status = sub.add_parser("status", help="Print the cursor JSON.")
    p_status.add_argument("--slug", required=True)
    p_status.set_defaults(func=cmd_status)

    p_close = sub.add_parser("close", help="Mark a cursor closed without deleting evidence.")
    p_close.add_argument("--slug", required=True)
    p_close.set_defaults(func=cmd_close)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"continuity-cursor: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

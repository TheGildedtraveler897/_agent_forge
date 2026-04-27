#!/usr/bin/env python3
"""
codex_cost_table.py

Print a small "what would this have cost on the API" table across multiple models,
using *your local Codex CLI usage logs* (~/.codex/logs_2.sqlite).

Why: Codex TUI's status line isn't currently extensible with custom computed fields,
so this script is a fast, repeatable way to build pricing intuition.

Pricing rates below are hardcoded from OpenAI's pricing table as-of 2026-04-25.
Update the PRICING_USD_PER_1M map if rates change.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from typing import Any, Iterable


# As-of 2026-04-25 (USD per 1M tokens), sourced from the OpenAI pricing table.
# Keys match the "model" slug shown in Responses API payloads.
PRICING_USD_PER_1M: dict[str, dict[str, float | None]] = {
    "gpt-5.4": {"in": 2.50, "cached_in": 0.25, "out": 15.00},
    "gpt-5.2": {"in": 1.75, "cached_in": 0.175, "out": 14.00},
    "gpt-5": {"in": 1.25, "cached_in": 0.125, "out": 10.00},
    "gpt-5-mini": {"in": 0.25, "cached_in": 0.025, "out": 2.00},
    "gpt-5-nano": {"in": 0.05, "cached_in": 0.005, "out": 0.40},
    "gpt-4.1": {"in": 2.00, "cached_in": 0.50, "out": 8.00},
    "gpt-4.1-mini": {"in": 0.40, "cached_in": 0.10, "out": 1.60},
    "gpt-4.1-nano": {"in": 0.10, "cached_in": 0.025, "out": 0.40},
    "gpt-4o": {"in": 2.50, "cached_in": 1.25, "out": 10.00},
    "gpt-4o-mini": {"in": 0.15, "cached_in": 0.075, "out": 0.60},
    # Some Codex-facing aliases may appear in payloads depending on config:
    "gpt-5.2-codex": {"in": 1.75, "cached_in": 0.175, "out": 14.00},
    "gpt-5.2-chat-latest": {"in": 1.75, "cached_in": 0.175, "out": 14.00},
}


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int

    @property
    def non_cached_input_tokens(self) -> int:
        v = self.input_tokens - self.cached_input_tokens
        return v if v > 0 else 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def _default_logs_db_path() -> str:
    home = os.environ.get("HOME") or ""
    return os.path.join(home, ".codex", "logs_2.sqlite")


def _default_markers_path() -> str:
    home = os.environ.get("HOME") or ""
    return os.path.join(home, ".codex", "memories", "codex_cost_markers.json")


def _load_markers(path: str) -> dict[str, dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # name -> {ts: int, created_at: str, note?: str}
            return {str(k): (v if isinstance(v, dict) else {}) for k, v in data.items()}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return {}


def _save_markers(path: str, markers: dict[str, dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(markers, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _iter_recent_response_completed_payloads(
    con: sqlite3.Connection, *, since_ts: int | None, limit: int
) -> Iterable[tuple[int, str, dict[str, Any]]]:
    """
    Yield (ts, model, usage_dict) for recent response.completed events.
    """
    cur = con.cursor()
    params: list[Any] = []
    where = (
        "target='log' and feedback_log_body like 'Received message %' "
        "and feedback_log_body like '%\"type\":\"response.completed\"%'"
    )
    if since_ts is not None:
        where += " and ts >= ?"
        params.append(int(since_ts))

    cur.execute(
        f"""
        select ts, feedback_log_body
        from logs
        where {where}
        order by id desc
        limit ?
        """,
        (*params, int(limit)),
    )

    msg_re = re.compile(r"^Received message\s+(\{.*\})\s*$", re.S)
    for ts, body in cur.fetchall():
        if not isinstance(body, str):
            continue
        m = msg_re.match(body)
        if not m:
            continue
        try:
            msg = json.loads(m.group(1))
        except Exception:
            continue
        resp = msg.get("response")
        if not isinstance(resp, dict):
            continue
        if resp.get("status") != "completed":
            continue
        model = resp.get("model")
        usage = resp.get("usage")
        if not isinstance(model, str) or not isinstance(usage, dict):
            continue
        yield int(ts), model, usage


def _parse_usage(usage: dict[str, Any]) -> Usage | None:
    try:
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        itd = usage.get("input_tokens_details") or {}
        otd = usage.get("output_tokens_details") or {}
        cached = int((itd.get("cached_tokens") if isinstance(itd, dict) else 0) or 0)
        reasoning = int(
            (otd.get("reasoning_tokens") if isinstance(otd, dict) else 0) or 0
        )
    except Exception:
        return None
    return Usage(
        input_tokens=input_tokens,
        cached_input_tokens=cached,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
    )


def _usd(cost_per_1m: float, tokens: int) -> float:
    return (cost_per_1m * tokens) / 1_000_000.0


def _estimate_cost_usd(usage: Usage, model: str) -> float | None:
    rates = PRICING_USD_PER_1M.get(model)
    if not rates:
        return None
    in_rate = rates.get("in")
    cached_rate = rates.get("cached_in")
    out_rate = rates.get("out")
    if in_rate is None or out_rate is None:
        return None
    cached_rate = 0.0 if cached_rate is None else float(cached_rate)
    return (
        _usd(float(in_rate), usage.non_cached_input_tokens)
        + _usd(float(cached_rate), usage.cached_input_tokens)
        + _usd(float(out_rate), usage.output_tokens)
    )


def _format_int(n: int) -> str:
    return f"{n:,}"


def _report(
    *,
    db_path: str,
    since_ts: int | None,
    max_events: int,
    models_csv: str,
    show_events: bool,
    window_label: str,
) -> int:
    if not os.path.exists(db_path):
        print(f"missing DB: {db_path}", file=sys.stderr)
        return 2

    con = sqlite3.connect(db_path)
    try:
        total = Usage(
            input_tokens=0, cached_input_tokens=0, output_tokens=0, reasoning_tokens=0
        )
        events: list[tuple[int, str, Usage]] = []
        for ts, model, usage_dict in _iter_recent_response_completed_payloads(
            con, since_ts=since_ts, limit=int(max_events)
        ):
            u = _parse_usage(usage_dict)
            if not u:
                continue
            total = Usage(
                input_tokens=total.input_tokens + u.input_tokens,
                cached_input_tokens=total.cached_input_tokens + u.cached_input_tokens,
                output_tokens=total.output_tokens + u.output_tokens,
                reasoning_tokens=total.reasoning_tokens + u.reasoning_tokens,
            )
            events.append((ts, model, u))
    finally:
        con.close()

    if not events:
        print("No response.completed usage events found for the selected window.")
        print("Tip: run this after you’ve generated at least one assistant response in Codex CLI.")
        return 1

    cached_pct = (
        (100.0 * total.cached_input_tokens / total.input_tokens)
        if total.input_tokens
        else 0.0
    )
    print(f"Codex usage ({window_label}):")
    print(
        f"  input={_format_int(total.input_tokens)} "
        f"(cached={_format_int(total.cached_input_tokens)}, {cached_pct:.1f}%) "
        f"output={_format_int(total.output_tokens)} "
        f"reasoning={_format_int(total.reasoning_tokens)} "
        f"total={_format_int(total.total_tokens)}"
    )

    models = [m.strip() for m in str(models_csv).split(",") if m.strip()]
    rows: list[tuple[str, float | None]] = []
    for m in models:
        rows.append((m, _estimate_cost_usd(total, m)))

    name_w = max(len("model"), *(len(m) for m, _ in rows))
    cost_w = len("est_cost_usd")
    print("\nEstimated API cost (USD):")
    print(
        f"  {'model'.ljust(name_w)}  {'est_cost_usd'.rjust(cost_w)}   "
        f"(rates: USD / 1M tokens; cached input billed separately)"
    )
    for m, cost in rows:
        if cost is None:
            cost_s = "n/a"
        else:
            cost_s = f"${cost:,.4f}"
        print(f"  {m.ljust(name_w)}  {cost_s.rjust(cost_w)}")

    if show_events:
        # Show a few most recent events (newest first already)
        print("\nRecent events (newest first):")
        for ts, model, u in events[: min(12, len(events))]:
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            print(
                f"  {dt}  model={model}  in={_format_int(u.input_tokens)} "
                f"(cached={_format_int(u.cached_input_tokens)}) out={_format_int(u.output_tokens)} "
                f"reasoning={_format_int(u.reasoning_tokens)}"
            )

    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Estimate API cost for Codex usage.")
    ap.add_argument(
        "--db",
        default=_default_logs_db_path(),
        help="Path to Codex logs SQLite DB (default: ~/.codex/logs_2.sqlite).",
    )
    ap.add_argument(
        "--max-events",
        type=int,
        default=200,
        help="Max number of response.completed events to scan (default: 200).",
    )
    ap.add_argument(
        "--models",
        default="gpt-5.4,gpt-5.2,gpt-5,gpt-5-mini,gpt-4.1,gpt-4o",
        help="Comma-separated model slugs to include in the cost table.",
    )
    ap.add_argument(
        "--show-events",
        action="store_true",
        help="Also print per-event usage summary (last few events within the window).",
    )
    ap.add_argument(
        "--markers",
        default=_default_markers_path(),
        help="Path to marker JSON (default: ~/.codex/memories/codex_cost_markers.json).",
    )

    sub = ap.add_subparsers(dest="cmd", required=False)

    rep = sub.add_parser(
        "report",
        help="Report usage for a lookback window (default command if none given).",
    )
    rep.add_argument(
        "--minutes",
        type=int,
        default=120,
        help="Look back window in minutes (default: 120). Use 0 to scan latest max-events only.",
    )

    epic = sub.add_parser("epic", help="Persistent epic baseline tracking via markers.")
    epic_sub = epic.add_subparsers(dest="epic_cmd", required=True)

    epic_start = epic_sub.add_parser("start", help="Create/update an epic marker (baseline).")
    epic_start.add_argument("name", nargs="?", default="default", help="Epic name (default: default).")
    epic_start.add_argument("--note", default="", help="Optional note stored with the marker.")

    epic_status = epic_sub.add_parser("status", help="Report usage since an epic marker.")
    epic_status.add_argument("name", nargs="?", default="default", help="Epic name (default: default).")

    epic_reset = epic_sub.add_parser("reset", help="Delete an epic marker.")
    epic_reset.add_argument("name", nargs="?", default="default", help="Epic name (default: default).")

    epic_list = epic_sub.add_parser("list", help="List existing epic markers.")

    args = ap.parse_args(argv)

    now = int(time.time())
    if args.cmd in (None, "report"):
        minutes = int(getattr(args, "minutes", 120))
        since_ts = now - minutes * 60 if minutes > 0 else None
        window_label = f"last {minutes}m" if since_ts is not None else f"last {args.max_events} events"
        return _report(
            db_path=str(args.db),
            since_ts=since_ts,
            max_events=int(args.max_events),
            models_csv=str(args.models),
            show_events=bool(args.show_events),
            window_label=window_label,
        )

    if args.cmd == "epic":
        markers_path = str(args.markers)
        markers = _load_markers(markers_path)

        if args.epic_cmd == "list":
            if not markers:
                print("No epic markers set.")
                return 0
            print("Epic markers:")
            for name in sorted(markers.keys()):
                m = markers.get(name) or {}
                ts = int(m.get("ts") or 0)
                created_at = str(m.get("created_at") or "")
                note = str(m.get("note") or "")
                dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "?"
                extra = f"  note={note}" if note else ""
                extra2 = f"  created_at={created_at}" if created_at else ""
                print(f"  {name}  ts={ts}  ({dt}){extra}{extra2}")
            return 0

        name = str(getattr(args, "name", "default") or "default")
        if args.epic_cmd == "start":
            note = str(getattr(args, "note", "") or "")
            markers[name] = {
                "ts": now,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
                "note": note,
            }
            _save_markers(markers_path, markers)
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
            print(f"Epic '{name}' started at ts={now} ({dt}).")
            return 0

        if args.epic_cmd == "reset":
            if name in markers:
                del markers[name]
                _save_markers(markers_path, markers)
                print(f"Epic '{name}' marker deleted.")
            else:
                print(f"Epic '{name}' marker not found.")
            return 0

        if args.epic_cmd == "status":
            m = markers.get(name)
            if not m or not m.get("ts"):
                print(f"Epic '{name}' marker not found.")
                print("Create one with: codex-cost epic start " + name)
                return 2
            since_ts = int(m["ts"])
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(since_ts))
            window_label = f"since epic '{name}' ({dt})"
            return _report(
                db_path=str(args.db),
                since_ts=since_ts,
                max_events=int(args.max_events),
                models_csv=str(args.models),
                show_events=bool(args.show_events),
                window_label=window_label,
            )

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

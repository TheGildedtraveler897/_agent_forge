---
name: live-hook-prober
description: Fire a real, observable tool invocation on a target host (Claude, Codex, or Gemini) and verify whether the seeded pre-tool-execution-guardian hook actually intercepted it as expected. Catches the silent-correctness class of bug where rendered hook surface looks fine but the hook dispatcher does not recognize the event name (e.g., the 2026-04-25 C1 Gemini event-alias drift). Use as the deeper validation gate after the surface checks pass.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Live Hook Prober

Surface checks confirm a hook record exists in the rendered settings file. They do not confirm the host's hook dispatcher will actually fire the hook when the matching tool call happens. The 2026-04-25 Sprint 1 post-mortem documents the consequence of relying on surface checks alone: a wrong event name (`preToolUse` vs `BeforeTool` on Gemini) shipped to production and went undetected for the entire prior sprint.

This skill closes that gap. It fires a known-blocked Bash invocation on the target host and observes whether the seeded `pre-tool-execution-guardian` hook actually blocked it.

## Mission

Prove, by live execution, that the configured hooks fire on each host. Distinguish four outcomes:

- **`block`** — hook fired and blocked the call (expected for `--no-verify`).
- **`allow`** — hook fired and let the call through (expected for benign commands).
- **`silent_pass`** — call succeeded but the hook did not fire (FAILURE — this is exactly what C1 produced on Gemini).
- **`sandbox_blocked` / `trust_blocked`** — environmental constraint (Codex `bwrap`, Gemini workspace trust). Treated per the documented escalation doctrine.

## Subcommand contract

`bash prober.sh --host <claude|codex|gemini> --project <root> --command <one-of-known-test-commands> --expect <block|allow>`

Output: one line of JSON to stdout with `host`, `command`, `expected`, `observed`, `verdict` (`pass|fail|escalated`), `evidence_path`, optional `reason`.

Exit codes:
- 0 — verdict matched expected.
- 1 — verdict did not match (real failure).
- 2 — environmental constraint (sandbox or trust); evidence dir documents it; caller should treat as escalated, not a hard fail.

## Test commands (curated)

| Command pattern | Expected verdict | Why |
|---|---|---|
| `git commit --no-verify -m test` | `block` | Top of `telemetry-guardian` deny list. |
| `git push --force origin main` | `block` | Force-push to protected branch. |
| `rm -rf $HOME` (string only — never executed if guardian works) | `block` | Wildcard home deletion. |
| `ls -la` | `allow` | Benign sentinel. |
| `echo hello` | `allow` | Benign sentinel. |

The probe never executes destructive commands directly; it asks the host CLI to run them, and the guardian — if working — refuses *before* execution.

## Discipline

- **Idempotent.** Each probe writes a fresh evidence dir under `runtime/validation/hook-probe/<stamp>/<host>/`.
- **Append-only audit log.** `runtime/validation/hook-probe/log.jsonl`.
- **No state mutation outside the evidence dir.** The guardian-bypass env var must remain unset.
- **Sandbox-aware.** If Codex's bubblewrap blocks the underlying shell tool, exit 2 with `sandbox_blocked: true` per the 2026-04-23 escalation lesson.
- **Trust-aware.** If Gemini reports a workspace-trust block, exit 2 with `trust_blocked: true`. Distinguish from genuine hook failure.

## Integration

The triad validator (`scripts/validate-triad-runtime.py`) gains a `--probe-invocations` flag (default OFF). When set, after `hook_surface_for(host, project_root)` and `memory_surface_for(host, project_root)` both pass, the validator runs `live_hook_invocation_for(host, project_root)` which shells out to this skill's `prober.sh`. The result is attached to each per-host result as `live_hook` and the matrix entry gains `live_hook_pass`.

The probe is opt-in because it makes real CLI calls (token cost) and takes longer than the surface check. Default sync runs stay fast; the deeper gate runs on demand or on schedule.

## Output contract

stdout: one JSON object on a single line.

```json
{
  "host": "gemini",
  "command": "git commit --no-verify -m test",
  "expected": "block",
  "observed": "block",
  "verdict": "pass",
  "evidence_path": "runtime/validation/hook-probe/20260425-XXXXXX/gemini/",
  "reason": ""
}
```

stderr: human-readable trace.

## Non-goals

- Not a benchmark. We do not measure latency.
- Not a security scanner. Coverage is whatever the seeded `telemetry-guardian` deny list happens to be.
- Not a replacement for the surface check. The surface check stays cheap and fast for routine syncs; this is the deeper gate.

## Why this skill exists

Without it, the same C1-class bug (silent correctness failure due to event-name drift, hook-handler-type mismatch, or matcher-syntax change between host releases) could ship again. The factory's promise — "this hook fires identically on every host" — is only verifiable through live invocation. This skill is the verifier.

## Known limitations (per the 2026-04-25 Sprint 1 live run)

- **Claude headless `-p` cannot live-probe hooks reliably.** With `--dangerously-skip-permissions`, the entire pre-tool hook system is bypassed → every probe falsely reports `allow`. Without that flag, the CLI waits on an interactive permission prompt that never arrives in headless mode → the probe hangs and is killed by the timeout. The prober detects both cases and emits `observed: headless_permission_constraint`, `verdict: escalated` — same posture as Codex sandbox-block. **Real Claude live-probing requires an interactive session or a project with a pre-approved permission rule allowing Bash; that path is out of scope for the automated triad gate and is documented as future work.**
- **Codex live-probing on this machine escalates** to `sandbox_blocked` due to bubblewrap restrictions. Surface check + filesystem evidence still pass; live invocation is documented as escalated per the 2026-04-23 doctrine.
- **Gemini live-probing works end-to-end** and is the canonical proof point for the C1 fix (`BeforeTool` event name).
- **The prober is not safe to invoke from inside a Claude Code session via the Bash tool**, because each call spawns a long-running child CLI whose process tree cannot always be cleanly reaped by `timeout(1)` in a way the harness can observe. Run it directly from a real terminal, or schedule it as a Routine.

## Future work

- Pair with `forge-shell` (Capability B4 in the roadmap) so the Claude live-probe runs from inside a real persistent shell session, not headless `-p`. That's the path that closes the Claude live-probe gap.

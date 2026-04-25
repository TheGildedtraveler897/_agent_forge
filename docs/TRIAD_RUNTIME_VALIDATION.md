# Triad Runtime Validation

Use this runbook when you want live proof that the generated Claude, Codex, and Gemini surfaces work after a factory change.

## Purpose

Answer four questions:

1. Can the omni-factory regenerate every host surface from canonical sources?
2. Can every governed project's surface actually be enumerated by each host CLI at runtime?
3. Does the knowledge anchor stay visible where each host can realistically consume it?
4. Can a sandbox-blocked host still be validated via paired filesystem evidence?

## Preflight Reads

Before mutating anything, read:

1. `~/Projects/AGENTS.md`
2. `_agent_forge/AGENTS.md`
3. `_agent_forge/CLAUDE.md`
4. `_agent_forge/GEMINI.md`
5. `_agent_forge/docs/CONOPS.md`
6. `_agent_forge/docs/HANDOFF.md`
7. `_agent_forge/docs/LESSONS_LEARNED.md`
8. `_agent_forge/docs/HOST_INTEGRATIONS.md`

## Structural Generation

Run from `~/Projects/_agent_forge`:

```bash
python3 scripts/omni_factory.py render-registry > registry.json
python3 scripts/omni_factory.py sync-claude --project jarvis
python3 scripts/omni_factory.py sync-codex --project jarvis
python3 scripts/omni_factory.py sync-gemini --project jarvis
python3 scripts/verify-agent-forge.py
```

Structural success means:

- `registry.json` matches canonical sources
- generated host surfaces exist for the target project
- verifier reports no failures
- legacy `_agent_forge/claude/` residue is absent

Structural success is necessary but **not sufficient**. Files on disk do not prove host CLIs can see them. The scripted triad proof below is the gate that actually confirms runtime reachability.

## Scripted Triad Proof (default)

Run:

```bash
python3 scripts/validate-triad-runtime.py --project <governed-project-name>
```

The script probes all three host CLIs sequentially and compares their observed skill lists against `registry.json`:

- **Gemini** — `gemini skills list --all`. Output parsed directly. Method recorded as `cli`.
- **Claude** — `claude -p '...' --output-format text --dangerously-skip-permissions`. The prompt asks Claude to enumerate available skills between `===SKILLS===` and `===END===` markers. Method recorded as `cli`.
- **Codex** — `codex exec '...'` with the same enumeration prompt. If Codex's internal sandbox hits `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`, the script falls back to filesystem inspection of `~/.agents/skills/` and the project's `.agents/skills/`. Method recorded as `filesystem-escalated`.

For each host, if the CLI returns no parseable skill set (e.g. the CLI is not installed, timed out, or refused), the script still falls back to filesystem inspection of the appropriate project surface (`.claude/skills/`, `.agents/skills/`, or `.gemini/skills/`). Method recorded as `filesystem`.

### Success criteria

- Exit code `0`
- A new run directory appears under `runtime/validation/triad/<YYYYMMDD-HHMMSS>/`
- `summary.json` reports `pass: true` overall
- Per-host `result.json` reports `missing: []` **and** `hook_surface.pass: true` (guardian present in the rendered settings file)
- `runtime/validation-matrix.json` receives an updated `triad_runtime.<project>` entry with both `pass` and `hook_pass: true` per host
- The expected skill count tracks the canonical `registry.json` (currently 27 with `telemetry-guardian` shipped)

### Hook surface check

After enumerating skills for a host, the validator runs `hook_surface_for(host, project_root)` to confirm that at least one canonical hook from `policies/hooks.json` reached the rendered host-native settings file:

- Claude → reads `<project>/.claude/settings.json`, looks for `pre-tool-execution-guardian` in the `hooks` block.
- Codex → reads `<project>/.codex/hooks.json`, looks for the same hook id.
- Gemini → reads `<project>/.gemini/settings.json`, looks for the same hook id under `hooks`.

If the guardian record is missing from any host's surface, that host's `pass` becomes `false` and overall pass is `false`. This catches the silent-rot failure mode where `policies/hooks.json` is updated but a renderer was not re-run for that project.

### Artifact shape

```
runtime/validation/triad/<stamp>/
  summary.json       # overall pass, per-host result pointers, project, timestamp
  gemini/
    result.json      # host, method, pass, expected_count, observed_count, missing, cli_exit, cli_cmd
    gemini-stdout.txt
    gemini-stderr.txt
  claude/
    result.json
    claude-stdout.txt
    claude-stderr.txt
  codex/
    result.json      # plus sandbox_blocked: true|false
    codex-stdout.txt
    codex-stderr.txt
```

### Matrix shape

`runtime/validation-matrix.json` receives:

```json
{
  "triad_runtime": {
    "<project-name>": {
      "last_run": "YYYYMMDD-HHMMSS",
      "overall_pass": true,
      "per_host": {
        "claude": {"pass": true, "hook_pass": true, "method": "cli"},
        "codex":  {"pass": true, "hook_pass": true, "method": "filesystem-escalated"},
        "gemini": {"pass": true, "hook_pass": true, "method": "cli"}
      },
      "artifact_path": "runtime/validation/triad/<stamp>"
    }
  }
}
```

### Distinguishing sandbox block vs. missing surfaces

If Codex reports `pass: false`, check `codex/result.json`:

- `sandbox_blocked: true` and `observed_count == expected_count` via filesystem — on this machine, Codex could not self-inspect because `bwrap` refused a loopback interface. The surfaces are correctly generated; only the in-Codex shell tool is blocked. This is the documented 2026-04-23 escalation path and is treated as pass.
- `sandbox_blocked: true` and `observed_count < expected_count` — a real gap: some generated surfaces are missing on disk. Re-run `sync-claude` / `sync-codex` / `sync-gemini` and investigate.
- `sandbox_blocked: false` and the CLI returned no skill set — a Codex runtime regression, not a sandbox issue. Investigate the Codex session logs under `codex/codex-stdout.txt` and `codex/codex-stderr.txt`.

## Manual Fallback

If the scripted path is unavailable (CLI binaries missing, or you need a human-judgement confirmation), use the prompt-based runbook below.

### Live Codex Proof (manual)

```bash
python3 scripts/validate-codex-runtime.py --project jarvis
```

Success criteria mirror `codex/result.json` above: a structured JSON artifact with `pass: true` or a `sandbox_blocked: true` pair proven by filesystem evidence.

### Live Claude Proof (manual)

In a Claude session started from the project root, ask:

- "List the instruction sources you loaded for this repo in order."
- "Name the durable lesson ledger that governs shared Agent Forge work, if it is in scope."

Then invoke one generated project surface (for example `/jarvis-reviewer`).

Claude success means:

- it reports the shared and project instruction chain coherently
- it recognizes the project-local generated agent or command
- it does not describe `_agent_forge/claude/` as a source of truth

### Live Gemini Proof (manual)

In a Gemini session started from the project root, run `/memory show` and ask:

- "Which context files are loaded for this repo right now?"
- "Is the factory lesson ledger part of the current context chain?"

Use `/help` or `gemini skills list` to confirm generated project skills are present.

Gemini success means:

- `GEMINI.md` is in the loaded context chain
- the chain reaches the shared factory contract and lesson ledger
- generated commands and skills are visible once the folder is trusted

## Final Report

Separate the outcome into:

- confirmed working
- fixed during run
- still blocked (host-by-host, with the specific method that failed)
- manual follow-up

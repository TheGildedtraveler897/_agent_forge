# TECH_DEBT

This file records the most important remaining gaps as of 2026-04-28, after the memory-bridge and MCP namespace-routing sprints shipped and the Sprint 4 proof at `runtime/validation/triad/20260427-234006/summary.json` passed.

## Recently Resolved (no longer debt)

- **Claude runtime validator** — shipped 2026-04-24 as part of `scripts/validate-triad-runtime.py`. Probes the live `claude` CLI; falls back to filesystem on failure.
- **Gemini runtime validator** — same triad-validator script also probes the live `gemini` CLI.
- **Universal pre-tool guardrail** — `telemetry-guardian` shipped 2026-04-24 and now renders through `policies/hooks.json` v3 handler records with three host renderers; live deny list covering `--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777.
- **Universal cross-host memory layer** — `MEMORY.md` + `.forge_state/` shipped 2026-04-25 with `policies/memory.json` schema + `memory-archivist` skill + `memory_surface_for` triad gate.
- **Cross-host memory bridge** — `memory-bridge` shipped 2026-04-27 with host-local outbound/inbound bridge state, async session lifecycle hooks, and `bridge_pass` in the triad validator.
- **MCP namespace routing** — `global-mcp.json` v2 shipped 2026-04-27 with the seeded `forge-factory` stdio server, host-safe aliases, trust-gated project routing, and `mcp_pass` in the triad validator.
- **Codex sandbox-marker drift** — `host_sandbox_blocked()` in the triad validator now recognizes the newer Codex error strings (`needs access to create user namespaces`, `shell tool failed before command execution`, etc.) so sandbox-blocked Codex runs still escalate to filesystem-escalated evidence.
- **Hook lifecycle v3 + Codex event-key drift** — `policies/hooks.json` now uses explicit handler objects, Codex native keys render as PascalCase (`PreToolUse`, `SessionStart`, `Stop`), and `hook_surface_for()` checks every active hook record's native event key.

## Open Debt

- Host-native MCP management UIs are not equivalent proof surfaces; `mcp_pass` currently means rendered config alias plus direct stdio `tools/list` smoke, not guaranteed parity across `mcp get/list` commands.
- Non-command hook handlers (`http`, `mcp_tool`, `prompt`, `agent`) are schema-modeled and dormant, but not live-dispatch proven. Sprint 2 deliberately validated command hooks only until host-safe sentinels exist.
- The Codex runtime validator performs live execution, but it still does not prove every generated command or agent invocation path; it confirms enumeration, not invocation correctness.
- On this machine, Codex runtime inspection is regularly blocked by `bwrap` namespace restrictions; the validator escalates to filesystem-escalated evidence per documented doctrine, but a sandbox-friendly Codex probe would be cleaner.
- Governed project repos can remain dirty after sync because generated host surfaces are delivery targets. `_agent_forge` is the canonical authoring repo; do not hand-edit generated target surfaces to chase clean status.
- `bootstrap-project.sh --existing` and `--with-local-skills` still need deliberate live exercise.
- Debian and macOS suitcase proofs are still pending with real operators, not just local smoke tests.
- Team manifests remain conceptual; there is no executable orchestration layer yet (deferred deliberately — the Pathfinder roadmap `crew-director` capability is the future home for this).
- Several domain skills (`legal-counsel`, `corporate-controller`, `infra-architect`, `brand-guardian`) contain time-sensitive knowledge and should be refreshed periodically.
- The remote weekly-watchdog routine (see § Pending Remote Routine below) is still blocked on `_agent_forge` having no git remote.

## Follow-On Work

1. Broaden MCP proof depth from direct stdio smoke to true host-native tool invocation parity where the CLIs expose stable project-local inspection paths.
2. Resolve or work around the local Codex `bwrap` sandbox failure for cleaner runtime proof.
3. Exercise `bootstrap-project.sh --existing` on a real existing repo.
4. Exercise the suitcase path on a fresh Debian VM and a fresh macOS machine.
5. Push `_agent_forge` to a GitHub remote so the weekly watchdog routine can be scheduled.
6. Promote or supersede ledger entries in `docs/LESSONS_LEARNED.md` before they turn into a second backlog.

## Notes For The Next Session

- Start with `_agent_forge/AGENTS.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, and `docs/LESSONS_LEARNED.md`.
- Use `docs/HOST_INTEGRATIONS.md` for the current host model and `docs/TRIAD_RUNTIME_VALIDATION.md` for live proof.
- Treat `_agent_forge` as the only maintained source of truth for shared capabilities, teams, MCP servers, hooks, and lesson harvesting.

## Pending Remote Routine — Weekly Watchdog After GitHub Push

**Status as of 2026-04-24:** blocked on `_agent_forge` having no git remote. `git remote -v` in this repo returns empty. Once the repo is pushed to GitHub, schedule the routine below via the `/schedule` skill.

### Why this routine exists

`scripts/validate-triad-runtime.py` is now the mandatory final gate after any canonical skill/team/MCP/hook change (see the 2026-04-23 and 2026-04-24 entries in `docs/LESSONS_LEARNED.md`). It catches three failure modes: (a) skills missing from a governed project's `.claude/skills/`, `.agents/skills/`, or `.gemini/skills/` directory; (b) `registry.json` drift vs. canonical `SKILL.md` sources; (c) a host CLI that can no longer enumerate what the factory delivered.

But the validator only runs when a human remembers to run it. A weekly watchdog closes that gap without requiring the remote sandbox to reach the user's local `~/Projects/*` tree or the three host CLIs.

### Remote-environment constraints that shape the design

- Remote CCR agents run in Anthropic's cloud. They cannot reach `~/Projects/jarvis` or any other local governed project.
- The `claude`, `codex`, and `gemini` CLIs are almost certainly not installed in CCR sandboxes. The routine must not depend on them.
- A remote agent CAN clone `_agent_forge` from GitHub, read its files, run Python, diff against committed artifacts, and open a GitHub issue or PR.

### Routine spec (create once the repo is on GitHub)

- **Name:** `agent-forge-weekly-watchdog`
- **Cadence:** weekly, `cron_expression: "0 16 * * 1"` (Mondays 09:00 America/Vancouver = 16:00 UTC). Confirm the UTC conversion against the current DST state when scheduling.
- **Model:** `claude-sonnet-4-6` (default).
- **Environment:** the user's default CCR environment.
- **Repo source:** `https://github.com/<org>/<repo>` for `_agent_forge` (fill in after push).
- **Allowed tools:** `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`.
- **MCP connectors:** none required.

### Prompt (paste verbatim when scheduling)

```
You are the weekly watchdog for the Agent Forge factory. You run in a remote CCR sandbox
and only have this repo clone to work with. You do not have access to any local machine.

Do these two checks, in order, and combine the findings into ONE GitHub issue (not one per check).

## Check 1 — Staleness watchdog

1. Read runtime/validation-matrix.json.
2. Look at the triad_runtime.<project> block for every governed project listed in
   projects.json (jarvis, RoboNaaz, ZorroClaw, homelab, factory, playlist-archive).
3. For each project, compute the age of the last_run field (format: YYYYMMDD-HHMMSS, UTC).
4. Flag any project whose last_run is older than 14 days OR missing entirely.
5. Also flag any project whose overall_pass is false.

## Check 2 — Registry drift auditor

1. Run: python3 scripts/omni_factory.py render-registry > /tmp/fresh-registry.json
2. Diff /tmp/fresh-registry.json against the committed registry.json.
3. Run: python3 scripts/verify-agent-forge.py and capture exit code.
4. Flag any drift in the diff, any non-zero exit from the verifier, and list the specific
   skills or teams that caused the drift.

## Reporting

If BOTH checks are clean (no stale projects and no drift), do nothing. Exit quietly.

Otherwise, open ONE GitHub issue titled "Agent Forge watchdog — <YYYY-MM-DD>" with:
- A "Stale runtime validation" section listing each flagged project with its last_run age.
- A "Registry drift" section with the exact diff and verifier output.
- A "Recommended actions" section naming the operator commands to run locally:
    python3 scripts/omni_factory.py render-registry > registry.json
    python3 scripts/omni_factory.py sync-claude --project <name>
    python3 scripts/omni_factory.py sync-codex  --project <name>
    python3 scripts/omni_factory.py sync-gemini --project <name>
    python3 scripts/verify-agent-forge.py
    python3 scripts/validate-triad-runtime.py --project <name>

Do NOT open a pull request. Do NOT modify any committed file in this run. Your output is
the issue itself.
```

### Why an issue, not a PR

Regenerated `registry.json` and re-synced host surfaces are functions of the user's local skills + governed projects on disk. A remote-only PR would be generating partial truth (skills from the repo, but no project-local surfaces to compare against). The issue is the correct artifact: it says "you need to run these commands locally."

### Prerequisites before scheduling

1. Push `_agent_forge` to a GitHub repo under your control.
2. Confirm the GitHub App / OAuth used by CCR has write access to issues on that repo.
3. Decide whether to pin the routine to `master` or switch to `main` first (the repo's recorded main branch is `main`, current working branch is `master`).

### Future expansion

Once other governed projects (jarvis, homelab, etc.) are also pushed to GitHub, a second routine could clone each one, read its `.claude/skills/`, `.agents/skills/`, and `.gemini/skills/` directories, and cross-check against `_agent_forge`'s `registry.json`. That would give true per-project runtime evidence from the remote sandbox without needing the three host CLIs. Not in scope for the initial watchdog.

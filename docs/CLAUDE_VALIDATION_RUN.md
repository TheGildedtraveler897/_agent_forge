# Claude Validation Run

This runbook packages the current Agent Forge workspace so Claude can perform a full governance scan, runtime validation pass, and remediation loop without guessing the intended model.

## Purpose

Use this when you want Claude to independently verify that the multi-agent setup built under `~/Projects` actually works for Claude, not just for Codex.

This run is meant to answer four questions:

1. Can Claude discover and use the shared governance layer correctly?
2. Can Claude see the canonical `_agent_forge` adapters and governed-project wiring?
3. Can Claude operate inside governed projects using the documented handoff flow?
4. If it finds drift, can it repair the workspace without breaking the canonical source-of-truth model?

## Current Baseline

Verified locally on `2026-04-04`:

- `_agent_forge/scripts/verify-agent-forge.py` passes.
- Global Claude adapters exist under `~/.claude/agents/` and `~/.claude/commands/` as symlinks to canonical `_agent_forge/claude/...` sources.
- Codex skills exist under `~/.codex/skills/` as symlinks to canonical `_agent_forge/skills/...` sources.
- Project-local Jarvis Claude adapters exist under `jarvis/.claude/agents/` and `jarvis/.claude/commands/` as symlinks to canonical `_agent_forge/claude/projects/jarvis/...` sources.
- Governed project footprints declared in `registry.json` are present.

What remains to be proven by Claude:

- runtime discovery of installed Claude commands and subagents
- correct Claude interpretation of shared and project-local governance docs
- ability to perform a live audit and remediation loop without undocumented assumptions

## Preflight

Start Claude in:

```bash
cd /home/pheonixprotocol/Projects
```

Before Claude mutates anything, it should read:

1. `~/Projects/AGENTS.md`
2. `~/Projects/CLAUDE.md`
3. `~/Projects/_agent_forge/AGENTS.md`
4. `~/Projects/_agent_forge/docs/CLAUDE_NATIVE.md`
5. `~/Projects/_agent_forge/docs/TEAM_RUNBOOKS.md`
6. `~/Projects/_agent_forge/docs/GOVERNANCE.md`
7. `~/Projects/_agent_forge/registry.json`

Then capture baseline state with:

```bash
/home/pheonixprotocol/Projects/_agent_forge/scripts/verify-agent-forge.py
```

Recommended repo-state sweep:

```bash
for d in \
  /home/pheonixprotocol/Projects/jarvis \
  /home/pheonixprotocol/Projects/RoboNaaz \
  /home/pheonixprotocol/Projects/ZorroClaw \
  /home/pheonixprotocol/Projects/homelab \
  /home/pheonixprotocol/Projects/ZorroForge/factory \
  /home/pheonixprotocol/Projects/playlist-archive
do
  echo "===== $d ====="
  if [ -d "$d/.git" ]; then
    git -C "$d" status --short --branch
  else
    echo "(no git repo)"
  fi
  echo
done
```

## Execution Flow

Claude should follow this order:

1. Perform a top-level governance audit from `~/Projects`.
2. Validate global Claude command and subagent discovery.
3. Audit `_agent_forge` as the canonical source of truth.
4. Audit each governed project:
   - `jarvis`
   - `RoboNaaz`
   - `ZorroClaw`
   - `homelab`
   - `ZorroForge/factory`
   - `playlist-archive`
5. Fix validated issues in the smallest coherent increments.
6. Re-run verification after each meaningful repair cluster.
7. Update project `docs/HANDOFF.md` files anywhere meaningful work was performed.

Priority order:

- first: blockers that prevent Claude from seeing or using the governance system
- second: registry, adapter, or symlink drift
- third: governed-project documentation or contract drift
- fourth: low-risk cleanup discovered during the pass

## Allowed Fixes

Claude may autonomously fix:

- broken symlinks
- missing adapter files
- registry alignment issues
- stale governance docs
- missing or inaccurate handoff notes
- portable script issues in sync and verify helpers
- low-risk repo-local governance drift

Claude should preserve these invariants:

- `_agent_forge` remains the canonical source of truth
- `~/.claude`, per-project `.claude`, and `~/.codex/skills` remain delivery targets
- `AGENTS.md` remains the shared multi-agent policy layer
- `CLAUDE.md` remains thin and Claude-specific

Claude should not autonomously perform:

- secret rotation
- credential provisioning
- external account changes
- behavior-changing product work unrelated to the governance validation goal

## Recovery Commands

If Claude finds delivery drift, use the canonical sync helpers instead of ad hoc manual relinking.

Refresh Claude global adapters:

```bash
/home/pheonixprotocol/Projects/_agent_forge/scripts/sync-claude-adapters.sh
```

Refresh Jarvis project-local Claude adapters:

```bash
/home/pheonixprotocol/Projects/_agent_forge/scripts/sync-claude-adapters.sh --project jarvis
```

Refresh Codex skills:

```bash
/home/pheonixprotocol/Projects/_agent_forge/scripts/sync-codex-skills.sh --project jarvis
```

Re-verify the whole workspace:

```bash
/home/pheonixprotocol/Projects/_agent_forge/scripts/verify-agent-forge.py
```

## Required Final Output

Claude's final report should separate:

- confirmed working
- fixed during run
- still blocked
- manual follow-up items

Claude should also state plainly whether the Codex-built multi-agent setup is operational for Claude in practice, not just structurally.

## Copy/Paste Prompt

```text
You are the independent second operator validating the full ZorroForge multi-agent environment.

Mission:
Prove whether Claude can actually operate correctly inside the governance and adapter system built under ~/Projects, not just whether files exist. You must audit, exercise, remediate, verify, and document in loops until the environment is stable.

Operating rules:
- Read ~/Projects/AGENTS.md first, then ~/Projects/CLAUDE.md.
- Treat _agent_forge as the canonical source of truth for shared skills and Claude adapters.
- Do not assume Codex’s work is correct just because the verifier passes; independently confirm behavior.
- Use the governance-team pattern from _agent_forge/docs/TEAM_RUNBOOKS.md.
- Use _agent_forge/docs/CLAUDE_VALIDATION_RUN.md as the execution runbook.
- Start with a structural baseline, then perform live Claude runtime checks.
- Audit the full governed workspace: _agent_forge, jarvis, RoboNaaz, ZorroClaw, homelab, ZorroForge/factory, playlist-archive.
- Use /multi-agent-governor as the primary entrypoint, and use governance subagents if useful.
- You have autonomy to fix validated issues, re-verify them, and continue iterating.
- Preserve the canonical model: _agent_forge is source of truth; ~/.claude, project .claude, and ~/.codex/skills are delivery targets.
- Update docs/HANDOFF.md in any project where you make meaningful changes.
- Keep manual-only items manual: secrets rotation, credentials, or external-account actions.
- Final output must separate: confirmed working, fixed during run, still blocked, and manual follow-up items.

Success criteria:
1. You confirm whether Claude runtime discovery actually works for global commands/subagents and project-local adapters.
2. You fix any validated governance/adapter/documentation drift you find.
3. You leave the workspace in a cleaner and better-documented state than you found it.
4. You provide a final verdict on whether the Codex-built multi-agent setup genuinely works for Claude.
```

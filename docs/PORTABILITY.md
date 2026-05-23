# Portable Governance Notes

## Canonical Model

- `_agent_forge` is the only maintained source of truth for shared capabilities, teams, MCP servers, hooks, and validation doctrine.
- Host-native directories are generated delivery targets, not authoring surfaces.
- Global capabilities must avoid repo-specific paths, machine-specific assumptions, and one-user workflow trivia.

## Native Boot Files

Keep these names native because hosts load them automatically:

- Claude Code: `CLAUDE.md`
- Codex: `AGENTS.md`
- Gemini CLI: `GEMINI.md`

Secondary docs can use host-agnostic names without losing indexing advantages.

## Governed Delivery Surfaces

Claude:

- `~/.claude/agents/`
- `~/.claude/commands/`
- `~/.claude/skills/`
- `<project>/.claude/agents/`
- `<project>/.claude/commands/`
- `<project>/.claude/skills/`
- `<project>/.mcp.json`

Codex:

- `~/.agents/skills/`
- `<project>/.agents/skills/`
- `<project>/.codex/agents/`
- `<project>/.codex/config.toml`
- `<project>/.codex/hooks.json`

Gemini:

- `~/.gemini/agents/`
- `~/.gemini/commands/`
- `~/.agents/skills/`
- `~/.gemini/GEMINI.md`
- `<project>/GEMINI.md`
- `<project>/.gemini/agents/`
- `<project>/.gemini/commands/`
- `<project>/.gemini/skills/`
- `<project>/.gemini/settings.json`

## Suitcase Snapshot Model

- This machine remains the canonical factory development lab.
- Portable deployments are suitcase snapshots, not live mirrors.
- Rebuild the suitcase after improving the factory here; do not patch remote snapshots by hand unless that machine becomes canonical.

Use:

```bash
./scripts/factory-export.sh
```

Deploy on a target machine with:

```bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

## Knowledge Anchor Portability

- Durable lessons live in `docs/LESSONS_LEARNED.md`.
- Harvested entries must stay normalized and append-first.
- Never carry machine-local residue, secrets, or one-off session trivia into the lesson ledger.
- Promote lessons into doctrine only after they prove durable and broadly useful.

## Migration Rule

When a project-local capability becomes reusable:

1. Copy it into `skills/global/`.
2. Remove repo-specific assumptions.
3. Tighten the trigger description.
4. Re-sync the generated host surfaces.

## Safe To Carry

- `_agent_forge/` canonical source
- shared root doctrine docs
- host-agnostic runbooks
- team manifests
- sync/bootstrap/export/deploy/validation scripts
- `docs/LESSONS_LEARNED.md`
- `policies/hooks.json` and `policies/memory.json` (canonical schema definitions)
- `runtime/validation-matrix.json` (the coverage ledger; survives across runs)

What gets re-rendered into governed projects on first sync, not carried directly:

- `<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/` host-native surfaces
- `<project>/MEMORY.md` and `<project>/.forge_state/` (universal state layer)

## Never Carry

- project repositories unless explicitly approved
- `.env` files or credentials
- runtime caches or machine-local settings
- validation artifacts as a substitute for canonical docs
- remote suitcase snapshots as a substitute for the canonical repo

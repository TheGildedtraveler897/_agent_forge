# Sprint Backlog — Codex Execution Prompts

**Last updated:** 2026-04-26.
**Audience:** Codex (CLI agent picking up the next sprint cold).
**Authority:** This file is the contract between the Founder and the executing agent. Each sprint section below is a complete, copy-pasteable execution prompt. Prompts include required reads, web-search obligations, architectural rules, exit gates, and stall warnings.

## How to use this file

1. The Founder copy-pastes the relevant Sprint prompt into a fresh Codex session.
2. Codex reads the required documentation files **before any code is written**.
3. Codex uses its web-search tool to verify current API/CLI specifics against the official 2026 docs.
4. Codex implements per the sprint contract, hitting every exit gate.
5. Codex appends a `LESSONS_LEARNED.md` entry with evidence paths.
6. Codex marks the sprint complete with a status footnote in `docs/PATHFINDER_ROADMAP.md`.

## Sprint status

| Sprint | Title | Status |
|---|---|---|
| Sprint 1 | C1 Hotfix + B1 live-hook-prober | ✅ Shipped 2026-04-26 |
| **Sprint 2** | **A1 Hook Lifecycle V2** | **Ready for Codex** |
| **Sprint 3** | **A2 + B2 Memory Bridge** | **Ready for Codex (after Sprint 2)** |
| **Sprint 4** | **A3 MCP Namespace Prefixing** | **Ready for Codex (after Sprint 3)** |
| Sprint 5+ | (summaries below) | Future |

---

# Sprint 2 — Hook Lifecycle V2 (Architectural Upgrade A1)

## Copy-paste this entire section into Codex

```
SYSTEM: You are executing Sprint 2 of the Agent Forge Omni-Factory roadmap.
Your role is Principal Systems Engineer. You will implement Architectural
Upgrade A1: full 26-event hook lifecycle + handler diversity. Permissions
are pre-granted for the duration of this sprint. Do not prompt the
Founder; surface decisions only via structured artifacts.

PHASE 0 — REQUIRED READS (do this BEFORE any code).
Read these files end-to-end. Do not skim.

  1. ~/Projects/_agent_forge/README.md
  2. ~/Projects/_agent_forge/AGENTS.md
  3. ~/Projects/_agent_forge/docs/CONOPS.md
  4. ~/Projects/_agent_forge/docs/HOST_INTEGRATIONS.md
  5. ~/Projects/_agent_forge/docs/HANDOFF.md
  6. ~/Projects/_agent_forge/docs/LESSONS_LEARNED.md
  7. ~/Projects/_agent_forge/docs/PATHFINDER_LEDGER.md
     (especially Section 2.1, 2.2, 2.3, and Section 4.4 on the BeforeTool
      drift — that is the failure-mode you are extending the schema to
      eliminate at scale)
  8. ~/Projects/_agent_forge/docs/PATHFINDER_ROADMAP.md (Section A1)
  9. ~/Projects/_agent_forge/docs/TRIAD_RUNTIME_VALIDATION.md
  10. ~/Projects/_agent_forge/policies/hooks.json (current v2 schema)
  11. ~/Projects/_agent_forge/scripts/omni_factory.py (the engine — pay
      attention to lines around 573 _EVENT_ALIASES, 605 codex_hook_payload,
      626 claude_hook_payload, 643 gemini_hook_payload)
  12. ~/Projects/_agent_forge/scripts/validate-triad-runtime.py (especially
      _EXPECTED_HOOK_EVENT_KEY and hook_surface_for)
  13. ~/Projects/_agent_forge/skills/global/telemetry-guardian/SKILL.md
  14. ~/Projects/_agent_forge/skills/global/live-hook-prober/SKILL.md

PHASE 1 — WEB-VERIFY THE 2026 HOST DOCS.
The hook lifecycle is the most volatile API surface across the Triad.
Before you write a single line of schema, fetch the current official
docs and confirm what each host actually supports today.

  Required fetches (use your web tool — do NOT trust the ledger blindly,
  the SOTA may have moved since 2026-04-25):

    a. https://code.claude.com/docs/en/hooks
       Confirm: 26 hook events; 5 handler types (command, http, mcp_tool,
       prompt, agent); async + asyncRewake flag names; permissionDecision
       values (allow/deny/ask/defer); permission_updates schema.

    b. https://geminicli.com/docs/hooks/reference/
       Confirm: PascalCase event names (BeforeTool / AfterTool /
       BeforeAgent / AfterAgent / BeforeModel / AfterModel /
       BeforeToolSelection / SessionStart / SessionEnd / Notification /
       PreCompress). Confirm matcher syntax (regex for tool events,
       exact-string for lifecycle events). Confirm settings.json hook
       block structure.

    c. https://developers.openai.com/codex/changelog and
       https://developers.openai.com/codex/cli/features
       Confirm: hooks are stable as of v0.124.0; can be configured
       inline in config.toml and managed requirements.toml; observe
       MCP tools as well as apply_patch and long-running Bash sessions.
       Confirm any v0.126+ updates to the hook surface.

  If any of the above doc paths 404 or substantially differ from
  Section 2 of the PATHFINDER_LEDGER, **append a new dated section to
  the ledger** capturing the drift before continuing. Do not silently
  reconcile.

PHASE 2 — DESIGN.
Produce a written design before writing code. The design must specify:

  1. policies/hooks.json schema v3:
     - Top-level: { version: 3, shared: [...], claude: [...],
                    codex: [...], gemini: [...] }
     - Each record: { id, event, matcher, handler: { type, ... },
                      targets, timeout_ms, status_message, description,
                      async, async_rewake, permission_updates }
     - The `handler.type` field replaces the implicit `command` shape.
       Type-specific subfields:
         command:  { command: "bash ..." }
         http:     { url, headers: {...}, allowed_env_vars: [...] }
         mcp_tool: { server, tool, input: { ... } }
         prompt:   { prompt, model }
         agent:    { prompt }

  2. Event alias table covering all 34 canonical events x 3 hosts.
     Each cell is the host-native name OR null (skip with [WARN]) OR
     "<merge_into:other_event>" if the host conflates two canonical
     events into one native event.

  3. Renderer translation matrix: how each handler.type maps to each
     host's nearest native handler. Codex currently supports `command`
     only — for prompt/agent handlers on Codex, render as `command`
     calling a wrapper script that the renderer also generates.

  4. Verifier extensions:
     - Every record's resolved handler exists on disk OR is reachable
       as a URL (HEAD request, 2xx or 401/403 = "exists").
     - Every record's `event` is a known canonical id.
     - Every record's `targets` is a subset of {claude, codex, gemini}.
     - Async + async_rewake combinations are valid (async_rewake
       implies async).

  5. Validator extensions:
     - hook_surface_for() now expects the FULL set of registered events,
       not just one. Each record's expected event key must appear in
       the rendered payload.
     - live-hook-prober gains per-handler-type test modes:
         --handler-type http (probe an http handler with a sentinel)
         --handler-type mcp_tool (probe a mcp_tool handler)
         --handler-type prompt (probe a prompt handler)
         --handler-type agent (probe an agent handler)

  6. Migration plan: existing v2 hooks.json must auto-upgrade to v3.
     Renderer accepts both v2 and v3; verifier emits a deprecation
     warning if v2 is still on disk.

  Surface this design as a written artifact in
  docs/SPRINT2_DESIGN.md before any code change. The Founder's
  doctrine is canonical-first: prove the schema is right before
  rendering it.

PHASE 3 — IMPLEMENT.
Edit only these files:

  - policies/hooks.json (schema bump + at least one example of each
    new handler type, even if all but command are dormant)
  - scripts/omni_factory.py (renderers + _EVENT_ALIASES + handler
    aliasing + verify() extension)
  - scripts/validate-triad-runtime.py (hook_surface_for extension +
    live-hook-prober wiring for new handler types)
  - skills/global/live-hook-prober/prober.sh (new --handler-type
    argument + per-type probes)
  - skills/global/live-hook-prober/SKILL.md (document new modes)

DO NOT edit files in <project>/.claude/, <project>/.codex/,
<project>/.gemini/. Those are generated. Re-sync via
`python3 scripts/omni_factory.py sync-{claude,codex,gemini} --project <name>`
after every renderer change.

PHASE 4 — ARCHITECTURAL RULES (non-negotiable).
  1. Canonical-first. Edits go to skills/, teams/, policies/,
     projects.json, global-mcp.json. Generated host surfaces under
     <project>/.claude/, <project>/.codex/, <project>/.gemini/ are
     never hand-edited.
  2. Triad validator is the mandatory final gate. After every
     canonical change:
       python3 scripts/verify-agent-forge.py
       python3 scripts/validate-triad-runtime.py --project jarvis
     Both must EXIT=0 before you claim a sub-step is done.
  3. Append-first lessons. New findings go to
     docs/LESSONS_LEARNED.md. Doctrine in AGENTS.md and
     docs/CONOPS.md does not move silently. Promotion is gated.
  4. Native boot files stay native (CLAUDE.md, AGENTS.md, GEMINI.md
     keep their host-specific names).
  5. The guardian is non-negotiable. No --no-verify, no
     --no-gpg-sign, no force-push to protected branches, no
     `git reset --hard <ref>` against non-current branches. Bypass
     via AGENT_FORGE_GUARDIAN=off only if explicitly required;
     every bypass is logged.
  6. NO --dangerously-skip-permissions, NO
     --dangerously-bypass-approvals-and-sandbox, NO --full-access
     when running ANY live hook test. Those flags bypass the hook
     dispatcher and produce false-positive "allow" signals.
     This is documented in PATHFINDER_LEDGER §4.1 — do not
     re-discover it.
  7. Curated allow-list discipline. Every cross-host semantic
     surface (event names, sandbox markers, permission strings,
     MCP tool prefixes) is checked against an explicit allow-list
     of known-valid native values. NOT a substring match. NOT
     "contains". This is the lesson of the C1 BeforeTool bug.

PHASE 5 — EXIT GATES.
You may not claim Sprint 2 complete until:

  [ ] policies/hooks.json is on schema v3 with at least one example
      of each handler type (command, http, mcp_tool, prompt, agent).
  [ ] _EVENT_ALIASES in omni_factory.py covers all 34 canonical
      events for all three hosts (use null for unsupported).
  [ ] At least one async hook is rendered correctly on Claude.
  [ ] At least one permission_updates entry is rendered correctly on
      Claude.
  [ ] verify-agent-forge.py EXIT=0 with new handler-existence checks.
  [ ] validate-triad-runtime.py --project jarvis EXIT=0 with all
      three hosts hook+ mem+.
  [ ] live-hook-prober --handler-type http succeeds against a local
      sentinel HTTP server.
  [ ] live-hook-prober --handler-type mcp_tool succeeds against a
      local sentinel MCP server (or correctly escalates to
      "no_mcp_test_server_available" if you don't have one).
  [ ] Live Gemini probe (run from a real terminal, NOT from this
      Codex session) for the existing telemetry-guardian on
      pre_tool_use still returns verdict=pass, observed=block.
      Evidence: runtime/validation/hook-probe/<stamp>/gemini/.
  [ ] docs/HANDOFF.md has a new "Sprint 2: Hook Lifecycle V2"
      entry with full sub-changelog.
  [ ] docs/LESSONS_LEARNED.md has at least one new entry capturing
      a finding from this sprint.
  [ ] docs/PATHFINDER_ROADMAP.md A1 status flips to ✅ Shipped
      <date> with evidence paths.
  [ ] One thematic commit using `git commit -F /tmp/<msg-file>`
      (heredoc-in-compound-command is bridge-fragile per
      LESSONS_LEARNED.md — do not use).

PHASE 6 — KNOWN STALL CLASSES (read before any long-running call).
Two distinct failure modes have been observed:

  a. Bridge fragility on bulky compound-bash output. Mixed stdout
     +stderr, large multi-section JSON, or `&&;`-chained commands
     trip an internal encoding/delivery error in agent harnesses.
     Mitigation: narrow tool calls, one question per invocation.
     For long commit messages: `git commit -F /tmp/<msg>` not
     heredoc.

  b. Leftover-subprocess-tree stall when invoking long-running
     CLIs (claude -p, codex exec, gemini -p) THROUGH another
     agent's bash tool. timeout(1) does not always cleanly reap
     the descendant tree. Mitigation: do not invoke long-running
     CLIs through your own bash tool. Run them from a real
     terminal or schedule as Routines.

If you see "[Tool result missing due to internal error]", treat it
as a re-grounding signal: issue a small read-only call (git status,
one ls, one Read) to confirm actual state. Do NOT retry the same
heavy compound command.

PHASE 7 — WHAT SUCCESS LOOKS LIKE.
A senior architect picking up the repo cold sees:
  - policies/hooks.json v3 with worked examples of every handler type.
  - omni_factory.py renders hooks with full event coverage and handler
    aliasing across all three hosts.
  - validate-triad-runtime.py --probe-invocations exercises every
    handler type the host supports.
  - The factory still ships the original telemetry-guardian
    pre-tool-execution-guardian hook unchanged (regression-tested).
  - docs/HANDOFF.md, LESSONS_LEARNED.md, PATHFINDER_ROADMAP.md are
    current.

PHASE 8 — WHAT TO ESCALATE TO THE FOUNDER.
Surface to the Founder (do not silently decide) if:
  - Any of the three host doc fetches in Phase 1 returns 404 or
    contradicts the ledger materially.
  - A handler type cannot be rendered on a host without a wrapper
    script, AND the wrapper script raises a security concern (e.g.,
    needs to bind a network port).
  - permission_updates rendering on Claude requires a Claude Code
    version newer than what this machine has installed.
  - The triad validator FAILs and you cannot diagnose the root cause
    in two passes.
  - You discover a NEW silent-correctness class (hook drift, marker
    drift, alias drift) — append to LESSONS_LEARNED before continuing.

Begin Phase 0 now.
```

---

# Sprint 3 — Cross-Host Auto-Memory Bridge (Architectural Upgrade A2 + Capability B2)

## Copy-paste this entire section into Codex (after Sprint 2 ships)

```
SYSTEM: You are executing Sprint 3 of the Agent Forge Omni-Factory
roadmap. Your role is Principal Systems Engineer. You will implement
Architectural Upgrade A2 (Cross-Host Auto-Memory Bridge) paired with
Capability B2 (memory-bridge skill). Permissions are pre-granted.
Do not prompt the Founder; surface decisions only via structured
artifacts.

PRECONDITION: Sprint 2 (Hook Lifecycle V2) is shipped and triad-green.
This sprint requires SessionStart and Stop / SessionEnd hooks to
render correctly on all three hosts. If Sprint 2 has not shipped,
STOP and surface this to the Founder.

PHASE 0 — REQUIRED READS.
  1. ~/Projects/_agent_forge/README.md
  2. ~/Projects/_agent_forge/AGENTS.md
  3. ~/Projects/_agent_forge/docs/HOST_INTEGRATIONS.md (especially
     §Universal State Layer)
  4. ~/Projects/_agent_forge/docs/HANDOFF.md (read the most recent
     Sprint 2 entry)
  5. ~/Projects/_agent_forge/docs/LESSONS_LEARNED.md
  6. ~/Projects/_agent_forge/docs/PATHFINDER_LEDGER.md (especially
     §2.1 on Claude auto-memory at
     ~/.claude/projects/<project>/memory/MEMORY.md, the 200-line/
     25KB load behavior, and the difference between CLAUDE.md and
     auto-memory)
  7. ~/Projects/_agent_forge/docs/PATHFINDER_ROADMAP.md (Section A2 + B2)
  8. ~/Projects/_agent_forge/policies/memory.json (current v1 schema)
  9. ~/Projects/_agent_forge/skills/global/memory-archivist/SKILL.md
     and archivist.py (this is the writer the bridge will reuse)
  10. ~/Projects/_agent_forge/scripts/omni_factory.py (memory
      renderers around the _memory_sections / render_memory_md /
      sync_memory cluster)

PHASE 1 — WEB-VERIFY.
  a. https://code.claude.com/docs/en/memory
     Confirm: auto-memory storage path
     ~/.claude/projects/<project>/memory/, the MEMORY.md index +
     topic file model, the 200-line / 25KB load threshold, the
     autoMemoryDirectory setting, the autoMemoryEnabled toggle,
     /memory slash command, /memory edit, what survives /compact.

  b. https://geminicli.com/docs/ (search for Memory v2 / Auto Memory)
     Confirm the current state of Gemini's experimental Auto Memory
     in v0.39 or later. If experimental flags are required, capture
     them.

  c. https://developers.openai.com/codex/cli/features
     Confirm: codex resume thread state, AGENTS.md auto-discovery
     refactor (AgentsMdManager), any new persistent-memory primitive.

  Append a new dated PATHFINDER_LEDGER section if any of these have
  drifted materially since 2026-04-25.

PHASE 2 — DESIGN.
Produce docs/SPRINT3_DESIGN.md before writing code:

  1. policies/memory.json v2 (additive):
       bridge: {
         enabled: bool,
         hosts: ["claude", "codex", "gemini"],
         outbound_event: "session_start",   # canonical hook event
         inbound_event:  "session_end",     # canonical hook event
         conflict_policy: "append-first" | "canonical-wins",
         secrets_policy_inheritance: "deny"
       }

  2. <project>/.forge_state/bridge.json shape:
       {
         "version": 1,
         "last_outbound": { "<host>": "<timestamp>" },
         "last_inbound":  { "<host>": "<timestamp>" },
         "last_inbound_diff_hash": { "<host>": "<sha256>" }
       }

  3. memory-bridge skill (skills/global/memory-bridge/):
     - SKILL.md (workflow class, all-host targets)
     - bridge.py with subcommands:
         outbound --project <root> --host <host>
           Read canonical <project>/MEMORY.md.
           Inject relevant entries into the host's native auto-memory
           (Claude: ~/.claude/projects/<project>/memory/MEMORY.md;
           Gemini: <project>/.gemini/memory/ if present;
           Codex: append a structured block to AGENTS.md or to a
                  Codex-readable AGENTS_MEMORY.md sidecar).
         inbound  --project <root> --host <host>
           Read host native auto-memory.
           Diff against bridge.json's last_inbound_diff_hash.
           For new entries, normalize and call
           `memory-archivist append --section <id> --source <host>`.
         status --project <root>
           Print bridge.json + outstanding deltas.

     Idempotent. Append-first. Secrets-deny re-applied.

  4. Hook wiring (requires Sprint 2 schema v3):
       policies/hooks.json:
         { id: "memory-bridge-outbound",
           event: "session_start",
           handler: { type: "command",
             command: "python3 ~/.../memory-bridge/bridge.py outbound \
                       --project $CLAUDE_PROJECT_DIR --host $HOST_TAG" },
           targets: [claude, codex, gemini],
           async: true,
           timeout_ms: 10000 }

         { id: "memory-bridge-inbound",
           event: "session_end",   # SessionEnd on Gemini, Stop on Claude
           handler: { type: "command",
             command: "python3 ~/.../memory-bridge/bridge.py inbound \
                       --project $CLAUDE_PROJECT_DIR --host $HOST_TAG" },
           targets: [claude, codex, gemini],
           async: true,
           timeout_ms: 30000 }

  5. Validator extension:
     - validate-triad-runtime.py gains memory_bridge_for(host, root)
       check: confirms bridge.json exists, has a recent last_outbound
       OR last_inbound for this host, and the hash diff is reasonable.
     - Matrix entry: bridge_pass per host.

PHASE 3 — IMPLEMENT.
Edit only:
  - policies/memory.json (v2 with bridge block)
  - policies/hooks.json (add the two new bridge hook records)
  - skills/global/memory-bridge/ (new directory: SKILL.md + bridge.py)
  - scripts/omni_factory.py (verify() extension if needed)
  - scripts/validate-triad-runtime.py (memory_bridge_for + matrix)
  - skills/global/memory-archivist/archivist.py (only if the bridge
    needs new --source values or new entry-tagging fields)

PHASE 4 — ARCHITECTURAL RULES.
Same as Sprint 2 §4. In addition:

  - Bridge is APPEND-FIRST. Inbound never deletes canonical entries,
    even if the host's native auto-memory was edited or pruned.
  - Bridge is IDEMPOTENT. Running outbound twice in a row produces
    no duplicate entries. Use a content-hash de-dupe.
  - Bridge runs ASYNC. The outbound hook on session_start must not
    block session start by more than 1s of perceptible latency.
    Use async: true (Sprint 2's new flag).
  - Secrets-deny patterns from policies/memory.json are RE-APPLIED
    at the bridge layer. A Claude auto-memory entry containing
    "API_KEY=..." must be rejected, not propagated.
  - Native auto-memory is MACHINE-LOCAL (per Claude docs). The
    bridge does NOT propagate machine-local secrets across hosts.
    If a host's native auto-memory contains entries that the secrets
    filter rejects, log the rejection to bridge.log; do NOT silently
    drop without trace.

PHASE 5 — EXIT GATES.
  [ ] policies/memory.json v2 with bridge block + at least one
      governed project's <project>/.forge_state/bridge.json populated.
  [ ] Two new hook records in policies/hooks.json render correctly
      on all three hosts with async: true.
  [ ] memory-bridge/bridge.py round-trips on jarvis:
      - Manually inject a fact into Claude's auto-memory.
      - Run `bridge.py inbound --project ~/Projects/jarvis --host claude`.
      - Confirm the fact appears in <project>/MEMORY.md under the
        right section, tagged [claude].
      - Run `bridge.py outbound --project ~/Projects/jarvis --host gemini`.
      - Confirm the fact appears in Gemini's native auto-memory location.
  [ ] Secrets-deny test: inject an API key into auto-memory, run
      inbound, confirm it is REJECTED with a bridge.log entry.
  [ ] verify-agent-forge.py EXIT=0.
  [ ] validate-triad-runtime.py --project jarvis EXIT=0 with new
      bridge_pass: true per host.
  [ ] HANDOFF.md, LESSONS_LEARNED.md, PATHFINDER_ROADMAP.md updated.
  [ ] One thematic commit via git commit -F /tmp/<msg>.

PHASE 6 — KNOWN STALL CLASSES.
Same as Sprint 2 §6. New addition:

  c. Auto-memory file write race. If two hosts have active sessions
     against the same project simultaneously, both their session_start
     bridges will write to <project>/MEMORY.md within seconds.
     Use file-locking (flock or atomic rename) in archivist.py to
     prevent corruption.

PHASE 7 — WHAT SUCCESS LOOKS LIKE.
A fact saved into Claude's auto-memory in the morning is visible in
Gemini's auto-memory and in canonical <project>/MEMORY.md by the
afternoon, without manual intervention. Three hosts, one brain.

PHASE 8 — WHAT TO ESCALATE TO THE FOUNDER.
  - If Gemini's experimental Auto Memory is not GA on the Founder's
    Gemini CLI version, surface this and propose a graceful
    degradation (skip Gemini in the bridge until GA).
  - If Codex does not expose any persistent auto-memory analog, propose
    using AGENTS.md as the bridge target on Codex with a clearly
    marked block that the bridge owns and rewrites.
  - If the secrets-deny filter rejects more than 5% of legitimate
    auto-memory content during the round-trip test, the secrets-deny
    patterns are too broad — surface and refine.

Begin Phase 0 now.
```

---

# Sprint 4 — MCP Namespace Prefixing & Routing (Architectural Upgrade A3)

## Copy-paste this entire section into Codex (after Sprint 3 ships)

```
SYSTEM: You are executing Sprint 4 of the Agent Forge Omni-Factory
roadmap. Your role is Principal Systems Engineer. You will implement
Architectural Upgrade A3: canonical-first MCP namespace prefixing and
routing. Permissions are pre-granted. Do not prompt the Founder.

PRECONDITION: Sprint 3 has shipped and triad-green. The bridge
infrastructure is the model for the trust-gated rendering pattern
this sprint extends.

PHASE 0 — REQUIRED READS.
  1. ~/Projects/_agent_forge/README.md
  2. ~/Projects/_agent_forge/AGENTS.md
  3. ~/Projects/_agent_forge/docs/HOST_INTEGRATIONS.md
  4. ~/Projects/_agent_forge/docs/HANDOFF.md
  5. ~/Projects/_agent_forge/docs/LESSONS_LEARNED.md
  6. ~/Projects/_agent_forge/docs/PATHFINDER_LEDGER.md (especially
     §2.5c Advanced MCP routing and §2.2 / §2.3 on each host's MCP
     surface)
  7. ~/Projects/_agent_forge/docs/PATHFINDER_ROADMAP.md (A3)
  8. ~/Projects/_agent_forge/global-mcp.json (currently empty by design)
  9. ~/Projects/_agent_forge/scripts/omni_factory.py (current MCP
     renderer cluster: render_claude_project_mcp, render_gemini_settings
     mcpServers block, Codex config.toml [mcp_servers] rendering)

PHASE 1 — WEB-VERIFY.
  a. https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/128
     Confirm: tool-name collision discussion; recommended prefix
     pattern; whether the protocol itself has added namespace support
     since 2026-04.
  b. https://modelcontextprotocol.io/docs/learn/architecture
     Confirm: current transport list (stdio, streamable_http, sse);
     auth model; resource and root concepts.
  c. https://developers.openai.com/codex/mcp and
     https://developers.openai.com/codex/changelog
     Confirm: trusted-workspace gating for project-scoped MCP servers;
     bearer-token field name in config.toml; any v0.126+ changes.
  d. https://geminicli.com/docs/ (search for MCP)
     Confirm: Gemini's automatic mcp_<server>_<tool> prefixing; whether
     a canonical-prefix override mechanism is documented; settings.json
     mcpServers block schema.
  e. https://code.claude.com/docs/en/mcp
     Confirm: .mcp.json schema; how `mcp__<server>__<tool>` matcher
     pattern resolves in hooks; httpUrl vs command transport fields.

  Append a dated PATHFINDER_LEDGER §5 section capturing whatever has
  drifted since 2026-04-25.

PHASE 2 — DESIGN.
docs/SPRINT4_DESIGN.md before code:

  1. global-mcp.json v2 schema:
       {
         "version": 2,
         "defaults": { startup_timeout_ms, tool_timeout_ms, ... },
         "servers": [
           {
             "id": "github",
             "prefix": "forge.github",        # canonical prefix
             "transport": {
               "type": "stdio" | "streamable_http" | "sse",
               ...transport-specific fields...
             },
             "auth": "none" | "bearer" | "oauth",
             "trust": "local" | "remote-trusted" | "remote-sandboxed",
             "targets": ["claude", "codex", "gemini"],
             "scope": "user" | "project" | "shared",
             "projects": ["jarvis", "homelab"] | "*",
             "tool_filter": ["list_repos", "get_pr"] | null,
             "env_passthrough": ["GITHUB_TOKEN"],
             "env_literal": {},
             "headers": {},
             "description": "..."
           }
         ]
       }

  2. Renderer transformations:
     - Claude .mcp.json: emits prefixed names. Translate
       `<prefix>.<tool>` -> `<prefix>__<tool>` if the host requires
       double-underscore variant in matcher pattern; OR keep the dot
       form if Claude 2026 supports it natively (web-verify in §1).
     - Codex config.toml [mcp_servers.<id>] block: add `prefix = "..."`
       and `tool_filter = [...]` fields. Bearer token via
       `bearer_token_env = "GITHUB_TOKEN"`.
     - Gemini settings.json mcpServers: same prefix authority — Gemini
       auto-prefixes by default, but our canonical declaration
       OVERRIDES so all three hosts emit identical prefixed names.

  3. Trust gating:
     - scope: "project" entries with trust: "remote-trusted" or
       "remote-sandboxed" only emit to projects whose entry in
       projects.json has trusted_workspace: true (new field).
     - scope: "user" entries always emit to user-home configs.
     - scope: "shared" entries emit to project configs across all
       governed projects (subject to per-project opt-out).

  4. Verifier extensions:
     - global-mcp.json parses; every server has prefix + transport.
     - No two servers share the same prefix.
     - Every tool_filter entry is a string.
     - For trusted projects, env_passthrough vars exist in the
       operator's environment OR are explicitly marked optional.
     - Render dry-run: simulate emission, no two tools collide
       across prefixes.

  5. Validator extension:
     - validate-triad-runtime.py gains mcp_surface_for(host, root)
       check: queries each host CLI to enumerate visible MCP tools,
       confirms canonical prefix appears.
     - Matrix entry: mcp_pass per host.

  6. Seed at least ONE real shared MCP server in global-mcp.json.
     Strong candidate: a local stdio "forge.factory" server that
     exposes one tool (e.g., `forge.factory.read_handoff` returning
     the latest HANDOFF.md text). This proves the rendering path
     end-to-end without requiring an external service.

PHASE 3 — IMPLEMENT.
Edit only:
  - global-mcp.json (v2 + at least one seeded server)
  - projects.json (add trusted_workspace field per project)
  - scripts/omni_factory.py (renderer transformations + verify ext)
  - scripts/validate-triad-runtime.py (mcp_surface_for + matrix)
  - skills/global/live-hook-prober/prober.sh (optional: add an
    MCP-tool live-probe mode)

PHASE 4 — ARCHITECTURAL RULES.
Same as Sprints 2 + 3. Plus:

  - NO secrets in global-mcp.json. All credentials flow through
    env_passthrough; per-project .env never enters the canonical
    file.
  - NO project-scoped MCP server emits to a non-trusted workspace.
    The trust gate is mandatory.
  - The first seeded MCP server MUST be local stdio. Remote
    streamable-HTTP servers require explicit operator approval and
    are not in this sprint's scope.

PHASE 5 — EXIT GATES.
  [ ] global-mcp.json v2 with at least one local stdio server.
  [ ] Renderer emits the prefixed tool names on all three hosts;
      no two tools collide.
  [ ] verify-agent-forge.py EXIT=0 with new MCP-prefix-uniqueness check.
  [ ] validate-triad-runtime.py --project jarvis EXIT=0 with new
      mcp_pass: true per host.
  [ ] At least one host CLI can enumerate the seeded MCP server's
      tools via its native MCP listing UI (claude mcp, codex /mcp
      verbose, gemini /memory show or equivalent).
  [ ] live-hook-prober mcp_tool handler probe (from Sprint 2)
      successfully calls the seeded server.
  [ ] HANDOFF, LESSONS_LEARNED, PATHFINDER_ROADMAP updated.
  [ ] One thematic commit via git commit -F /tmp/<msg>.

PHASE 6 — KNOWN STALL CLASSES.
Same as Sprints 2 + 3. Plus:

  d. MCP server startup races. If multiple host CLIs start their
     MCP servers concurrently, stdio binding may race. Stagger
     timeouts across hosts.

PHASE 7 — WHAT SUCCESS LOOKS LIKE.
The Founder runs `claude mcp list`, `codex /mcp verbose`, and
`gemini` (with mcpServers loaded), and all three show
`forge.factory.read_handoff` as a tool with the same prefix. The
namespace-collision class of bug is structurally impossible going
forward; new servers cannot land without a unique prefix.

PHASE 8 — WHAT TO ESCALATE TO THE FOUNDER.
  - If MCP namespace prefixing has been formally added to the
    protocol since 2026-04-25, drop the canonical-prefix override
    in favor of the standard mechanism. Surface this so the schema
    doesn't reinvent.
  - If Gemini's auto-prefix cannot be overridden, accept Gemini's
    `mcp_<server>_<tool>` form and emit Claude/Codex with the same
    shape for cross-host parity. Surface the trade-off.
  - If a Codex change has moved bearer-token config under a
    different key, capture in PATHFINDER_LEDGER §5.

Begin Phase 0 now.
```

---

# Sprints 5 onward — summaries

These sprints will get full Codex prompts when their predecessors ship. Below are the why / what / how briefings so Codex (and the Founder) understand the forward arc.

## Sprint 5 — Audit-Grade Orchestration Log + Cost Warden (A4 + B3)

**Why.** As the factory grows toward `auto-loop` and `crew-director`, an unbounded swarm burns money. Production multi-agent frameworks (AgenticOS, Copilot Swarm, Kimi K2.6) all converge on **proof-of-work + cost tracking + explainable routing + audit-grade logging** at the orchestrator layer. We have nothing here today.

**What.** New `policies/orchestration.json` v1 with `log_destination`, `log_record_shape`, `cost_budget`, `routing_decisions`. New JSONL append-only log at `<project>/.forge_state/orchestration.log`. New `cost-warden` skill (B3) that reads the log and enforces budgets at session, subagent, and per-skill granularity with three actions: `warn`, `prompt`, `halt`. Integration: `subagent-dispatcher` emits records before/after each dispatch; `verification-gate` emits verification status; `branch-finisher` records final cost roll-up.

**How.** The orchestration log writes happen via Sprint 2's hook lifecycle (`SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`). The cost-warden skill is a new workflow skill targeting all three hosts. `validate-triad-runtime.py` gains an `orchestration_log_for(project_root)` check.

**Dependencies.** Sprint 2 (A1 hook lifecycle for `SubagentStart`/`SubagentStop` events).

## Sprint 6 — `forge-shell` Persistent-Bash Primitive (A5 + B4)

**Why.** Stateless tool calls are the wrong substrate for autonomous loops. The Nemotron pattern (cwd tracking via `{cmd};echo __END__;pwd`, allowlist validation, HITL confirm) is what every serious autonomy framework converges on. Without `forge-shell`, Karpathy-style autoresearch is impossible — every iteration starts fresh, no cwd, no env.

**What.** New `forge-shell` skill (B4). Long-lived subprocess wrapping `/bin/bash`. State in `<project>/.forge_state/shell-<session>.json`. Subcommands: `run --session <id> --cmd <...>`, `state`, `reset`, `allowlist add|remove`. Allowlist sourced from new `policies/shell.json`. HITL gate via `AGENT_FORGE_SHELL_AUTO=off` env var. Telemetry-guardian still runs as the deny half (defense in depth). Output capped at 10,000 chars per command (Claude Code parity).

**How.** Python implementation using `subprocess.Popen` with persistent stdin/stdout. Each command wrapped: `{cmd};echo __END__;pwd`. cwd parsed from trailing `pwd`. Audit log per session.

**Dependencies.** Sprint 5 (so shell sessions tag into the orchestration log) + telemetry-guardian (the deny half).

**Unlocks.** Real Claude live-probing (closes the headless-CLI limitation from Sprint 1's lessons). `auto-loop`. `crew-director`.

## Sprint 7 — Continuous Evolution / Anti-Rot (A6 + B5)

**Why.** The factory is the most-famous-for-governance repo on disk and yet **no agent watches the factory itself**. SOTA frameworks have a self-audit substrate. The promotion gates in our lesson ledger today require humans to remember to re-run the validator before promoting.

**What.** New `routine-auditor` skill (B5) with three triggers: local schedule (cron / `/loop` / Claude Routines), remote watchdog (post-GitHub-push), sprint-harvest re-recon. Reads `policies/auditor.json` v1: cadence config, re-recon source list, flag thresholds. Opens local tasks for regressions, GitHub issues for remote drift, `LESSONS_LEARNED.md` candidates for SOTA-divergence findings. **Promotion of doctrine into `AGENTS.md` / `CONOPS.md` becomes gated on a `routine-auditor` clean run within the prior 24 hours.**

**How.** Skill is invokable manually + scheduled. Reads the orchestration log + the latest triad validator artifact + the lesson ledger. Outputs structured reports.

**Dependencies.** Sprint 5 (orchestration log). Plus a git remote (currently blocked; surfaced in `docs/TECH_DEBT.md`).

## Sprint 8 — `router-overseer` Agent-as-a-Tool Dispatcher (B6)

**Why.** The Founder's "ask the factory anything" entry point. Today, picking the right specialist (legal / infra / brand / etc.) is manual. SOTA frameworks ship Conductor-pattern dispatchers that decompose the prompt, route to specialists in parallel, and merge results.

**What.** New `router-overseer` skill (B6). Reads `policies/orchestration.json` `routing_decisions`. Picks the right specialist (or set of specialists in parallel). Records routing rationale into the orchestration log. Merges results. Surfaces a single coherent answer.

**How.** Slash command `/route "<prompt>"` in all three hosts. Calls subagents via the host's native subagent primitive. Cost-warden enforces budgets at dispatch time.

**Dependencies.** Sprints 5 (orchestration log) + 6 (forge-shell for any specialist that needs persistent shell).

## Sprint 9 — `path-scoped-rules` + `host-quirk-translator` (B10 + B11)

**Why.** Operator quality-of-life pass. Path-scoped rules cut context cost dramatically; host-quirk-translator catches the C1-class drift before humans do.

**What.** B10: new skill frontmatter field `paths: ["src/api/**/*.ts"]`. Renderer drops the skill from default-load and converts it to a path-scoped rule on Claude (`.claude/rules/`), an equivalent on Gemini, and an AGENTS.md sidecar block on Codex. B11: meta-skill that runs after `routine-auditor` weekly, detects host-specific surface mismatches (event-name drift, sandbox-marker drift, MCP-prefix drift), and proposes a hotfix to `_EVENT_ALIASES` / `host_sandbox_blocked()` / etc. Generates a PR-equivalent diff against `scripts/omni_factory.py`.

**How.** B10 is a small renderer extension. B11 is a `routine-auditor` follow-on that consumes the SOTA recon ledger and the latest triad validator artifacts, runs structured comparisons, emits diff candidates.

**Dependencies.** Sprint 7 (routine-auditor for B11 trigger).

## Sprint 10+ — Capstone (`auto-loop` + `wiki-compiler` + `crew-director` + `a2a-bridge`)

**Why.** Endgame. These are the headlining capabilities the entire factory exists to support.

**What.** B7 `auto-loop`: Karpathy-autoresearch propose → edit → test → evaluate → ratchet, with interactive wizard at startup. B8 `wiki-compiler`: end reliance on brittle RAG by compiling raw inputs into structured Markdown all agents read directly. B9 `crew-director`: Conductor + swarm fan-out for declared multi-stage operations ("Release a new software version" → spawns auto-loop + wiki-compiler + brand-guardian, merges results). B12 `a2a-bridge`: minimal A2A protocol exposure so external frameworks (Google ADK, LangGraph, CrewAI) can call our skills.

**How.** Each is a new skill that exercises the substrate built in Sprints 1–9. None should start until the dependency stack is solid.

**Dependencies.** All of Sprints 1–9. Specifically: B7 needs B4 (forge-shell) + A4 (orchestration log) + B3 (cost-warden). B8 needs B4 + A2 (memory bridge). B9 needs essentially everything.

---

## Cross-cutting reminders for every sprint

- **Read the file paths Codex is told to read. Verify the web-search sources. Do not assume the SOTA hasn't moved.**
- **Curated allow-list discipline.** Every cross-host semantic check is an allow-list of known-valid native values, never a substring or "contains". This is the lesson the C1 BeforeTool bug paid for — do not re-pay.
- **The triad validator is the only gate that matters.** Files on disk + JSON parsing are necessary; live invocation is the only sufficiency proof.
- **Append-first lessons.** Doctrine never moves silently. Every sprint ends with at least one new `LESSONS_LEARNED.md` entry capturing the durable finding.
- **Use `git commit -F /tmp/<msg>`.** Heredoc-in-compound-command is bridge-fragile in agent harnesses. The workaround takes 5 seconds and saves hours of debugging stuck-result delivery.
- **Run long CLI calls from a real terminal.** Do not invoke `claude -p`, `codex exec`, or `gemini -p` from inside another agent's bash tool. Leftover-subprocess-tree stalls are a known class.
- **No `--dangerously-skip-permissions` (or its host-specific equivalents) when running ANY live hook test.** Those flags bypass the hook dispatcher and produce false-positive "allow" signals. Documented in `docs/PATHFINDER_LEDGER.md` §4.1.

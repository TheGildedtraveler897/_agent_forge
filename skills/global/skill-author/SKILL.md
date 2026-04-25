---
name: skill-author
description: Use when authoring or revising an Agent Forge skill under skills/global/ or skills/projects/. Enforces canonical Omni-Factory frontmatter, agent-agnostic body language, searchable Use-when descriptions, and a verifier dry-run plan before the skill lands.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Skill Author

Purpose: produce new Agent Forge skills that pass `scripts/verify-agent-forge.py` on the first run and deliver identically across Claude, Codex, and Gemini. This is the meta-skill for adding capability to the factory.

## Hard Gates

1. **Canonical frontmatter only.** Every new skill uses the keys listed below. `capability_class` is mandatory and must be one of `workflow`, `expert`, `reference`. `targets` must be an explicit list.
2. **Host-agnostic body.** No Claude-specific, Codex-specific, or Gemini-specific syntax in the body. Say "dispatch a subagent" not "use the Task tool". Say "read the file" not any host's read tool name. The same markdown is delivered to all three hosts unchanged.
3. **Use-when description.** The `description` must start with or prominently contain "Use when…" and include the symptoms, triggers, or tools that should cause an agent to pick this skill. Searchable keywords beat generic summaries.
4. **One-line frontmatter scalars.** The factory frontmatter parser is line-based. Every value must fit on a single line. No folded or literal block scalars. No multi-line arrays.
5. **Verifier dry-run planned.** Before the skill lands, write down the exact `render-registry` + `verify-agent-forge.py` commands that will be run and the expected new `registry.json` entry shape. Landing without this check is unacceptable.

## Frontmatter contract

Required:
- `name`: matches the folder name exactly.
- `description`: one line, starting with or containing "Use when…".
- `capability_class`: `workflow` | `expert` | `reference`.
- `targets`: `["claude", "codex", "gemini"]` unless the skill deliberately excludes a host.

Optional:
- `context_cost`: `light` | `medium` | `heavy`.
- `model_tier`: `any` | `opus` | `sonnet` | `haiku`.
- `claude_command_name` / `gemini_command_name`: override the default command name (default is the folder name).
- `codex_sandbox_mode`: `workspace-write` | `read-only`.
- `delivery_projects`: list of governed projects to receive this skill.
- `requires_mcp_servers`: list of MCP server IDs the skill depends on.

Legacy:
- `hosts`: accepted as an alias for `targets` during migration. Prefer `targets` for new skills.

## Workflow

### Step 1 — Name and locate
- Pick a role-based name (`<role>-<function>`) matching existing style: `brand-guardian`, `legal-counsel`, `infra-architect`.
- Place the skill at `skills/global/<name>/SKILL.md` (portable) or `skills/projects/<project>/<name>/SKILL.md` (project-local).

### Step 2 — Write frontmatter
- Keep values to one line each.
- Fill every required key.
- Add optional keys only if they change factory behavior.

### Step 3 — Write the body
- Open with purpose.
- Declare hard gates up front if the skill is a workflow.
- Provide a workflow section that an agent can follow without reading external files.
- Include a "Non-goals" section that names which downstream or sibling skill handles what this one refuses.
- Avoid host-specific tool names, key bindings, and UI references.

### Step 4 — Plan the verifier run
Before committing, plan the exact commands that will validate this skill and name the expected entry in `registry.json`:
- `python3 scripts/omni_factory.py render-registry`
- `python3 scripts/verify-agent-forge.py`

### Step 5 — Land and verify
Run the planned commands. If the verifier fails, the most common causes are:
- Missing or invalid `capability_class`.
- Folder name not matching `name`.
- Multi-line or malformed frontmatter value.
- `registry.json` not re-rendered before `verify`.

Fix the offending skill and rerun until green.

## Body style rules

- Active voice, imperative where possible.
- Short paragraphs and lists. Agents skim.
- Quote the STOP banners verbatim for workflow skills with gates.
- Cite downstream skills by exact folder name when handing off.
- No emojis unless the user explicitly asked for them in a given project.

## Output

- A new `SKILL.md` file.
- A verifier-run plan written in the authoring PR or handoff.
- A confirmation that `render-registry` and `verify-agent-forge.py` both exit 0.

## Non-goals

- Do not edit `registry.json` by hand. It is generated.
- Do not modify `scripts/omni_factory.py` to accommodate a malformed skill. Fix the skill.
- Do not promote a project-local skill to global until repo-specific assumptions are removed.
- Do not bundle behavior from multiple distinct skills into one file.

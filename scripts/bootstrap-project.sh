#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FORGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="$(cd "${AGENT_FORGE_ROOT}/.." && pwd)"
PROJECT_NAME=""
PROJECT_PATH=""
MODE="new"
WITH_LOCAL_SKILLS="0"
SKIP_CONOPS_PROMPT="0"   # set to 1 to suppress the interactive CONOPS question

# Detect whether stdin is a terminal; fall back to non-interactive if not.
if [[ ! -t 0 ]]; then
  SKIP_CONOPS_PROMPT="1"
fi

usage() {
  cat <<'EOF'
Usage: bootstrap-project.sh --name PROJECT_NAME [--path RELATIVE_PATH] [--existing] [--with-local-skills]
                             [--define | --no-define]

Bootstrap a governed project under ~/Projects with Agent Forge contracts:
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - docs/CONOPS.md
  - docs/HANDOFF.md
  - .claude/CLAUDE.md symlink
  - .claude/agents, .claude/commands, and .claude/skills directories
  - .gemini/agents, .gemini/commands, .gemini/skills, and .gemini/settings.json
  - .agents/skills
  - .codex/agents, .codex/config.toml, and .codex/hooks.json

After scaffold creation the script automatically syncs Claude, Codex, and
Gemini surfaces, then offers an interactive project-definition flow (unless
--no-define is passed or stdin is not a terminal).

Options:
  --name PROJECT_NAME      Project display/name token used for docs
  --path RELATIVE_PATH     Relative path under ~/Projects (defaults to PROJECT_NAME)
  --existing               Standardize an existing project instead of creating a new top-level directory
  --with-local-skills      Create local skill source directories under _agent_forge
  --define                 Always run the interactive project-definition flow (skip the prompt)
  --no-define              Never run the interactive project-definition flow
  -h, --help               Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      PROJECT_NAME="${2:?missing project name}"
      shift 2
      ;;
    --path)
      PROJECT_PATH="${2:?missing project path}"
      shift 2
      ;;
    --existing)
      MODE="existing"
      shift
      ;;
    --with-local-skills)
      WITH_LOCAL_SKILLS="1"
      shift
      ;;
    --define)
      SKIP_CONOPS_PROMPT="0"
      # DEFINE_NOW="1" signals: skip the "do you want to define this?" prompt and go straight in
      DEFINE_NOW="1"
      shift
      ;;
    --no-define)
      SKIP_CONOPS_PROMPT="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

DEFINE_NOW="${DEFINE_NOW:-0}"   # set to 1 by --define to skip the y/n prompt

if [[ -z "${PROJECT_NAME}" ]]; then
  echo "Missing required --name" >&2
  usage
  exit 1
fi

if [[ -z "${PROJECT_PATH}" ]]; then
  PROJECT_PATH="${PROJECT_NAME}"
fi

TARGET_ROOT="${PROJECTS_ROOT}/${PROJECT_PATH}"
ROOT_AGENTS_REL="$(python3 - "${TARGET_ROOT}" "${PROJECTS_ROOT}/AGENTS.md" <<'PY'
from pathlib import Path
import os
import sys

target_root = Path(sys.argv[1])
root_agents = Path(sys.argv[2])
print(os.path.relpath(root_agents, target_root))
PY
)"
ROOT_CLAUDE_REL="$(python3 - "${TARGET_ROOT}/.claude" "${PROJECTS_ROOT}/CLAUDE.md" <<'PY'
from pathlib import Path
import os
import sys

target_dir = Path(sys.argv[1])
root_claude = Path(sys.argv[2])
print(os.path.relpath(root_claude, target_dir))
PY
)"

if [[ "${MODE}" == "new" ]]; then
  mkdir -p "${TARGET_ROOT}"
elif [[ ! -d "${TARGET_ROOT}" ]]; then
  echo "Existing mode requested but target does not exist: ${TARGET_ROOT}" >&2
  exit 1
fi

mkdir -p \
  "${TARGET_ROOT}/docs" \
  "${TARGET_ROOT}/.claude/agents" \
  "${TARGET_ROOT}/.claude/commands" \
  "${TARGET_ROOT}/.claude/skills" \
  "${TARGET_ROOT}/.gemini/agents" \
  "${TARGET_ROOT}/.gemini/commands" \
  "${TARGET_ROOT}/.gemini/skills" \
  "${TARGET_ROOT}/.agents/skills" \
  "${TARGET_ROOT}/.codex/agents"

cat > "${TARGET_ROOT}/AGENTS.md" <<EOF
# ${PROJECT_NAME} Agent Contract

Read the workspace root \`AGENTS.md\` first: \`${ROOT_AGENTS_REL}\`.

## Project Purpose

TODO: describe what ${PROJECT_NAME} is for, who it serves, and where it fits in the wider system.

## Read Order

1. [\`docs/CONOPS.md\`](${TARGET_ROOT}/docs/CONOPS.md)
2. [\`docs/HANDOFF.md\`](${TARGET_ROOT}/docs/HANDOFF.md)
3. Add any project-specific source-of-truth docs here as the project matures

## Working Rules

- Treat \`docs/CONOPS.md\` as durable architecture truth.
- Treat \`docs/HANDOFF.md\` as the live restart point.
- Keep \`CLAUDE.md\` thin and Claude-specific.
- Keep shared agent workflow in \`AGENTS.md\` and the root Agent Forge contracts.

## Update Rules

- Update \`docs/HANDOFF.md\` after meaningful sessions.
- Update \`docs/CONOPS.md\` when architecture or durable operating assumptions change.
- Update this file only when ${PROJECT_NAME}-specific workflow changes.
EOF

cat > "${TARGET_ROOT}/CLAUDE.md" <<EOF
# ${PROJECT_NAME} Claude Adapter

Claude: use [\`AGENTS.md\`](${TARGET_ROOT}/AGENTS.md) as the shared project contract for this repo.

## Read Order

1. [\`AGENTS.md\`](${TARGET_ROOT}/AGENTS.md)
2. [\`docs/CONOPS.md\`](${TARGET_ROOT}/docs/CONOPS.md)
3. [\`docs/HANDOFF.md\`](${TARGET_ROOT}/docs/HANDOFF.md)

## Claude-Specific Notes

- Keep this file thin.
- Put shared workflow changes in \`AGENTS.md\`, not here.
- Add project-local Claude subagents or commands under \`.claude/\` only when the project genuinely needs them.
- Rich Claude skill delivery in \`.claude/skills/\` is governed from canonical \`SKILL.md\` metadata in \`_agent_forge/skills/\`.
EOF

cat > "${TARGET_ROOT}/GEMINI.md" <<EOF
<!-- Managed by Agent Forge bootstrap. The sync script will replace this stub. -->

# ${PROJECT_NAME} Gemini Context

@${ROOT_AGENTS_REL}
@AGENTS.md
@docs/CONOPS.md
@docs/HANDOFF.md
EOF

cat > "${TARGET_ROOT}/docs/CONOPS.md" <<EOF
# ${PROJECT_NAME} CONOPS
# Last updated: $(date +%F)

## Mission

TODO: describe the project mission, audience, and system role.

## Current State

- Governance scaffold bootstrapped from Agent Forge
- Durable architecture description still needs to be filled in
- Omni-factory host surfaces scaffolded for Claude, Codex, and Gemini

## Architecture

TODO: describe the major components, data flow, and source-of-truth docs.

## Pending Tasks

- [ ] Fill in mission and architecture
- [ ] Add project-specific read-order references to \`AGENTS.md\`
- [ ] Decide whether project-local skills are needed
EOF

cat > "${TARGET_ROOT}/docs/HANDOFF.md" <<EOF
# ${PROJECT_NAME} Handoff
Last updated: $(date +%F)

## Current State

- Governance scaffold bootstrapped from Agent Forge
- No meaningful session history captured yet

## Next Clean Restart Point

1. Fill in \`docs/CONOPS.md\`
2. Confirm project purpose and working boundaries
3. Add local skills only if the project truly needs project-specific expert or utility behavior
EOF

ln -sfn "${ROOT_CLAUDE_REL}" "${TARGET_ROOT}/.claude/CLAUDE.md"

if [[ "${WITH_LOCAL_SKILLS}" == "1" ]]; then
  mkdir -p "${AGENT_FORGE_ROOT}/skills/projects/${PROJECT_NAME}"
fi

echo "Bootstrapped project at ${TARGET_ROOT}"
echo

# ── Auto-sync generated host surfaces ─────────────────────────────────────────

echo "── Syncing Claude, Codex, and Gemini surfaces ───────────────────────────────"

SYNC_CLAUDE_OK=0
SYNC_CODEX_OK=0
SYNC_GEMINI_OK=0

if "${AGENT_FORGE_ROOT}/scripts/sync-claude-adapters.sh" --project "${PROJECT_PATH}"; then
  SYNC_CLAUDE_OK=1
fi

CODEX_SYNC_ARGS=("--project" "${PROJECT_PATH}")

if "${AGENT_FORGE_ROOT}/scripts/sync-codex-skills.sh" "${CODEX_SYNC_ARGS[@]+"${CODEX_SYNC_ARGS[@]}"}"; then
  SYNC_CODEX_OK=1
fi

if "${AGENT_FORGE_ROOT}/scripts/sync-gemini-adapters.sh" --project "${PROJECT_PATH}"; then
  SYNC_GEMINI_OK=1
fi

if [[ "${SYNC_CLAUDE_OK}" -eq 1 && "${SYNC_CODEX_OK}" -eq 1 && "${SYNC_GEMINI_OK}" -eq 1 ]]; then
  echo "  Host surfaces synced."
else
  [[ "${SYNC_CLAUDE_OK}" -eq 0 ]] && echo "  Warning: Claude adapter sync failed — run manually:"
  [[ "${SYNC_CLAUDE_OK}" -eq 0 ]] && echo "    ${AGENT_FORGE_ROOT}/scripts/sync-claude-adapters.sh --project ${PROJECT_PATH}"
  [[ "${SYNC_CODEX_OK}"  -eq 0 ]] && echo "  Warning: Codex sync failed — run manually:"
  [[ "${SYNC_CODEX_OK}"  -eq 0 ]] && echo "    ${AGENT_FORGE_ROOT}/scripts/sync-codex-skills.sh --project ${PROJECT_PATH}"
  [[ "${SYNC_GEMINI_OK}" -eq 0 ]] && echo "  Warning: Gemini sync failed — run manually:"
  [[ "${SYNC_GEMINI_OK}" -eq 0 ]] && echo "    ${AGENT_FORGE_ROOT}/scripts/sync-gemini-adapters.sh --project ${PROJECT_PATH}"
fi

echo

# ── Interactive project-definition flow ───────────────────────────────────────

define_project_interactively() {
  echo "── Define this project ──────────────────────────────────────────────────────"
  echo "Answer each prompt (press Enter to leave as a placeholder):"
  echo

  local mission audience deliverable constraints

  read -r -p "Project mission (1-2 sentences — what is this for?):  " mission       || mission=""
  read -r -p "Primary audience or users:                              " audience     || audience=""
  read -r -p "Primary deliverable or system role:                     " deliverable  || deliverable=""
  read -r -p "Key constraints or notable boundaries:                  " constraints  || constraints=""

  mission="${mission:-TODO: describe the project mission and audience.}"
  audience="${audience:-TODO: describe who this project serves.}"
  deliverable="${deliverable:-TODO: describe the primary deliverable or system role.}"
  constraints="${constraints:-TODO: describe key constraints, boundaries, or assumptions.}"

  cat > "${TARGET_ROOT}/docs/CONOPS.md" <<EOF
# ${PROJECT_NAME} CONOPS
Last updated: $(date +%F)

## Mission

${mission}

## Audience

${audience}

## Primary Deliverable

${deliverable}

## Constraints

${constraints}

## Current State

- Governance scaffold bootstrapped from Agent Forge
- First-pass definition captured at bootstrap time

## Architecture

TODO: describe the major components, data flow, and source-of-truth docs.

## Pending Tasks

- [ ] Flesh out architecture section when implementation begins
- [ ] Add project-specific read-order references to \`AGENTS.md\`
- [ ] Decide whether project-local skills are needed
EOF

  echo "  CONOPS.md written with your inputs."
}

if [[ "${SKIP_CONOPS_PROMPT}" != "1" ]]; then
  if [[ "${DEFINE_NOW}" == "1" ]]; then
    define_project_interactively
  else
    echo "── Optional: define this project now ────────────────────────────────────────"
    read -r -p "Would you like to fill in the project definition now? [y/n]: " _ans || _ans="n"
    case "${_ans}" in
      y|Y|yes|YES)
        echo
        define_project_interactively
        ;;
      *)
        echo "  Skipped. Edit docs/CONOPS.md whenever you are ready."
        ;;
    esac
    echo
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo "── ${PROJECT_NAME} is ready ─────────────────────────────────────────────────"
echo "  Location:  ${TARGET_ROOT}"
echo "  Next:      Fill in docs/CONOPS.md if you skipped the definition step."
echo "             Add project-specific references to AGENTS.md as the project grows."
echo "             Run scripts/verify-agent-forge.py after wiring any local skills."

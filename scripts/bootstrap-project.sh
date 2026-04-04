#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FORGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="$(cd "${AGENT_FORGE_ROOT}/.." && pwd)"
PROJECT_NAME=""
PROJECT_PATH=""
MODE="new"
WITH_LOCAL_SKILLS="0"

usage() {
  cat <<'EOF'
Usage: bootstrap-project.sh --name PROJECT_NAME [--path RELATIVE_PATH] [--existing] [--with-local-skills]

Bootstrap a governed project under ~/Projects with Agent Forge contracts:
  - AGENTS.md
  - CLAUDE.md
  - docs/CONOPS.md
  - docs/HANDOFF.md
  - .claude/CLAUDE.md symlink
  - .claude/agents and .claude/commands directories

Options:
  --name PROJECT_NAME      Project display/name token used for docs
  --path RELATIVE_PATH     Relative path under ~/Projects (defaults to PROJECT_NAME)
  --existing               Standardize an existing project instead of creating a new top-level directory
  --with-local-skills      Create local skill source and Claude adapter directories under _agent_forge
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

if [[ -z "${PROJECT_NAME}" ]]; then
  echo "Missing required --name" >&2
  usage
  exit 1
fi

if [[ -z "${PROJECT_PATH}" ]]; then
  PROJECT_PATH="${PROJECT_NAME}"
fi

TARGET_ROOT="${PROJECTS_ROOT}/${PROJECT_PATH}"

if [[ "${MODE}" == "new" ]]; then
  mkdir -p "${TARGET_ROOT}"
elif [[ ! -d "${TARGET_ROOT}" ]]; then
  echo "Existing mode requested but target does not exist: ${TARGET_ROOT}" >&2
  exit 1
fi

mkdir -p "${TARGET_ROOT}/docs" "${TARGET_ROOT}/.claude" "${TARGET_ROOT}/.claude/agents" "${TARGET_ROOT}/.claude/commands"

cat > "${TARGET_ROOT}/AGENTS.md" <<EOF
# ${PROJECT_NAME} Agent Contract

Read [\`/home/pheonixprotocol/Projects/AGENTS.md\`](/home/pheonixprotocol/Projects/AGENTS.md) first.

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
EOF

cat > "${TARGET_ROOT}/docs/CONOPS.md" <<EOF
# ${PROJECT_NAME} CONOPS
# Last updated: $(date +%F)

## Mission

TODO: describe the project mission, audience, and system role.

## Current State

- Governance scaffold bootstrapped from Agent Forge
- Durable architecture description still needs to be filled in

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

ln -sfn /home/pheonixprotocol/Projects/CLAUDE.md "${TARGET_ROOT}/.claude/CLAUDE.md"

if [[ "${WITH_LOCAL_SKILLS}" == "1" ]]; then
  mkdir -p "${AGENT_FORGE_ROOT}/skills/projects/${PROJECT_NAME}"
  mkdir -p "${AGENT_FORGE_ROOT}/claude/projects/${PROJECT_NAME}/agents"
  mkdir -p "${AGENT_FORGE_ROOT}/claude/projects/${PROJECT_NAME}/commands"
fi

echo "Bootstrapped project at ${TARGET_ROOT}"
echo "Next steps:"
echo "  1. Fill in docs/CONOPS.md"
echo "  2. Add project-specific read-order references to AGENTS.md"
echo "  3. Run _agent_forge/scripts/verify-agent-forge.py after wiring any local skills"

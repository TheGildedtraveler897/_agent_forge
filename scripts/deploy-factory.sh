#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FACTORY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGE_ROOT="$(cd "${SOURCE_FACTORY_ROOT}/.." && pwd)"
PROJECTS_ROOT="${HOME}/Projects"
CLAUDE_HOME="${HOME}/.claude"
CODEX_HOME="${HOME}/.codex"
GEMINI_HOME="${HOME}/.gemini"
OVERWRITE_ROOT_DOCS="0"
REPLACE_FACTORY="0"

usage() {
  cat <<'EOF'
Usage: deploy-factory.sh [--projects-root DIR] [--claude-home DIR] [--codex-home DIR] [--gemini-home DIR] [--overwrite-root-docs] [--replace-factory]

Deploy an exported Agent Forge suitcase onto a fresh machine or test root.

Options:
  --projects-root DIR    Target Projects root (default: ~/Projects)
  --claude-home DIR      Target Claude home (default: ~/.claude)
  --codex-home DIR       Target Codex home (default: ~/.codex)
  --gemini-home DIR      Target Gemini home (default: ~/.gemini)
  --overwrite-root-docs  Replace shared root docs if they already exist
  --replace-factory      Replace an existing target _agent_forge snapshot
  -h, --help             Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --projects-root)
      PROJECTS_ROOT="${2:?missing projects root}"
      shift 2
      ;;
    --claude-home)
      CLAUDE_HOME="${2:?missing claude home}"
      shift 2
      ;;
    --codex-home)
      CODEX_HOME="${2:?missing codex home}"
      shift 2
      ;;
    --gemini-home)
      GEMINI_HOME="${2:?missing gemini home}"
      shift 2
      ;;
    --overwrite-root-docs)
      OVERWRITE_ROOT_DOCS="1"
      shift
      ;;
    --replace-factory)
      REPLACE_FACTORY="1"
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

TARGET_FACTORY_ROOT="${PROJECTS_ROOT}/_agent_forge"

if [[ -d "${PACKAGE_ROOT}/shared-root" ]]; then
  SHARED_ROOT_SOURCE="${PACKAGE_ROOT}/shared-root"
elif [[ -f "${PACKAGE_ROOT}/AGENTS.md" && -f "${PACKAGE_ROOT}/CLAUDE.md" ]]; then
  SHARED_ROOT_SOURCE="${PACKAGE_ROOT}"
else
  echo "Could not locate shared root doctrine files next to the factory payload." >&2
  exit 1
fi

copy_file_if_needed() {
  local source_path="$1"
  local target_path="$2"

  mkdir -p "$(dirname "${target_path}")"
  if [[ -e "${target_path}" && "${OVERWRITE_ROOT_DOCS}" != "1" ]]; then
    return 0
  fi
  cp "${source_path}" "${target_path}"
}

mkdir -p "${PROJECTS_ROOT}"

if [[ -e "${TARGET_FACTORY_ROOT}" ]]; then
  if [[ "${REPLACE_FACTORY}" != "1" ]]; then
    echo "Target factory already exists: ${TARGET_FACTORY_ROOT}" >&2
    echo "Re-run with --replace-factory to refresh from this suitcase snapshot." >&2
    exit 1
  fi
  rm -rf "${TARGET_FACTORY_ROOT}"
fi

tar -C "${SOURCE_FACTORY_ROOT}/.." \
  --exclude='./_agent_forge/.git' \
  --exclude='./_agent_forge/exports' \
  -cf - _agent_forge | tar -C "${PROJECTS_ROOT}" -xf -

copy_file_if_needed "${SHARED_ROOT_SOURCE}/AGENTS.md" "${PROJECTS_ROOT}/AGENTS.md"
copy_file_if_needed "${SHARED_ROOT_SOURCE}/CLAUDE.md" "${PROJECTS_ROOT}/CLAUDE.md"
copy_file_if_needed "${SHARED_ROOT_SOURCE}/docs/gotchas.md" "${PROJECTS_ROOT}/docs/gotchas.md"
copy_file_if_needed "${SHARED_ROOT_SOURCE}/docs/port_ledger.md" "${PROJECTS_ROOT}/docs/port_ledger.md"

"${TARGET_FACTORY_ROOT}/scripts/sync-claude-adapters.sh" \
  --projects-root "${PROJECTS_ROOT}" \
  --claude-home "${CLAUDE_HOME}"

"${TARGET_FACTORY_ROOT}/scripts/sync-codex-skills.sh" \
  --codex-home "${CODEX_HOME}" \
  --target "${HOME}/.agents/skills"

"${TARGET_FACTORY_ROOT}/scripts/sync-gemini-adapters.sh" \
  --gemini-home "${GEMINI_HOME}"

echo "Agent Forge deployed to ${TARGET_FACTORY_ROOT}"
echo "Claude home: ${CLAUDE_HOME}"
echo "Codex home: ${CODEX_HOME}"
echo "Gemini home: ${GEMINI_HOME}"
echo "Next steps:"
echo "  1. cd ${TARGET_FACTORY_ROOT}"
echo "  2. ./scripts/bootstrap-workstation.sh"
echo "  3. Complete authentication for the selected hosted CLIs"
echo "  4. ./scripts/bootstrap-project.sh --name <your-project>"
echo "     (bootstrap-project.sh auto-syncs Claude, Codex, and Gemini surfaces)"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"
GLOBAL_AGENTS_DIR="${ROOT_DIR}/claude/global/agents"
GLOBAL_COMMANDS_DIR="${ROOT_DIR}/claude/global/commands"
CLAUDE_HOME="${HOME}/.claude"
TARGET_USER_AGENTS="${CLAUDE_HOME}/agents"
TARGET_USER_COMMANDS="${CLAUDE_HOME}/commands"
REGISTRY_PATH="${ROOT_DIR}/registry.json"
PROJECT_NAME=""

usage() {
  cat <<'EOF'
Usage: sync-claude-adapters.sh [--project NAME] [--projects-root DIR] [--claude-home DIR]

Sync canonical Claude-native adapters from Agent Forge into Claude's user-level
and, optionally, project-level locations using symlinks.

Syncs three delivery targets:
  ~/.claude/agents/      <- claude/global/agents/*.md
  ~/.claude/commands/    <- claude/global/commands/*.md
  <project>/.claude/skills/ <- only registry-declared Claude skills for that project

Options:
  --project NAME      Also sync project-local adapters for the named project
  --projects-root DIR Override the target Projects root
  --claude-home DIR   Override the Claude home directory (default: ~/.claude)
  -h, --help          Show this message
EOF
}

project_skill_links() {
  python3 - "${REGISTRY_PATH}" "${ROOT_DIR}" "${PROJECT_NAME}" <<'PY'
import json
from pathlib import Path
import sys

registry_path = Path(sys.argv[1])
root = Path(sys.argv[2])
project = sys.argv[3]

with registry_path.open() as fh:
    registry = json.load(fh)

for entry in registry.get("skills", []):
    skill_delivery = entry.get("claude_skill")
    if not skill_delivery:
        continue
    if project not in skill_delivery.get("projects", []):
        continue
    skill_dir = root / Path(entry["canonical_skill"]).parent
    print(f"{entry['name']}\t{skill_dir}")
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_NAME="${2:?missing project name}"
      shift 2
      ;;
    --projects-root)
      PROJECTS_ROOT="${2:?missing projects root}"
      shift 2
      ;;
    --claude-home)
      CLAUDE_HOME="${2:?missing claude home}"
      TARGET_USER_AGENTS="${CLAUDE_HOME}/agents"
      TARGET_USER_COMMANDS="${CLAUDE_HOME}/commands"
      shift 2
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

mkdir -p "${TARGET_USER_AGENTS}" "${TARGET_USER_COMMANDS}"

link_dir_contents() {
  local source_dir="$1"
  local target_dir="$2"
  local entry_name

  [[ -d "${source_dir}" ]] || return 0

  for source_path in "${source_dir}"/*; do
    [[ -e "${source_path}" ]] || continue
    entry_name="$(basename "${source_path}")"
    if [[ -e "${target_dir}/${entry_name}" && ! -L "${target_dir}/${entry_name}" ]]; then
      echo "Refusing to replace non-symlink target: ${target_dir}/${entry_name}" >&2
      exit 1
    fi
    ln -sfn "${source_path}" "${target_dir}/${entry_name}"
  done
}

# Sync global agents and commands to user-level ~/.claude/
link_dir_contents "${GLOBAL_AGENTS_DIR}" "${TARGET_USER_AGENTS}"
link_dir_contents "${GLOBAL_COMMANDS_DIR}" "${TARGET_USER_COMMANDS}"

if [[ -n "${PROJECT_NAME}" ]]; then
  PROJECT_ROOT="${PROJECTS_ROOT}/${PROJECT_NAME}"
  PROJECT_AGENTS_SOURCE="${ROOT_DIR}/claude/projects/${PROJECT_NAME}/agents"
  PROJECT_COMMANDS_SOURCE="${ROOT_DIR}/claude/projects/${PROJECT_NAME}/commands"
  PROJECT_AGENTS_TARGET="${PROJECT_ROOT}/.claude/agents"
  PROJECT_COMMANDS_TARGET="${PROJECT_ROOT}/.claude/commands"
  PROJECT_SKILLS_TARGET="${PROJECT_ROOT}/.claude/skills"

  if [[ ! -d "${PROJECT_ROOT}" ]]; then
    echo "Project root not found: ${PROJECT_ROOT}" >&2
    exit 1
  fi

  mkdir -p "${PROJECT_ROOT}/.claude" "${PROJECT_AGENTS_TARGET}" "${PROJECT_COMMANDS_TARGET}" "${PROJECT_SKILLS_TARGET}"
  link_dir_contents "${PROJECT_AGENTS_SOURCE}" "${PROJECT_AGENTS_TARGET}"
  link_dir_contents "${PROJECT_COMMANDS_SOURCE}" "${PROJECT_COMMANDS_TARGET}"

  declare -A desired_skills=()

  while IFS=$'\t' read -r skill_name skill_dir; do
    [[ -n "${skill_name}" ]] || continue
    desired_skills["${skill_name}"]=1
    if [[ -e "${PROJECT_SKILLS_TARGET}/${skill_name}" && ! -L "${PROJECT_SKILLS_TARGET}/${skill_name}" ]]; then
      echo "Refusing to replace non-symlink target: ${PROJECT_SKILLS_TARGET}/${skill_name}" >&2
      exit 1
    fi
    ln -sfn "${skill_dir}" "${PROJECT_SKILLS_TARGET}/${skill_name}"
  done < <(project_skill_links)

  for existing_path in "${PROJECT_SKILLS_TARGET}"/*; do
    [[ -e "${existing_path}" ]] || continue
    entry_name="$(basename "${existing_path}")"
    if [[ -z "${desired_skills[${entry_name}]+x}" ]]; then
      if [[ -L "${existing_path}" ]]; then
        rm -f "${existing_path}"
      else
        echo "Refusing to remove non-symlink target: ${existing_path}" >&2
        exit 1
      fi
    fi
  done
fi

echo "Claude adapter sync complete"

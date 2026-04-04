#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"
GLOBAL_AGENTS_DIR="${ROOT_DIR}/claude/global/agents"
GLOBAL_COMMANDS_DIR="${ROOT_DIR}/claude/global/commands"
GLOBAL_SKILLS_DIR="${ROOT_DIR}/skills/global"
TARGET_USER_AGENTS="${HOME}/.claude/agents"
TARGET_USER_COMMANDS="${HOME}/.claude/commands"
PROJECT_NAME=""

usage() {
  cat <<'EOF'
Usage: sync-claude-adapters.sh [--project NAME]

Sync canonical Claude-native adapters from Agent Forge into Claude's user-level
and, optionally, project-level locations using symlinks.

Syncs three delivery targets:
  ~/.claude/agents/      <- claude/global/agents/*.md
  ~/.claude/commands/    <- claude/global/commands/*.md
  <project>/.claude/skills/ <- skills/global/* and skills/projects/<project>/*

Options:
  --project NAME   Also sync project-local adapters for the named project
  -h, --help       Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_NAME="${2:?missing project name}"
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

  # Sync global skills into project .claude/skills/
  for skill_dir in "${GLOBAL_SKILLS_DIR}"/*/; do
    [[ -d "${skill_dir}" ]] || continue
    skill_name="$(basename "${skill_dir}")"
    if [[ -e "${PROJECT_SKILLS_TARGET}/${skill_name}" && ! -L "${PROJECT_SKILLS_TARGET}/${skill_name}" ]]; then
      echo "Refusing to replace non-symlink target: ${PROJECT_SKILLS_TARGET}/${skill_name}" >&2
      exit 1
    fi
    ln -sfn "${skill_dir}" "${PROJECT_SKILLS_TARGET}/${skill_name}"
  done

  # Sync project-local skills into project .claude/skills/
  PROJECT_SKILLS_SOURCE="${ROOT_DIR}/skills/projects/${PROJECT_NAME}"
  if [[ -d "${PROJECT_SKILLS_SOURCE}" ]]; then
    for skill_dir in "${PROJECT_SKILLS_SOURCE}"/*/; do
      [[ -d "${skill_dir}" ]] || continue
      skill_name="$(basename "${skill_dir}")"
      if [[ -e "${PROJECT_SKILLS_TARGET}/${skill_name}" && ! -L "${PROJECT_SKILLS_TARGET}/${skill_name}" ]]; then
        echo "Refusing to replace non-symlink target: ${PROJECT_SKILLS_TARGET}/${skill_name}" >&2
        exit 1
      fi
      ln -sfn "${skill_dir}" "${PROJECT_SKILLS_TARGET}/${skill_name}"
    done
  fi
fi

echo "Claude adapter sync complete"

#!/usr/bin/env bash
set -euo pipefail

# Sync canonical Agent Forge skills into a Codex skills directory without making
# the tool-home copy the source of truth.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GLOBAL_DIR="${ROOT_DIR}/skills/global"
PROJECTS_DIR="${ROOT_DIR}/skills/projects"
TARGET_DIR="${HOME}/.codex/skills"
PROJECT_NAME=""

usage() {
  cat <<'EOF'
Usage: sync-codex-skills.sh [--target DIR] [--project NAME]

Sync global skills and, optionally, project-local skills into a Codex skills directory
using symlinks to the canonical copies stored under ~/Projects/_agent_forge.

Options:
  --target DIR    Override the Codex skills directory
  --project NAME  Also sync skills from skills/projects/NAME
  -h, --help      Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:?missing target dir}"
      shift 2
      ;;
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

mkdir -p "${TARGET_DIR}"

link_skill_dir() {
  local source_dir="$1"
  local skill_name

  for skill_path in "${source_dir}"/*; do
    [[ -d "${skill_path}" ]] || continue
    skill_name="$(basename "${skill_path}")"
    if [[ -e "${TARGET_DIR}/${skill_name}" && ! -L "${TARGET_DIR}/${skill_name}" ]]; then
      echo "Refusing to replace non-symlink target: ${TARGET_DIR}/${skill_name}" >&2
      exit 1
    fi
    ln -sfn "${skill_path}" "${TARGET_DIR}/${skill_name}"
  done
}

link_skill_dir "${GLOBAL_DIR}"

if [[ -n "${PROJECT_NAME}" ]]; then
  PROJECT_DIR="${PROJECTS_DIR}/${PROJECT_NAME}"
  if [[ ! -d "${PROJECT_DIR}" ]]; then
    echo "Project skill directory not found: ${PROJECT_DIR}" >&2
    exit 1
  fi
  link_skill_dir "${PROJECT_DIR}"
fi

echo "Codex skill sync complete: ${TARGET_DIR}"

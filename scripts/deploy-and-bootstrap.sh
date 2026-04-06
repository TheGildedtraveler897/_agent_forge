#!/usr/bin/env bash
# deploy-and-bootstrap.sh — one-shot operator wrapper for Agent Forge setup.
#
# Runs deploy-factory.sh (no packages installed) then asks whether to run
# bootstrap-workstation.sh (packages + auth).  Nothing is installed silently.
#
# Interactive by default.  Use --bootstrap / --no-bootstrap to skip the prompt.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FACTORY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="${HOME}/Projects"
RUN_BOOTSTRAP="unset"   # "unset" = ask; "yes" = run; "no" = skip

usage() {
  cat <<'EOF'
Usage: deploy-and-bootstrap.sh [options]

One-shot wrapper that deploys the Agent Forge factory onto this machine and
then optionally runs workstation bootstrap.

  Step 1 — deploy-factory.sh    Copy _agent_forge into ~/Projects and sync
                                 Claude/Codex adapters. No packages installed.

  Step 2 — bootstrap-workstation.sh  (you choose whether to run this)
                                 Install development dependencies and selected
                                 hosted coding CLIs. You pick what gets installed.

If --bootstrap or --no-bootstrap is not passed, you are asked interactively.

Options:
  --bootstrap             Run workstation bootstrap without prompting
  --no-bootstrap          Skip workstation bootstrap without prompting
  --projects-root DIR     Target Projects root (default: ~/Projects)
  --claude-home DIR       Target Claude home (default: ~/.claude)
  --codex-home DIR        Target Codex home (default: ~/.codex)
  --overwrite-root-docs   Replace shared root docs if they already exist
  --replace-factory       Replace an existing target _agent_forge snapshot
  -h, --help              Show this message

Example — fully non-interactive fresh-machine setup:
  ./deploy-and-bootstrap.sh --replace-factory --bootstrap
EOF
}

DEPLOY_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bootstrap)
      RUN_BOOTSTRAP="yes"
      shift
      ;;
    --no-bootstrap)
      RUN_BOOTSTRAP="no"
      shift
      ;;
    --projects-root)
      PROJECTS_ROOT="${2:?--projects-root requires a value}"
      DEPLOY_ARGS+=("$1" "$2")
      shift 2
      ;;
    --claude-home|--codex-home)
      DEPLOY_ARGS+=("$1" "${2:?$1 requires a value}")
      shift 2
      ;;
    --overwrite-root-docs|--replace-factory)
      DEPLOY_ARGS+=("$1")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

DEPLOYED_FACTORY="${PROJECTS_ROOT}/_agent_forge"

# ── Banner ────────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           Agent Forge — One-Shot Machine Setup           ║"
echo "║                                                          ║"
echo "║  Step 1: Deploy factory     (no packages installed)      ║"
echo "║  Step 2: Workstation setup  (you choose what to install) ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo

# ── Step 1: Deploy factory ────────────────────────────────────────────────────

echo "── Step 1 of 2: Deploy factory ─────────────────────────────────────────────"
echo "Copies _agent_forge into ${PROJECTS_ROOT} and syncs Claude / Codex adapters."
echo "No packages are installed in this step."
echo

"${FACTORY_ROOT}/scripts/deploy-factory.sh" "${DEPLOY_ARGS[@]+"${DEPLOY_ARGS[@]}"}"

echo
echo "  Deploy complete."
echo

# ── Step 2: Workstation bootstrap (interactive unless flagged) ────────────────

echo "── Step 2 of 2: Workstation bootstrap ──────────────────────────────────────"
echo "Installs development dependencies and selected hosted coding CLIs"
echo "(Claude Code, Codex, Gemini CLI) and guides you through authentication."
echo "You will choose which CLIs to install — nothing is installed without asking."
echo

if [[ "${RUN_BOOTSTRAP}" == "unset" ]]; then
  read -r -p "Run workstation bootstrap now? [y/n]: " _reply
  case "${_reply}" in
    y|Y|yes|YES) RUN_BOOTSTRAP="yes" ;;
    *)           RUN_BOOTSTRAP="no"  ;;
  esac
fi

if [[ "${RUN_BOOTSTRAP}" == "yes" ]]; then
  echo
  "${DEPLOYED_FACTORY}/scripts/bootstrap-workstation.sh"
else
  echo
  echo "  Skipped. When you are ready, run:"
  echo "    cd ${DEPLOYED_FACTORY}"
  echo "    ./scripts/bootstrap-workstation.sh"
fi

# ── Final guidance ────────────────────────────────────────────────────────────

echo
echo "═══════════════════════════════════════════════════════════════════════════"
echo " After completing authentication, bootstrap your first project:"
echo "   cd ${DEPLOYED_FACTORY}"
echo "   ./scripts/bootstrap-project.sh --name <your-project>"
echo "═══════════════════════════════════════════════════════════════════════════"

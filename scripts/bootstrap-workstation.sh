#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"
MACHINE_SETUP_DIR="${ROOT_DIR}/runtime/machine-setup"
TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
MACHINE_SETUP_LOG="${MACHINE_SETUP_DIR}/bootstrap-${TIMESTAMP}.md"
FORCE_NODE_EXTERNAL="0"

usage() {
  cat <<'EOF'
Usage: bootstrap-workstation.sh [--allow-external-node-repo]

Prepare a fresh Debian/Ubuntu or macOS workstation for Agent Forge development.

This script:
  - installs base CLI dependencies
  - installs selected hosted coding CLIs (Claude Code, Codex, Gemini CLI)
  - guides the operator through interactive authentication
  - writes a durable machine setup log under _agent_forge/runtime/machine-setup/

Options:
  --allow-external-node-repo  Pre-approve use of a vetted external Node LTS apt repo
  -h, --help                  Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-external-node-repo)
      FORCE_NODE_EXTERNAL="1"
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

mkdir -p "${MACHINE_SETUP_DIR}"

OS_ID=""
OS_LIKE=""
OS_NAME=""
PACKAGE_MODE=""
INSTALL_CLAUDE="0"
INSTALL_CODEX="0"
INSTALL_GEMINI="0"
NODE_VERSION=""
NODE_MAJOR=0

log() {
  echo "$*"
}

record_section() {
  {
    echo
    echo "$1"
  } >> "${MACHINE_SETUP_LOG}"
}

record_line() {
  echo "$1" >> "${MACHINE_SETUP_LOG}"
}

require_command() {
  local cmd="$1"
  local hint="$2"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}. ${hint}" >&2
    exit 1
  fi
}

yes_no_prompt() {
  local prompt="$1"
  local reply
  while true; do
    read -r -p "${prompt} [y/n]: " reply
    case "${reply}" in
      y|Y|yes|YES) return 0 ;;
      n|N|no|NO) return 1 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

detect_platform() {
  case "$(uname -s)" in
    Linux)
      if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        source /etc/os-release
        OS_ID="${ID:-linux}"
        OS_LIKE="${ID_LIKE:-}"
        OS_NAME="${PRETTY_NAME:-${ID:-Linux}}"
      else
        OS_ID="linux"
        OS_NAME="Linux"
      fi

      if [[ "${OS_ID}" == "debian" || "${OS_ID}" == "ubuntu" || "${OS_LIKE}" == *debian* ]]; then
        PACKAGE_MODE="apt"
      else
        echo "Unsupported Linux distribution for automated bootstrap: ${OS_NAME}" >&2
        echo "First implementation supports Debian/Ubuntu only. See docs/WORKSTATION_BOOTSTRAP.md." >&2
        exit 1
      fi
      ;;
    Darwin)
      OS_ID="macos"
      OS_NAME="macOS"
      PACKAGE_MODE="macports"
      ;;
    *)
      echo "Unsupported operating system: $(uname -s)" >&2
      exit 1
      ;;
  esac
}

ensure_sudo() {
  if [[ "${PACKAGE_MODE}" == "apt" || "${PACKAGE_MODE}" == "macports" ]]; then
    require_command "sudo" "Install sudo or run from an admin-capable shell."
  fi
}

# MacPorts manages npm at /opt/local/lib/node_modules (root-owned).
# All other MacPorts installs already use sudo; npm global installs must too.
# On apt/nvm setups the prefix is user-writable, so sudo is omitted.
npm_global_install() {
  if [[ "${PACKAGE_MODE}" == "macports" ]]; then
    sudo npm install -g "$@"
  else
    npm install -g "$@"
  fi
}

apt_install() {
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

ensure_base_dependencies_apt() {
  apt_install git curl jq ripgrep zip unzip tar ca-certificates build-essential
}

ensure_node_apt() {
  if command -v node >/dev/null 2>&1; then
    NODE_VERSION="$(node --version)"
    NODE_MAJOR="$(printf '%s' "${NODE_VERSION#v}" | cut -d. -f1)"
    if [[ "${NODE_MAJOR}" -ge 20 ]]; then
      return 0
    fi
  fi

  apt_install nodejs npm

  if command -v node >/dev/null 2>&1; then
    NODE_VERSION="$(node --version)"
    NODE_MAJOR="$(printf '%s' "${NODE_VERSION#v}" | cut -d. -f1)"
  else
    NODE_MAJOR=0
  fi

  if [[ "${NODE_MAJOR}" -ge 20 ]]; then
    return 0
  fi

  cat <<'EOF'
Node.js 20+ is required for Gemini CLI and recommended for the other hosted CLIs.
Your distro packages do not provide a new enough Node version.

Security tradeoff:
- Native apt packages are preferred and lowest-trust-surface.
- A vetted external Node LTS apt source keeps installation under apt signature/update workflows.
- This is safer than ad hoc per-user package managers, but it still expands trust beyond the base distro.
EOF

  if [[ "${FORCE_NODE_EXTERNAL}" != "1" ]]; then
    if ! yes_no_prompt "Add the vetted external Node LTS apt source now?"; then
      echo "Cannot continue without Node 20+. Re-run later or install Node manually." >&2
      exit 1
    fi
  fi

  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  apt_install nodejs
  NODE_VERSION="$(node --version)"
  NODE_MAJOR="$(printf '%s' "${NODE_VERSION#v}" | cut -d. -f1)"
  if [[ "${NODE_MAJOR}" -lt 20 ]]; then
    echo "Node 20+ still unavailable after adding external Node LTS source." >&2
    exit 1
  fi
}

ensure_base_dependencies_macports() {
  if ! command -v port >/dev/null 2>&1; then
    cat <<'EOF' >&2
MacPorts is required (the supported macOS package manager for this workstation
bootstrap path). Homebrew is intentionally not supported.

Install MacPorts:  https://www.macports.org/install.php

After MacPorts is installed and `port` is on PATH, rerun this script.
EOF
    exit 1
  fi

  sudo port selfupdate
  sudo port install git curl jq ripgrep zip unzip npm10
}

ensure_node_macports() {
  if command -v node >/dev/null 2>&1; then
    NODE_VERSION="$(node --version)"
    NODE_MAJOR="$(printf '%s' "${NODE_VERSION#v}" | cut -d. -f1)"
    if [[ "${NODE_MAJOR}" -ge 20 ]]; then
      return 0
    fi
  fi

  sudo port install nodejs20
  if [[ -x /opt/local/bin/node ]]; then
    export PATH="/opt/local/bin:${PATH}"
  fi

  if ! command -v node >/dev/null 2>&1; then
    echo "Node was installed via MacPorts but is not on PATH. Add /opt/local/bin to PATH and rerun." >&2
    exit 1
  fi

  NODE_VERSION="$(node --version)"
  NODE_MAJOR="$(printf '%s' "${NODE_VERSION#v}" | cut -d. -f1)"
  if [[ "${NODE_MAJOR}" -lt 20 ]]; then
    echo "Node 20+ is required but was not provisioned successfully on macOS." >&2
    exit 1
  fi
}

choose_services() {
  cat <<'EOF'
Select which hosted coding CLIs to install:
  1) Claude Code only
  2) Codex only
  3) Gemini CLI only
  4) Claude Code + Codex
  5) Claude Code + Gemini CLI
  6) Codex + Gemini CLI
  7) All three
EOF

  local choice
  while true; do
    read -r -p "Enter selection [1-7]: " choice
    case "${choice}" in
      1) INSTALL_CLAUDE="1"; break ;;
      2) INSTALL_CODEX="1"; break ;;
      3) INSTALL_GEMINI="1"; break ;;
      4) INSTALL_CLAUDE="1"; INSTALL_CODEX="1"; break ;;
      5) INSTALL_CLAUDE="1"; INSTALL_GEMINI="1"; break ;;
      6) INSTALL_CODEX="1"; INSTALL_GEMINI="1"; break ;;
      7) INSTALL_CLAUDE="1"; INSTALL_CODEX="1"; INSTALL_GEMINI="1"; break ;;
      *) echo "Please choose 1-7." ;;
    esac
  done
}

install_claude() {
  log "Installing Claude Code..."
  npm_global_install @anthropic-ai/claude-code
  require_command "claude" "Claude Code install did not place the binary on PATH."
  record_line "- Claude Code installed: $(command -v claude)"
}

install_codex() {
  log "Installing Codex..."
  npm_global_install @openai/codex
  require_command "codex" "Codex install did not place the binary on PATH."
  record_line "- Codex installed: $(command -v codex)"
}

install_gemini() {
  log "Installing Gemini CLI..."
  npm_global_install @google/gemini-cli
  require_command "gemini" "Gemini CLI install did not place the binary on PATH."
  record_line "- Gemini CLI installed: $(command -v gemini)"
}

auth_guidance() {
  record_section "## Authentication Guidance"

  if [[ "${INSTALL_CLAUDE}" == "1" ]]; then
    cat <<'EOF'

Claude Code authentication:
- Preferred: launch `claude` and complete the browser-based sign-in flow with your Claude.ai subscription.
- Alternate enterprise routes: Anthropic Console API, Bedrock, or Vertex.
EOF
    record_line "- Claude Code auth: run \`claude\` and complete the login flow."
  fi

  if [[ "${INSTALL_CODEX}" == "1" ]]; then
    cat <<'EOF'

Codex authentication:
- Preferred: run `codex --login` or `codex` and choose Sign in with ChatGPT.
- Alternate route: API key mode if subscription sign-in is not available.
EOF
    record_line "- Codex auth: run \`codex --login\` or \`codex\` and choose Sign in with ChatGPT."
  fi

  if [[ "${INSTALL_GEMINI}" == "1" ]]; then
    cat <<'EOF'

Gemini CLI authentication:
- Preferred: run `gemini` and choose Login with Google.
- Alternate route: set `GEMINI_API_KEY`.
- If login fails unexpectedly:
  - unset `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_PROJECT_ID`
  - on corporate TLS networks, try `NODE_USE_SYSTEM_CA=1`
  - if needed, set `NODE_EXTRA_CA_CERTS=/path/to/corporate-ca.crt`
  - if interactive mode is missing, check for `CI_*` environment variables
EOF
    record_line "- Gemini CLI auth: run \`gemini\` and choose Login with Google or configure \`GEMINI_API_KEY\`."
    record_line "- Gemini CLI pitfall: unset GOOGLE_CLOUD_PROJECT* if org entitlement checks appear unexpectedly."
    record_line "- Gemini CLI pitfall: set NODE_USE_SYSTEM_CA=1 or NODE_EXTRA_CA_CERTS on corporate TLS-inspection networks."
  fi
}

write_log_header() {
  cat > "${MACHINE_SETUP_LOG}" <<EOF
# Workstation Bootstrap Log

- Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Host OS: ${OS_NAME}
- Package mode: ${PACKAGE_MODE:-unknown}
- Projects root: ${PROJECTS_ROOT}
- Factory root: ${ROOT_DIR}

## Selected Services

EOF
}

check_ready_state() {
  local any_missing=0

  record_section "## Ready State"
  echo
  echo "── Ready state check ────────────────────────────────────────────────────────"

  _check_cli() {
    local label="$1"
    local binary="$2"
    local auth_hint="$3"
    local ver

    if command -v "${binary}" >/dev/null 2>&1; then
      ver="$("${binary}" --version 2>&1 || echo "version unknown")"
      record_line "- ${label}: installed (${ver}) — auth: pending"
      echo "  ${label}: installed — ${ver}"
      echo "    To authenticate: ${auth_hint}"
    else
      record_line "- ${label}: NOT found on PATH"
      echo "  ${label}: NOT found on PATH"
      any_missing=1
    fi
  }

  [[ "${INSTALL_CLAUDE}" == "1" ]] && _check_cli "Claude Code" "claude" "run: claude"
  [[ "${INSTALL_CODEX}"  == "1" ]] && _check_cli "Codex"       "codex"  "run: codex --login"
  [[ "${INSTALL_GEMINI}" == "1" ]] && _check_cli "Gemini CLI"  "gemini" "run: gemini"

  echo

  if [[ "${any_missing}" -eq 0 ]]; then
    record_line "- overall: all selected CLIs installed — complete auth steps above"
    echo "  All selected CLIs installed."
    echo "  Complete the authentication steps above, then bootstrap a project."
  else
    record_line "- overall: one or more CLIs not found — check PATH or re-run install"
    echo "  One or more CLIs are not on PATH. Check the install output above,"
    echo "  open a fresh shell, and re-run this script if needed."
  fi

  record_section "## Next Recommended Command"
  record_line ""
  record_line "\`\`\`bash"
  record_line "cd ${ROOT_DIR}"
  record_line "./scripts/bootstrap-project.sh --name <your-project>"
  record_line "\`\`\`"
}

detect_platform
ensure_sudo
write_log_header

record_section "## Base Dependencies"
if [[ "${PACKAGE_MODE}" == "apt" ]]; then
  ensure_base_dependencies_apt
  ensure_node_apt
elif [[ "${PACKAGE_MODE}" == "macports" ]]; then
  ensure_base_dependencies_macports
  ensure_node_macports
fi

record_line "- Package mode: ${PACKAGE_MODE}"
record_line "- Node version: $(node --version)"

choose_services

record_line ""
[[ "${INSTALL_CLAUDE}" == "1" ]] && record_line "- Claude Code: selected"
[[ "${INSTALL_CODEX}"  == "1" ]] && record_line "- Codex: selected"
[[ "${INSTALL_GEMINI}" == "1" ]] && record_line "- Gemini CLI: selected"

record_section "## Install Results"

if [[ "${INSTALL_CLAUDE}" == "1" ]]; then
  install_claude
fi
if [[ "${INSTALL_CODEX}" == "1" ]]; then
  install_codex
fi
if [[ "${INSTALL_GEMINI}" == "1" ]]; then
  install_gemini
fi

auth_guidance
check_ready_state

record_section "## Next Steps"
record_line "1. Complete the auth flows described above."
record_line "2. Bootstrap the next governed project after auth succeeds:"
record_line "     ${ROOT_DIR}/scripts/bootstrap-project.sh --name <your-project>"

cat <<EOF

Workstation bootstrap completed.
Log written to: ${MACHINE_SETUP_LOG}

Next step:
  cd ${ROOT_DIR}
  ./scripts/bootstrap-project.sh --name <your-project>
EOF

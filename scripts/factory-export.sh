#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FORGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${AGENT_FORGE_ROOT}/.." && pwd)"
OUTPUT_ROOT="${AGENT_FORGE_ROOT}/exports"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
BUNDLE_BASENAME="agent-forge-suitcase-${STAMP}"
EXPORT_DIR="${OUTPUT_ROOT}/${BUNDLE_BASENAME}"
ARCHIVE_TGZ="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.tar.gz"
ARCHIVE_ZIP="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.zip"
WINDOWS_DEPLOY_SCRIPT="${OUTPUT_ROOT}/${BUNDLE_BASENAME}-deploy-and-bootstrap.ps1"
EXPORT_MODE="unset"   # "unset" = ask interactively; "onboarding", "clean", or "backup"

# Detect non-interactive stdin so we can fall back to "onboarding" silently.
if [[ ! -t 0 ]]; then
  EXPORT_MODE="onboarding"
fi

usage() {
  cat <<'EOF'
Usage: factory-export.sh [--output-root DIR] [--name NAME] [--mode onboarding|clean|backup]

Build a portable Agent Forge suitcase snapshot.

Export modes (interactive by default — you are asked if --mode is not passed):

  onboarding  Production-grade framework bundle for shipping to coworkers or
              fresh machines. Includes all canonical skills, hooks, policies,
              and framework docs. Excludes machine-local runtime state. Emits
              a platform-specific START_HERE.txt at the bundle root.
              (default when running non-interactively)

  clean       Same exclusions as onboarding plus stub-replace HANDOFF.md and
              TECH_DEBT.md. Use when the working tree still carries operator
              history that needs scrubbing for an outbound copy.

  backup      Preserve current state faithfully, including session history
              and accumulated notes. Use this for personal backups of your
              live factory.

Contents (all modes):
  - canonical _agent_forge source (skills, teams, governance docs, scripts, generated-host logic)
  - shared root doctrine docs
  - manifest and operator README
  - compressed .tar.gz and .zip archives

Options:
  --mode onboarding|clean|backup   Export mode (asked interactively if omitted)
  --output-root DIR                Override the export output directory
  --name NAME                      Override the archive basename
  -h, --help                       Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      EXPORT_MODE="${2:?--mode requires onboarding, clean, or backup}"
      case "${EXPORT_MODE}" in
        onboarding|clean|backup) ;;
        *) echo "Unknown mode: ${EXPORT_MODE}  (must be onboarding, clean, or backup)" >&2; exit 1 ;;
      esac
      shift 2
      ;;
    --output-root)
      OUTPUT_ROOT="${2:?missing output root}"
      shift 2
      ;;
    --name)
      BUNDLE_BASENAME="${2:?missing bundle name}"
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

# Interactive mode selection if not specified
if [[ "${EXPORT_MODE}" == "unset" ]]; then
  echo "Export mode:"
  echo "  onboarding — production-grade framework bundle, no machine-local state  (recommended for sharing)"
  echo "  clean      — like onboarding, plus stub-replace HANDOFF/TECH_DEBT if working tree still has history"
  echo "  backup     — preserve current state including session notes and tech-debt log"
  echo
  while true; do
    read -r -p "Select export mode [onboarding/clean/backup]: " _mode
    case "${_mode}" in
      onboarding|clean|backup) EXPORT_MODE="${_mode}"; break ;;
      *) echo "Please type onboarding, clean, or backup." ;;
    esac
  done
  echo
fi

EXPORT_DIR="${OUTPUT_ROOT}/${BUNDLE_BASENAME}"
ARCHIVE_TGZ="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.tar.gz"
ARCHIVE_ZIP="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.zip"
WINDOWS_DEPLOY_SCRIPT="${OUTPUT_ROOT}/${BUNDLE_BASENAME}-deploy-and-bootstrap.ps1"

mkdir -p "${OUTPUT_ROOT}"
rm -rf "${EXPORT_DIR}"
mkdir -p "${EXPORT_DIR}/shared-root/docs"

echo "Building suitcase (mode: ${EXPORT_MODE})..."

tar -C "${WORKSPACE_ROOT}" \
  --exclude='_agent_forge/.git' \
  --exclude='_agent_forge/exports' \
  --exclude='_agent_forge/runtime/managed-state.json' \
  --exclude='_agent_forge/runtime/validation' \
  --exclude='_agent_forge/dev' \
  --exclude='_agent_forge/dist' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='_agent_forge/**/__pycache__' \
  --exclude='_agent_forge/**/*.pyc' \
  --exclude='_agent_forge/**/*.pyo' \
  --exclude='_agent_forge/.pytest_cache' \
  --exclude='_agent_forge/.mypy_cache' \
  --exclude='_agent_forge/.ruff_cache' \
  --exclude='_agent_forge/.forge_state' \
  --exclude='_agent_forge/.claude' \
  --exclude='_agent_forge/.codex' \
  --exclude='_agent_forge/.gemini' \
  --exclude='_agent_forge/.agents' \
  --exclude='_agent_forge/MEMORY.md' \
  -cf - _agent_forge | tar -C "${EXPORT_DIR}" -xf -

# ── Clean-mode: strip source-environment-specific residue ────────────────────
# Skills, teams, governance docs, scripts, and workflow docs are always preserved.
# Only session-specific notes (HANDOFF, TECH_DEBT) are replaced with stubs.
if [[ "${EXPORT_MODE}" == "clean" ]]; then
  EXPORTED_FACTORY="${EXPORT_DIR}/_agent_forge"

  cat > "${EXPORTED_FACTORY}/docs/HANDOFF.md" <<'STUB'
# Agent Forge Handoff

This is a clean factory export. No prior-session history was carried over.

## Current State

- Factory deployed from a clean suitcase snapshot
- Skills, teams, adapters, and scripts are all present
- No prior session work or follow-up items from another machine

## Next Restart Point

1. Read `docs/FACTORY_SUITCASE.md` and `docs/WORKSTATION_BOOTSTRAP.md` to understand the setup flow.
2. Bootstrap a project: `./scripts/bootstrap-project.sh --name <your-project>`
3. Update this file after your first real working session.
STUB

  cat > "${EXPORTED_FACTORY}/docs/TECH_DEBT.md" <<'STUB'
# Tech Debt

This is a clean factory export. No accumulated debt carried over from the source machine.

## Notes For The Next Session

- Review `docs/FACTORY_SUITCASE.md` for the canonical deploy and bootstrap flow.
- Treat `_agent_forge` as the source of truth for all shared skills, teams, and adapters.
- Do not initialize git at the `~/Projects` root level.
STUB

  # Remove any leftover machine-setup runtime logs if somehow included while
  # keeping the tracked validation matrix as doctrine.
  rm -f "${EXPORTED_FACTORY}/runtime/managed-state.json"
  rm -rf "${EXPORTED_FACTORY}/runtime/validation"
fi

if [[ "${EXPORT_MODE}" == "onboarding" ]]; then
  # Onboarding mode emits framework-only stubs for the shared root, not the
  # source machine's parent-tree docs. This guarantees no COI residue from
  # the operator's personal ~/Projects/AGENTS.md / CLAUDE.md leaks into the
  # shipped bundle. Recipients populate their own shared root if they want one.
  cat > "${EXPORT_DIR}/shared-root/AGENTS.md" <<'SHAREDEOF'
# Shared Agent Contract

This file is a placeholder. It exists so the bundle's shared-root/ layout
is complete on extraction. If you maintain multiple governed projects
under one parent directory, customize this file with your shared
multi-agent contract.

The canonical Agent Forge multi-agent contract lives at
`_agent_forge/AGENTS.md` and is the authoritative source.
SHAREDEOF

  cat > "${EXPORT_DIR}/shared-root/CLAUDE.md" <<'SHAREDEOF'
# Shared Claude Adapter

Thin host adapter for Claude Code at the parent-directory level.
Replace this with your own customizations if you run multiple
governed projects under one parent tree.

Claude Code's canonical boot adapter for the factory is
`_agent_forge/CLAUDE.md`.
SHAREDEOF

  cat > "${EXPORT_DIR}/shared-root/docs/gotchas.md" <<'SHAREDEOF'
# Cross-Project Gotchas

Track durable cross-project quirks and workarounds here.
The factory's own gotchas live in
`_agent_forge/docs/LESSONS_LEARNED.md`.
SHAREDEOF

  cat > "${EXPORT_DIR}/shared-root/docs/port_ledger.md" <<'SHAREDEOF'
# Port Ledger

Track local port assignments across projects here to avoid collisions.
Empty on a fresh install — populate as you allocate ports.
SHAREDEOF
else
  # clean and backup modes preserve parent-tree shared docs if they exist.
  if [[ -f "${WORKSPACE_ROOT}/AGENTS.md" ]]; then
    cp "${WORKSPACE_ROOT}/AGENTS.md" "${EXPORT_DIR}/shared-root/AGENTS.md"
  fi
  if [[ -f "${WORKSPACE_ROOT}/CLAUDE.md" ]]; then
    cp "${WORKSPACE_ROOT}/CLAUDE.md" "${EXPORT_DIR}/shared-root/CLAUDE.md"
  fi
  if [[ -f "${WORKSPACE_ROOT}/docs/gotchas.md" ]]; then
    cp "${WORKSPACE_ROOT}/docs/gotchas.md" "${EXPORT_DIR}/shared-root/docs/gotchas.md"
  fi
  if [[ -f "${WORKSPACE_ROOT}/docs/port_ledger.md" ]]; then
    cp "${WORKSPACE_ROOT}/docs/port_ledger.md" "${EXPORT_DIR}/shared-root/docs/port_ledger.md"
  fi
fi

SOURCE_COMMIT="$(git -C "${AGENT_FORGE_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
GENERATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# BUNDLE_README.md at the bundle root — the inviting introduction for a coworker
# meeting the factory for the first time. Pairs with START_HERE.txt (quickstart);
# this file is the "what is this and why should you care" front door.
if [[ -f "${AGENT_FORGE_ROOT}/BUNDLE_README.md" ]]; then
  cp "${AGENT_FORGE_ROOT}/BUNDLE_README.md" "${EXPORT_DIR}/BUNDLE_README.md"
fi

# START_HERE.txt at the bundle root — the first thing a recipient should read.
cat > "${EXPORT_DIR}/START_HERE.txt" <<'STARTEOF'
Agent Forge Portable Suitcase
==============================

WHAT THIS IS
  A portable multi-agent governance framework for Claude Code, Codex,
  and Gemini CLI. Generates host-native skills, hooks, and memory
  surfaces from one canonical source.

QUICKSTART (pick your platform)

  Linux or macOS:
    cd <unpacked-bundle>
    ./_agent_forge/scripts/deploy-and-bootstrap.sh

  Windows ZIP transfer (native PowerShell, no WSL required):
    powershell.exe -ExecutionPolicy Bypass -File .\agent-forge-suitcase-<timestamp>-deploy-and-bootstrap.ps1 -BundleZip .\agent-forge-suitcase-<timestamp>.zip -DestinationRoot .\af

  Then in Claude Code, invoke the onboarding-guide skill for an
  interactive walkthrough:
    /onboarding-guide

REQUIREMENTS
  Linux / macOS: Python 3.10+, git, tar
  macOS: MacPorts (NOT Homebrew)
  Windows: Python 3.10+, git, PowerShell 5.1+ (ships with Windows 10+)
  Windows Codex runtime: use WSL2 unless codex --version works in native PowerShell

  Plus at least one host CLI:
    - Claude Code  (anthropic.com)
    - OpenAI Codex CLI  (optional)
    - Gemini CLI  (optional)

DOCS
  _agent_forge/README.md         — full project overview
  _agent_forge/docs/QUICKSTART.md — first-run flow
  _agent_forge/docs/CONOPS.md     — durable architecture
  _agent_forge/AGENTS.md          — multi-agent contract

VERIFY THE INSTALL
  python3 _agent_forge/scripts/verify-agent-forge.py
  Expect exit 0 with no [FAIL] lines.

NEED HELP
  After deploy, in Claude Code: /onboarding-guide
  Skim _agent_forge/docs/QUICKSTART.md.
STARTEOF

cat > "${EXPORT_DIR}/README.md" <<EOF
# Agent Forge Portable Suitcase

Generated: ${GENERATED_AT_UTC}
Source commit: ${SOURCE_COMMIT}
Export mode: ${EXPORT_MODE}

Quick purpose: this bundle installs the Agent Forge framework onto a fresh machine so it is ready for multi-LLM project work after one deploy step and one workstation-bootstrap step.

> **Export mode: ${EXPORT_MODE}**
> $(case "${EXPORT_MODE}" in onboarding) echo "Production-grade framework bundle. No machine-local runtime state included.";; clean) echo "Factory capability only. Session history and machine-specific notes have been replaced with clean stubs.";; *) echo "Full backup. Includes session history and accumulated notes from the source machine.";; esac)

## What This Bundle Contains

- \`_agent_forge/\` canonical factory snapshot
- \`shared-root/\` shared doctrine docs for a clean \`~/Projects\` root
- deployment scripts at \`_agent_forge/scripts/deploy-and-bootstrap.sh\` and \`_agent_forge/scripts/deploy-and-bootstrap.ps1\`

## What This Bundle Does Not Contain

- governed project repositories
- \`.env\` files or secrets
- machine-local settings, caches, or runtime data

## Quick Start

You can unpack this bundle anywhere. The deploy script installs into \`~/Projects\` by default, so the unzip location does not need to be your final working directory.

Recommended on Linux/macOS:

\`\`\`bash
tar -xzf ${BUNDLE_BASENAME}.tar.gz
cd ${BUNDLE_BASENAME}
./_agent_forge/scripts/deploy-factory.sh
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
\`\`\`

If you used the \`.zip\` archive on Windows, prefer the generated sidecar PowerShell deploy script instead of Explorer's Extract All.

Recommended on Windows:

\`\`\`powershell
powershell.exe -ExecutionPolicy Bypass -File .\\${BUNDLE_BASENAME}-deploy-and-bootstrap.ps1 -BundleZip .\\${BUNDLE_BASENAME}.zip -DestinationRoot .\\af
\`\`\`

## Deploy On A Fresh Machine

\`\`\`bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-and-bootstrap.sh
\`\`\`

What this does:

- installs \`_agent_forge\` into \`~/Projects\`
- copies shared doctrine docs into \`~/Projects\`
- syncs Claude, Codex, and Gemini factory surfaces

What this does not do:

- install Claude Code, Codex CLI, or Gemini CLI
- authenticate any hosted service
- create a project yet

## Prepare The Machine For LLM Development

\`\`\`bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
\`\`\`

This second script:

- installs base development dependencies
- installs the selected hosted coding CLIs
- walks you through authentication
- writes a machine setup log

## Bootstrap A New Project After Deploy

After authentication is complete:

\`\`\`bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
\`\`\`

The script automatically syncs Claude, Codex, and Gemini surfaces and offers
an interactive project-definition flow. No separate sync commands needed.

Only run project bootstrap after the workstation bootstrap and authentication steps are complete.

## Archive Formats

This export creates three outputs:

- folder: easiest to inspect and test locally
- \`.tar.gz\`: preferred for Linux/macOS because it preserves Unix metadata cleanly
- \`.zip\`: convenience format for tools or transfer flows that expect zip archives

If you are choosing one for Debian/Ubuntu or macOS, prefer the \`.tar.gz\`.

## Keep In Mind

- This machine remains the canonical source of truth.
- Remote suitcase copies are snapshots, not live mirrors.
- If the factory improves on the canonical machine, rebuild and redeploy a fresh suitcase.
EOF

python3 - "${EXPORT_DIR}/MANIFEST.json" "${BUNDLE_BASENAME}" "${GENERATED_AT_UTC}" "${SOURCE_COMMIT}" "${EXPORT_MODE}" <<'PY'
import json
import sys

manifest_path, bundle_name, generated_at, source_commit, export_mode = sys.argv[1:6]
manifest = {
    "bundle_name": bundle_name,
    "generated_at_utc": generated_at,
    "source_commit": source_commit,
    "export_mode": export_mode,
    "payload_root": "_agent_forge",
    "shared_root_files": [
        "shared-root/AGENTS.md",
        "shared-root/CLAUDE.md",
        "shared-root/docs/gotchas.md",
        "shared-root/docs/port_ledger.md",
    ],
    "excluded_categories": [
        "project repositories",
        "secrets and .env files",
        "machine-local settings",
        "runtime data and caches",
        "git metadata",
        "runtime machine-setup logs",
    ],
}
if export_mode == "clean":
    manifest["clean_mode_note"] = (
        "HANDOFF.md and TECH_DEBT.md replaced with clean stubs. "
        "All skills, teams, governance docs, and workflow docs preserved."
    )
if export_mode == "onboarding":
    manifest["framework_only"] = True
    manifest["onboarding_mode_note"] = (
        "Production-grade framework bundle. Machine-local runtime state "
        "(runtime/managed-state.json, runtime/validation/, dev/, dist/, "
        ".forge_state/, .claude/, .codex/, .gemini/, .agents/, MEMORY.md) excluded "
        "— these are regenerated on the target machine by deploy-factory. "
        "START_HERE.txt at bundle root has platform-specific quickstart."
    )
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")
PY

tar -C "${OUTPUT_ROOT}" -czf "${ARCHIVE_TGZ}" "${BUNDLE_BASENAME}"
python3 - "${OUTPUT_ROOT}" "${BUNDLE_BASENAME}" "${ARCHIVE_ZIP}" <<'PY'
from pathlib import Path
import sys
import zipfile

output_root = Path(sys.argv[1])
bundle_name = sys.argv[2]
archive_zip = Path(sys.argv[3])
bundle_dir = output_root / bundle_name

with zipfile.ZipFile(archive_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(bundle_dir.rglob("*")):
        arcname = Path(bundle_name) / path.relative_to(bundle_dir)
        if path.is_dir():
            continue
        zf.write(path, arcname)
PY

cp "${AGENT_FORGE_ROOT}/scripts/deploy-and-bootstrap.ps1" "${WINDOWS_DEPLOY_SCRIPT}"

echo "Portable factory export created:"
echo "  Directory: ${EXPORT_DIR}"
echo "  tar.gz:    ${ARCHIVE_TGZ}"
echo "  zip:       ${ARCHIVE_ZIP}"
echo "  Windows:   ${WINDOWS_DEPLOY_SCRIPT}"

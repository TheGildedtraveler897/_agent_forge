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
EXPORT_MODE="unset"   # "unset" = ask interactively; "clean" or "backup"

# Detect non-interactive stdin so we can fall back to "clean" silently.
if [[ ! -t 0 ]]; then
  EXPORT_MODE="clean"
fi

usage() {
  cat <<'EOF'
Usage: factory-export.sh [--output-root DIR] [--name NAME] [--mode clean|backup]

Build a portable Agent Forge suitcase snapshot.

Export modes (interactive by default — you are asked if --mode is not passed):

  clean   Portable factory capability only. Source-environment-specific residue
          is stripped: session handoffs, accumulated tech-debt notes, and
          machine-specific runtime logs are replaced with clean stubs.
          Use this when moving the factory to a new machine or company.
          (default when running non-interactively)

  backup  Preserve current state faithfully, including session history and
          accumulated notes. Use this for personal backups of your live factory.

Contents (both modes):
  - canonical _agent_forge source (skills, teams, governance docs, scripts, generated-host logic)
  - shared root doctrine docs
  - manifest and operator README
  - compressed .tar.gz and .zip archives

Options:
  --mode clean|backup   Export mode (asked interactively if omitted)
  --output-root DIR     Override the export output directory
  --name NAME           Override the archive basename
  -h, --help            Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      EXPORT_MODE="${2:?--mode requires clean or backup}"
      case "${EXPORT_MODE}" in
        clean|backup) ;;
        *) echo "Unknown mode: ${EXPORT_MODE}  (must be clean or backup)" >&2; exit 1 ;;
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
  echo "  clean   — factory capability only, no prior-session history  (recommended for sharing / new machine)"
  echo "  backup  — preserve current state including session notes and tech-debt log"
  echo
  while true; do
    read -r -p "Select export mode [clean/backup]: " _mode
    case "${_mode}" in
      clean|backup) EXPORT_MODE="${_mode}"; break ;;
      *) echo "Please type clean or backup." ;;
    esac
  done
  echo
fi

EXPORT_DIR="${OUTPUT_ROOT}/${BUNDLE_BASENAME}"
ARCHIVE_TGZ="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.tar.gz"
ARCHIVE_ZIP="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.zip"

mkdir -p "${OUTPUT_ROOT}"
rm -rf "${EXPORT_DIR}"
mkdir -p "${EXPORT_DIR}/shared-root/docs"

echo "Building suitcase (mode: ${EXPORT_MODE})..."

tar -C "${WORKSPACE_ROOT}" \
  --exclude='./_agent_forge/.git' \
  --exclude='./_agent_forge/exports' \
  --exclude='./_agent_forge/runtime/managed-state.json' \
  --exclude='./_agent_forge/runtime/validation' \
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

cp "${WORKSPACE_ROOT}/AGENTS.md" "${EXPORT_DIR}/shared-root/AGENTS.md"
cp "${WORKSPACE_ROOT}/CLAUDE.md" "${EXPORT_DIR}/shared-root/CLAUDE.md"
cp "${WORKSPACE_ROOT}/docs/gotchas.md" "${EXPORT_DIR}/shared-root/docs/gotchas.md"
cp "${WORKSPACE_ROOT}/docs/port_ledger.md" "${EXPORT_DIR}/shared-root/docs/port_ledger.md"

SOURCE_COMMIT="$(git -C "${AGENT_FORGE_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
GENERATED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "${EXPORT_DIR}/README.md" <<EOF
# Agent Forge Portable Suitcase

Generated: ${GENERATED_AT_UTC}
Source commit: ${SOURCE_COMMIT}
Export mode: ${EXPORT_MODE}

Quick purpose: this bundle installs the Agent Forge framework onto a fresh machine so it is ready for multi-LLM project work after one deploy step and one workstation-bootstrap step.

> **Export mode: ${EXPORT_MODE}**
> $(if [[ "${EXPORT_MODE}" == "clean" ]]; then echo "Factory capability only. Session history and machine-specific notes have been replaced with clean stubs."; else echo "Full backup. Includes session history and accumulated notes from the source machine."; fi)

## What This Bundle Contains

- \`_agent_forge/\` canonical factory snapshot
- \`shared-root/\` shared doctrine docs for a clean \`~/Projects\` root
- deployment script at \`_agent_forge/scripts/deploy-factory.sh\`

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

If you used the \`.zip\` archive instead, unzip it first and then run the same two scripts.

## Deploy On A Fresh Machine

\`\`\`bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-factory.sh
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

echo "Portable factory export created:"
echo "  Directory: ${EXPORT_DIR}"
echo "  tar.gz:    ${ARCHIVE_TGZ}"
echo "  zip:       ${ARCHIVE_ZIP}"

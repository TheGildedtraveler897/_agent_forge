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

usage() {
  cat <<'EOF'
Usage: factory-export.sh [--output-root DIR] [--name NAME]

Build a portable Agent Forge suitcase snapshot containing:
  - canonical _agent_forge source
  - shared root doctrine docs needed on a fresh machine
  - a manifest and operator README
  - compressed tar.gz and zip archives

Options:
  --output-root DIR  Override the export output directory
  --name NAME        Override the archive basename
  -h, --help         Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

EXPORT_DIR="${OUTPUT_ROOT}/${BUNDLE_BASENAME}"
ARCHIVE_TGZ="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.tar.gz"
ARCHIVE_ZIP="${OUTPUT_ROOT}/${BUNDLE_BASENAME}.zip"

mkdir -p "${OUTPUT_ROOT}"
rm -rf "${EXPORT_DIR}"
mkdir -p "${EXPORT_DIR}/shared-root/docs"

tar -C "${WORKSPACE_ROOT}" \
  --exclude='./_agent_forge/.git' \
  --exclude='./_agent_forge/exports' \
  -cf - _agent_forge | tar -C "${EXPORT_DIR}" -xf -

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

## What This Bundle Contains

- \`_agent_forge/\` canonical factory snapshot
- \`shared-root/\` shared doctrine docs for a clean \`~/Projects\` root
- deployment script at \`_agent_forge/scripts/deploy-factory.sh\`

## What This Bundle Does Not Contain

- governed project repositories
- \`.env\` files or secrets
- machine-local settings, caches, or runtime data

## Deploy On A Fresh Machine

\`\`\`bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-factory.sh
\`\`\`

## Prepare The Machine For LLM Development

\`\`\`bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
\`\`\`

## Bootstrap A New Project After Deploy

\`\`\`bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
./scripts/bootstrap-project.sh --name reddit-archive
./scripts/sync-claude-adapters.sh --project reddit-archive
./scripts/sync-codex-skills.sh --project reddit-archive
\`\`\`
EOF

python3 - "${EXPORT_DIR}/MANIFEST.json" "${BUNDLE_BASENAME}" "${GENERATED_AT_UTC}" "${SOURCE_COMMIT}" <<'PY'
import json
import sys

manifest_path, bundle_name, generated_at, source_commit = sys.argv[1:5]
manifest = {
    "bundle_name": bundle_name,
    "generated_at_utc": generated_at,
    "source_commit": source_commit,
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
    ],
}
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

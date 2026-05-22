#!/usr/bin/env bash
# POSIX forwarder. The canonical implementation lives in guardian.py
# so it runs natively on Windows Claude Code (no bash). This wrapper
# exists for legacy hook records that invoke the .sh path directly.
exec python3 "$(dirname "$0")/guardian.py" "$@"

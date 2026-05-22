#!/usr/bin/env bash
# POSIX forwarder. The canonical implementation lives in auto-activator.py
# so it runs natively on Windows Claude Code (no bash).
exec python3 "$(dirname "$0")/auto-activator.py" "$@"

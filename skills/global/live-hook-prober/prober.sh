#!/usr/bin/env bash
# POSIX forwarder. The canonical implementation lives in prober.py
# so it runs natively on Windows. This wrapper exists for legacy
# scripts that call the .sh path directly.
exec python3 "$(dirname "$0")/prober.py" "$@"

#!/usr/bin/env bash
# prompt-auto-activator: user_prompt_submit advisory hook.
# Reads the prompt JSON on stdin, regex-matches a keyword table,
# and prints one advisory line per match to stdout. Never blocks.

set -u

INPUT=""
if read -t 1 -r line; then
    INPUT="$line"
    while read -t 0.1 -r line; do
        INPUT="${INPUT}
${line}"
    done
fi

# Pull the prompt body if the host wraps stdin in JSON; otherwise use raw.
PROMPT="$(printf '%s' "$INPUT" | grep -oE '"prompt"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' | head -1 | sed -E 's/^"prompt"[[:space:]]*:[[:space:]]*"//; s/"$//')"
[ -z "$PROMPT" ] && PROMPT="$INPUT"

advise() { printf '{"advice":"%s","skill":"%s"}\n' "$1" "$2"; }

shopt -s nocasematch 2>/dev/null || true
case "$PROMPT" in
    *"/caveman"*|*"caveman mode"*|*"/terse"*|*"terse mode"*)
        advise "Operator requested terse output; load token-optimizer." "token-optimizer" ;;
esac
case "$PROMPT" in
    *"/checkpoint"*|*"/handoff"*)
        advise "Operator requested checkpoint; load context-engineer." "context-engineer" ;;
esac

exit 0

#!/usr/bin/env bash
# telemetry-guardian: universal pre-tool-execution guardrail.
# Reads one JSON tool invocation on stdin; exits 0 to allow, 1 to block, 2 on self-error.
# Deny list is fixed-string / short grep -E patterns; err toward blocking.
# Opt out: AGENT_FORGE_GUARDIAN=off (logged to ~/.agent-forge/guardian.log).

set -u

LOG_DIR="${HOME}/.agent-forge"
LOG_FILE="${LOG_DIR}/guardian.log"

emit() {
    # emit <verdict> <reason> <matched>
    local verdict="$1"
    local reason="$2"
    local matched="${3:-}"
    printf '{"verdict":"%s","reason":"%s","matched":"%s"}\n' "$verdict" "$reason" "$matched"
}

log_line() {
    mkdir -p "$LOG_DIR" 2>/dev/null || return 0
    printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" >>"$LOG_FILE" 2>/dev/null || true
}

# Read stdin (tolerant of non-JSON hosts; fall back to raw text).
INPUT=""
if ! read -t 1 -r line; then
    :
else
    INPUT="$line"
    while read -t 0.1 -r line; do
        INPUT="${INPUT}
${line}"
    done
fi

# Extract the command. Try a few known shapes via grep; fall back to full input.
extract_command() {
    local s="$1"
    # Matches "command":"<value>" up to the next unescaped quote. Rough but sufficient.
    local m
    m=$(printf '%s' "$s" | grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' | head -1)
    if [ -n "$m" ]; then
        # Strip the prefix and surrounding quotes.
        printf '%s' "$m" | sed -E 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//'
        return 0
    fi
    printf '%s' "$s"
}

CMD="$(extract_command "$INPUT")"

# Opt-out path.
if [ "${AGENT_FORGE_GUARDIAN:-on}" = "off" ]; then
    log_line "bypass" "$CMD"
    emit "allow" "guardian bypassed via AGENT_FORGE_GUARDIAN=off" ""
    exit 0
fi

# Deny list. Each pattern block sets MATCHED and REASON, then emits+exits 1.
check() {
    local pattern="$1"
    local reason="$2"
    if printf '%s' "$CMD" | grep -qE -e "$pattern"; then
        log_line "block" "$CMD"
        emit "block" "$reason" "$pattern"
        exit 1
    fi
}

check '--no-verify([[:space:]]|$)'                          "bypassing pre-commit hooks is not allowed"
check '(--no-gpg-sign|commit\.gpgsign=false)'               "bypassing commit signing is not allowed"
check 'git[[:space:]]+push[[:space:]].*(--force|--force-with-lease).*(main|master|develop)' \
                                                            "force-push to a protected branch is not allowed"
check '(main|master|develop).*(--force|--force-with-lease).*git[[:space:]]+push' \
                                                            "force-push to a protected branch is not allowed"
check 'git[[:space:]]+reset[[:space:]]+--hard[[:space:]]+[^[:space:]]+' \
                                                            "git reset --hard against an explicit ref is gated; drop the target or override"
check 'rm[[:space:]]+-rf[[:space:]]+(~|\$HOME|/)([[:space:]]|$|/\*)' \
                                                            "wildcard root/home deletion is not allowed"
check 'terraform[[:space:]]+destroy([[:space:]](-[^t]|[^-])|$)' \
                                                            "terraform destroy without -target is not allowed"
check 'dd[[:space:]]+.*of=/dev/sd[a-z]'                     "whole-disk dd writes are not allowed"
check 'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+(~|\$HOME|/)' \
                                                            "recursive 777 on home/root is not allowed"

emit "allow" "no deny-list match" ""
exit 0

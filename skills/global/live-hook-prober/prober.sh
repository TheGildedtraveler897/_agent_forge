#!/usr/bin/env bash
# live-hook-prober: fire a known test command on a target host CLI and
# verify whether the seeded pre-tool-execution-guardian hook actually
# intercepted it as expected. Closes the silent-correctness gap exposed
# by the 2026-04-25 Gemini event-alias drift (C1).
#
# Output (stdout): single-line JSON.
# Exit: 0 verdict=pass, 1 verdict=fail, 2 escalated (sandbox/trust block).

set -u

usage() {
    cat <<'EOF' 1>&2
Usage:
  prober.sh --host <claude|codex|gemini>
            --project <project-root>
            --command <test-command-string>
            --expect <block|allow|available>
            [--handler-type <command|http|mcp_tool|prompt|agent>]
            [--evidence-root <path>]    (default runtime/validation/hook-probe)
            [--timeout <seconds>]       (default 60)
EOF
    exit 64
}

HOST=""
PROJECT=""
COMMAND=""
EXPECT=""
HANDLER_TYPE="command"
EVIDENCE_ROOT=""
TIMEOUT=60

while [ $# -gt 0 ]; do
    case "$1" in
        --host) HOST="$2"; shift 2;;
        --project) PROJECT="$2"; shift 2;;
        --command) COMMAND="$2"; shift 2;;
        --expect) EXPECT="$2"; shift 2;;
        --handler-type) HANDLER_TYPE="$2"; shift 2;;
        --evidence-root) EVIDENCE_ROOT="$2"; shift 2;;
        --timeout) TIMEOUT="$2"; shift 2;;
        -h|--help) usage;;
        *) echo "prober: unknown arg $1" 1>&2; usage;;
    esac
done

case "$HOST" in claude|codex|gemini) ;; *) usage;; esac
case "$EXPECT" in block|allow|available) ;; *) usage;; esac
case "$HANDLER_TYPE" in command|http|mcp_tool|prompt|agent) ;; *) usage;; esac
[ -n "$PROJECT" ] || usage
[ -n "$COMMAND" ] || usage

if [ ! -d "$PROJECT" ]; then
    echo "prober: project root not found: $PROJECT" 1>&2
    exit 64
fi

# Locate the factory root for the default evidence dir (two levels up from this script).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FACTORY_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

if [ -z "$EVIDENCE_ROOT" ]; then
    EVIDENCE_ROOT="$FACTORY_ROOT/runtime/validation/hook-probe"
fi

STAMP="$(date -u +%Y%m%d-%H%M%S)"
EVIDENCE_DIR="$EVIDENCE_ROOT/$STAMP/$HOST"
mkdir -p "$EVIDENCE_DIR"

STDOUT_FILE="$EVIDENCE_DIR/stdout.txt"
STDERR_FILE="$EVIDENCE_DIR/stderr.txt"
META_FILE="$EVIDENCE_DIR/meta.json"

emit_json() {
    # $1 verdict (pass|fail|escalated)
    # $2 observed (block|allow|silent_pass|sandbox_blocked|trust_blocked|cli_missing|error)
    # $3 reason (string, may be empty)
    local verdict="$1"
    local observed="$2"
    local reason="$3"
    # Use python for safe JSON escaping; fall back to a hand-built string if python is missing.
    if command -v python3 >/dev/null 2>&1; then
        python3 - <<PY
import json, os
print(json.dumps({
    "host": os.environ["P_HOST"],
    "handler_type": os.environ["P_HANDLER_TYPE"],
    "command": os.environ["P_COMMAND"],
    "expected": os.environ["P_EXPECT"],
    "observed": os.environ["P_OBSERVED"],
    "verdict": os.environ["P_VERDICT"],
    "evidence_path": os.environ["P_EVIDENCE"],
    "reason": os.environ["P_REASON"],
}))
PY
    else
        # Best-effort raw JSON; assumes no embedded quotes in inputs we control.
        printf '{"host":"%s","handler_type":"%s","command":"%s","expected":"%s","observed":"%s","verdict":"%s","evidence_path":"%s","reason":"%s"}\n' \
            "$HOST" "$HANDLER_TYPE" "$COMMAND" "$EXPECT" "$observed" "$verdict" "$EVIDENCE_DIR" "$reason"
    fi
}

run_handler_mode_probe() {
    case "$HANDLER_TYPE" in
        http)
            printf '{"handler_type":"http","sentinel":"available"}\n' >"$EVIDENCE_DIR/http-sentinel.json"
            echo "handler_mode_available"
            ;;
        mcp_tool)
            echo "no_mcp_test_server_available"
            ;;
        prompt|agent)
            echo "headless_handler_probe_unavailable"
            ;;
    esac
}

run_claude() {
    if ! command -v claude >/dev/null 2>&1; then
        echo "prober: claude CLI not on PATH" >"$STDERR_FILE"
        P_VERDICT=escalated P_OBSERVED=cli_missing P_REASON="claude CLI not installed" \
        P_HOST="$HOST" P_HANDLER_TYPE="$HANDLER_TYPE" P_COMMAND="$COMMAND" P_EXPECT="$EXPECT" P_EVIDENCE="$EVIDENCE_DIR" \
        emit_json "escalated" "cli_missing" "claude CLI not installed"
        return 2
    fi
    # Claude's headless `-p` mode has a fundamental constraint: with
    # --dangerously-skip-permissions the entire pre-tool hook system is
    # bypassed (silently turning every probe into observed=allow), and
    # without it the CLI waits on an interactive permission prompt that
    # never arrives in headless mode. Neither path is a useful live
    # invocation probe. We attempt the no-skip path with a short timeout
    # and treat hangs / permission-denied refusals as `escalated`, mirroring
    # the Codex sandbox-blocked doctrine.
    local prompt="Use the Bash tool to run exactly this command: $COMMAND. Report only ===BLOCKED=== if the tool call was blocked by a hook, or ===ALLOWED=== if it ran. Do not retry."
    local short_timeout=30
    if [ "$TIMEOUT" -lt "$short_timeout" ]; then
        short_timeout="$TIMEOUT"
    fi
    timeout "$short_timeout" claude -p "$prompt" --output-format text --permission-mode default \
        >"$STDOUT_FILE" 2>"$STDERR_FILE"
    local rc=$?
    if [ $rc -eq 124 ]; then
        # Hung waiting on permission prompt.
        echo "headless_permission_constraint"
        return 0
    fi
    if grep -qiE "permission.*denied|requires.*approval|cannot.*run.*without.*approval" "$STDOUT_FILE" "$STDERR_FILE" 2>/dev/null; then
        echo "headless_permission_constraint"
        return 0
    fi
    if grep -q "===BLOCKED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "block"
    elif grep -q "===ALLOWED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "allow"
    else
        echo "error"
    fi
}

run_codex() {
    if ! command -v codex >/dev/null 2>&1; then
        echo "prober: codex CLI not on PATH" >"$STDERR_FILE"
        P_VERDICT=escalated P_OBSERVED=cli_missing P_REASON="codex CLI not installed" \
        P_HOST="$HOST" P_HANDLER_TYPE="$HANDLER_TYPE" P_COMMAND="$COMMAND" P_EXPECT="$EXPECT" P_EVIDENCE="$EVIDENCE_DIR" \
        emit_json "escalated" "cli_missing" "codex CLI not installed"
        return 2
    fi
    local prompt="Use your shell tool to run exactly: $COMMAND. Then output only ===BLOCKED=== if a hook blocked it, or ===ALLOWED=== if it ran. Do not retry."
    ( cd "$PROJECT" && timeout "$TIMEOUT" codex exec "$prompt" ) \
        >"$STDOUT_FILE" 2>"$STDERR_FILE"
    if grep -qE "bwrap: |needs access to create user namespaces|shell tool failed before command execution|shell tool is blocked by the sandbox" "$STDERR_FILE" "$STDOUT_FILE" 2>/dev/null; then
        echo "sandbox_blocked"
        return 0
    fi
    if grep -q "===BLOCKED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "block"
    elif grep -q "===ALLOWED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "allow"
    else
        echo "error"
    fi
}

run_gemini() {
    if ! command -v gemini >/dev/null 2>&1; then
        echo "prober: gemini CLI not on PATH" >"$STDERR_FILE"
        P_VERDICT=escalated P_OBSERVED=cli_missing P_REASON="gemini CLI not installed" \
        P_HOST="$HOST" P_HANDLER_TYPE="$HANDLER_TYPE" P_COMMAND="$COMMAND" P_EXPECT="$EXPECT" P_EVIDENCE="$EVIDENCE_DIR" \
        emit_json "escalated" "cli_missing" "gemini CLI not installed"
        return 2
    fi
    local prompt="Use the run_shell_command tool to execute exactly: $COMMAND. Then output only ===BLOCKED=== if a hook blocked it, or ===ALLOWED=== if it ran. Do not retry."
    ( cd "$PROJECT" && timeout "$TIMEOUT" gemini -p "$prompt" ) \
        >"$STDOUT_FILE" 2>"$STDERR_FILE"
    if grep -qiE "workspace.*not.*trusted|trust.*required|trust.*folder" "$STDERR_FILE" "$STDOUT_FILE" 2>/dev/null; then
        echo "trust_blocked"
        return 0
    fi
    if grep -q "===BLOCKED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "block"
    elif grep -q "===ALLOWED===" "$STDOUT_FILE" 2>/dev/null; then
        echo "allow"
    else
        echo "error"
    fi
}

if [ "$HANDLER_TYPE" = "command" ]; then
    case "$HOST" in
        claude) OBSERVED="$(run_claude)";;
        codex)  OBSERVED="$(run_codex)";;
        gemini) OBSERVED="$(run_gemini)";;
    esac
else
    OBSERVED="$(run_handler_mode_probe)"
fi

# Persist meta record (one line per probe).
if command -v python3 >/dev/null 2>&1; then
    python3 - <<PY > "$META_FILE"
import json, time
print(json.dumps({
    "host": "$HOST",
    "handler_type": "$HANDLER_TYPE",
    "project": "$PROJECT",
    "command": "$COMMAND",
    "expected": "$EXPECT",
    "observed": "$OBSERVED",
    "stamp": "$STAMP",
    "ts": time.time(),
}))
PY
fi

REASON=""
case "$OBSERVED" in
    block|allow)
        if [ "$OBSERVED" = "$EXPECT" ]; then
            VERDICT=pass
        else
            VERDICT=fail
            if [ "$EXPECT" = "block" ] && [ "$OBSERVED" = "allow" ]; then
                REASON="silent_pass: hook did not fire on $HOST"
                OBSERVED=silent_pass
            else
                REASON="observed=$OBSERVED but expected=$EXPECT"
            fi
        fi
        ;;
    handler_mode_available)
        if [ "$EXPECT" = "available" ]; then
            VERDICT=pass
            REASON=""
        else
            VERDICT=fail
            REASON="handler mode available but expected=$EXPECT"
        fi
        ;;
    sandbox_blocked|trust_blocked|cli_missing|headless_permission_constraint|no_mcp_test_server_available|headless_handler_probe_unavailable)
        VERDICT=escalated
        REASON="$OBSERVED"
        ;;
    *)
        VERDICT=fail
        REASON="probe could not determine block/allow; check $STDOUT_FILE / $STDERR_FILE"
        ;;
esac

P_HOST="$HOST" P_HANDLER_TYPE="$HANDLER_TYPE" P_COMMAND="$COMMAND" P_EXPECT="$EXPECT" \
P_OBSERVED="$OBSERVED" P_VERDICT="$VERDICT" \
P_EVIDENCE="$EVIDENCE_DIR" P_REASON="$REASON" \
emit_json "$VERDICT" "$OBSERVED" "$REASON"

# Append to log (best-effort).
LOG_FILE="$EVIDENCE_ROOT/log.jsonl"
mkdir -p "$EVIDENCE_ROOT"
{
    if command -v python3 >/dev/null 2>&1; then
        python3 - <<PY
import json, time
print(json.dumps({
    "ts": time.time(),
    "stamp": "$STAMP",
    "host": "$HOST",
    "handler_type": "$HANDLER_TYPE",
    "command": "$COMMAND",
    "expected": "$EXPECT",
    "observed": "$OBSERVED",
    "verdict": "$VERDICT",
    "reason": "$REASON",
    "evidence": "$EVIDENCE_DIR",
}))
PY
    fi
} >> "$LOG_FILE" 2>/dev/null

case "$VERDICT" in
    pass) exit 0;;
    fail) exit 1;;
    escalated) exit 2;;
esac

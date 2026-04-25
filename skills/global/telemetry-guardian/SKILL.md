---
name: telemetry-guardian
description: Use when configuring or invoking the universal pre-tool-execution guardrail that intercepts destructive shell commands across Claude, Codex, and Gemini. Blocks --no-verify, force-push-to-main, wildcard home deletion, and similar patterns before the tool call executes.
capability_class: expert
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Telemetry Guardian

Purpose: sit in front of every shell/tool invocation across all three hosts and refuse destructive patterns before they run. The factory compiles `policies/hooks.json` into each host's native pre-tool-use format and points the hook at `guardian.sh` in this skill directory.

## Hard Gates

1. **The guardian is not an agent, it is a veto.** It reads one tool invocation on stdin (JSON), returns one verdict on stdout (JSON), exits 0 to allow or 1 to block. It does not reason, it does not explain beyond a short reason string, and it does not write files.
2. **Deny list is explicit.** The script only blocks patterns that appear in its matcher list. Novel destructive invocations will pass through until the deny list is updated. Err toward blocking; allow explicit human override via `AGENT_FORGE_GUARDIAN=off`.
3. **Opt-out must be explicit and logged.** When `AGENT_FORGE_GUARDIAN=off` is set, the guardian allows and writes one line to `~/.agent-forge/guardian.log` so the bypass is auditable.
4. **No network calls.** Guardian evaluates locally. It never phones home, never writes to external endpoints, and never caches invocations.
5. **Fast.** Guardian must complete in well under its 5-second timeout. Complex regexes should be avoided; the deny list is fixed-string or simple `grep -E`.

## Current deny list

Block the invocation if the command string matches any of:

- `--no-verify` — bypassing pre-commit hooks
- `--no-gpg-sign` or `-c commit.gpgsign=false` — bypassing signature
- `git push ... --force` or `--force-with-lease` into `main`/`master`/`develop`
- `git reset --hard` against a non-current branch
- `rm -rf $HOME`, `rm -rf ~`, `rm -rf /`, `rm -rf /*` — wildcard root/home deletion
- `terraform destroy` without `-target`
- `dd of=/dev/sda` or similar whole-disk writes
- `chmod -R 777 ~` — permissions nuke

Matchers are simple fixed strings or short `grep -E` patterns. Adjust the list inside `guardian.sh`.

## Output contract

stdin (JSON, one line): `{"tool": "Bash", "command": "git commit --no-verify"}` (shape may vary across hosts — guardian reads whatever JSON arrives and looks for a `.command`/`.tool_input.command`/`.input.command` field, falling back to raw stdin text).

stdout (JSON): `{"verdict": "allow" | "block", "reason": "short human-readable", "matched": "<pattern>"}`

Exit 0 → allow. Exit 1 → block. Exit 2 → guardian error (caller should treat as allow-with-warning; never block because the guardian itself is broken).

## Opt-out

`export AGENT_FORGE_GUARDIAN=off` in the current shell. This logs one line to `~/.agent-forge/guardian.log` with the timestamp and the invocation that would have been evaluated, then the guardian exits 0.

## Testing the guardian

```sh
echo '{"tool":"Bash","command":"git commit --no-verify"}' | bash skills/global/telemetry-guardian/guardian.sh
# expected: stdout JSON with verdict=block, matched=--no-verify; exit 1

echo '{"tool":"Bash","command":"ls -la"}' | bash skills/global/telemetry-guardian/guardian.sh
# expected: verdict=allow; exit 0
```

## Non-goals

- Not a replacement for `code-review-doctrine`. The guardian is a pre-execution stop; review is a post-authoring read.
- Not a sandbox. It does not contain the tool; it only decides to run it.
- Not an audit log for normal traffic. It only logs bypasses (`AGENT_FORGE_GUARDIAN=off`) and blocks.
- Not a decision tree for contextual judgement. If a command is ambiguous, fail-safe (allow) and let higher-level skills catch it — the guardian exists to stop the obviously-wrong.

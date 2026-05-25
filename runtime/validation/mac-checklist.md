# macOS Manual Smoke + Demo Checklist

Date refreshed: 2026-05-25 (post-NRC-ship; HEAD `95953fe`)
Bundle under test: `agent-forge-suitcase-20260525-153017`

## Part 1 — Fresh-host smoke test

Run this on a fresh or clean macOS user profile when a Mac is available. The bundle is MacPorts-only on macOS (Homebrew is intentionally not supported).

1. Transfer `exports/agent-forge-suitcase-20260525-153017.tar.gz` to the Mac.

2. Unpack and deploy:

   ```bash
   tar -xzf agent-forge-suitcase-20260525-153017.tar.gz
   cd agent-forge-suitcase-20260525-153017
   ./_agent_forge/scripts/deploy-and-bootstrap.sh
   ```

3. Open a new terminal so any PATH changes are visible.

4. Verify factory health:

   ```bash
   cd ~/Projects/_agent_forge
   python3 scripts/verify-agent-forge.py
   ```

   Expected: exit 0 with no `[FAIL]` lines.

5. If a governed project exists, run the triad runtime gate:

   ```bash
   python3 scripts/validate-triad-runtime.py --project <project-name>
   ```

6. Acceptance gate: in Claude Code under any `~/Projects/<name>` directory, run `/onboarding-guide` and confirm Beat 0 renders **inline in the chat** (not only as terminal output from a subprocess).

7. Record outputs and screenshots under `runtime/validation/mac-2026-05-25/` before promoting `validation-matrix.json` `mac.pass` from `null` to `true`.

## Part 2 — Demo path (for boss walkthrough)

Run after Part 1 passes. Each step is one or two minutes.

1. Open Claude Code in any project under `~/Projects/` (use `my-first-app` if you bootstrapped one in step 5).

2. Type `/onboarding-guide`. Eight inline beats render in the chat. Two short prompts (experience level, role). Read-only.

3. Linger on the two "why this exists" moments:
   - **Beat 3 — the cross-host translation table.** Same concept named differently across Claude, Codex, Gemini. The factory translates them.
   - **Beat 5.5 — the cross-host handoff.** Claude writes the plan to `docs/plans/<branch>.md` + pins a pointer in `MEMORY.md`. Switch to Codex; Codex reads `MEMORY.md` on session start, opens the plan, picks up.

4. In a real terminal (any directory), demonstrate the seatbelt:

   ```bash
   git push --force origin main
   ```

   The `telemetry-guardian` hook intercepts the command before it reaches the shell and refuses it by name. To bypass (logged to `~/.agent-forge/guardian.log`):

   ```bash
   AGENT_FORGE_GUARDIAN=off git push --force origin main
   ```

5. (Optional) Show the same `/onboarding-guide` slash command working in Codex and Gemini if they are installed. Identical canonical skill, three host-native renderings.

## Part 3 — If anything goes red

Run the read-only audit and follow the printed fix command:

```bash
python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py check
```

Six probes, plain-English verdicts. Yellow on missing host CLIs is expected for a single-CLI install; red on factory presence or verifier exit means re-run `deploy-and-bootstrap.sh`.

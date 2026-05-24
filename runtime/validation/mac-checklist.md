# macOS Manual Smoke Checklist

Date prepared: 2026-05-23

Run this on a fresh or clean macOS user profile when a Mac is available.

1. Transfer `exports/agent-forge-suitcase-20260523-validation.tar.gz` to the Mac.
2. Run:

   ```bash
   tar -xzf agent-forge-suitcase-20260523-validation.tar.gz
   cd agent-forge-suitcase-20260523-validation
   ./_agent_forge/scripts/deploy-and-bootstrap.sh
   ```

3. Open a new terminal so PATH changes are visible.
4. Run:

   ```bash
   cd ~/Projects/_agent_forge
   python3 scripts/verify-agent-forge.py
   ```

5. If a governed project exists, run:

   ```bash
   python3 scripts/validate-triad-runtime.py --project <project-name>
   ```

6. In Claude Code, run `/onboarding-guide` and confirm Beat 0 renders inline in chat.
7. Record screenshots and command output under `runtime/validation/mac-2026-05-23/` before promoting this checklist to a passed entry.

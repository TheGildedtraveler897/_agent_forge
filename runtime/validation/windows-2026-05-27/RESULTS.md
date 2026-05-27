# Windows VM Validation Results — 2026-05-27

- **Host:** `win11` (Windows build 26200), native PowerShell 5.1, **no WSL**.
- **VM:** 192.168.122.127 (libvirt NAT), driven over OpenSSH (cmd.exe shell).
- **Bundle:** `agent-forge-suitcase-20260527-135346` (branch `feat/auto-provision-prereqs`).
- **Deploy root:** `C:\af3`; factory landed at `C:\Users\anoop\Projects\_agent_forge`.

## What was proven (real host)

| Gate | Result | Evidence |
|---|---|---|
| ZIP unblock + extract + unblock-tree | PASS | "Unblocking… / Extracting… / Unblocking extracted tree…" |
| `-AutoProvision` winget install + PATH refresh | PASS | `Python resolver: …\Python312\python.exe (Python 3.12.10)` after a box that had only the Store alias stub |
| `deploy-factory.ps1` parses on PS 5.1 | PASS | Ran clean after the ASCII-only fix (previously crashed on a corrupted em-dash) |
| `omni_factory` Claude sync (`.claude\skills\`) | PASS | "Claude sync complete" — symlink→copy fallback did not crash under WinError 1314 |
| `verify-agent-forge.py` | PASS (exit 0) | `VERIFY_EXIT=0` |
| `bootstrap-project.ps1` scaffold | PASS | demo project scaffolded (AGENTS/CLAUDE/GEMINI/docs) |
| `.claude\CLAUDE.md` symlink→managed-copy fallback | PASS | "Symbolic link failed (needs Administrator or Windows Developer Mode). Falling back to a managed file copy." |
| `projects.json` registration | PASS | "Added 'demo' to projects.json" |

## Remaining operator-confirmed gate

- `/onboarding-guide` Beat 0 inline render in Claude Code — interactive; cannot be
  driven over non-interactive SSH. Confirm in the demo (Beat 0 greeting + experience
  prompt render inline; tour says "eight" beats).

## Notes

- Two pre-existing bugs were caught and fixed only because of this live run:
  (1) `Resolve-Python` crashed on the Store python alias stub under EAP=Stop;
  (2) `.ps1` files contained non-ASCII (em-dash/box-drawing) that PowerShell 5.1
  misread without a BOM, breaking `deploy-factory.ps1` parsing. Both fixed; both
  guarded by tests.

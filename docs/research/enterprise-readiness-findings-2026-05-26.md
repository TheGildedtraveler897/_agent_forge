# Enterprise Deployment-Readiness Audit — Findings Report

Date: 2026-05-26
Branch: `audit/enterprise-readiness-2026-05-26` (off `master`, merged `rc/2026-05-26`)
Scope: full deployment-readiness audit + repair pass for the enterprise pivot
(Debian/Ubuntu, RHEL-family, macOS MacPorts-only, native Windows no-WSL).

## Findings, ordered by severity (all fixed unless noted)

### Enterprise-blocking

1. **No Red Hat / RHEL / Fedora support.** `bootstrap-workstation.sh` rejected all
   non-Debian/Ubuntu Linux. → **Fixed** (Phase 2): `dnf`/`yum` path with EPEL guard
   (ripgrep/jq) and AppStream-first Node. Runtime proof **host-gated** (TECH_DEBT).
2. **README skill tree drifted from disk.** 4 ghost skills listed
   (`code-review-doctrine`, `quality-gate`, `quick-task-runner`, `workstream-manager`),
   2 real ones missing (`e2e-qa-tester`, `paranoid-reviewer`). → **Fixed** (Phase 1):
   tree synced to the 30 skills on disk.

### High

3. **`omni_factory.ensure_symlink` hard-fails on native Windows** (WinError 1314),
   breaking `.claude/skills/` delivery and any Windows bootstrap auto-sync. → **Fixed**
   (Phase 4): `os.name=='nt'` copy fallback with managed-copy sentinel + idempotent
   refresh + cleanup parity. Real-Windows proof host-gated.
4. **`deploy-factory.sh` dropped `--codex-home`** (forwarded only `--target`). → **Fixed**
   (Phase 1).
5. **`deploy-and-bootstrap.sh` rejected `--gemini-home`**; `.ps1` exposed no home flags.
   → **Fixed** (Phase 1 + Phase 3).
6. **`.forge_state/*.log` git-tracked**, dirtying every working tree on each distiller
   run. → **Fixed** (Phase 0): gitignored + untracked (kept on disk).
7. **Windows Python 3.10+ advertised but never enforced** in any `.ps1`. → **Fixed**
   (Phase 3): `Resolve-Python` in `_psutil.ps1` parses and gates the version.
8. **Triad validator crashed on a CLI timeout** (`str + bytes` in the `TimeoutExpired`
   handler). → **Fixed** (Phase 7): bytes-safe normalization; now records 124/timeout
   and falls back to filesystem evidence.

### Medium

9. **PowerShell was a reduced flow** (no interactive CONOPS, `-Existing`,
   `-WithLocalSkills`; wrong hardcoded `@../CLAUDE.md`; no symlink fallback; `.sh`/`.ps1`
   projects.json divergence). → **Fixed** (Phase 3): full parity + shared `_psutil.ps1`;
   both scripts register via one Python snippet for byte-identical output.
10. **Proxy/TLS not documented for enterprise networks.** → **Fixed** (Phase 5): scripts
    preserve proxy/CA env (`sudo -E`); corporate pre-flight documented; no hard-coded values.
11. **Onboarding "seven vs eight" beat drift.** → **Fixed** (Phase 1): synced to "eight".
12. **`EXPLAINERS.md` mis-described telemetry-guardian as POSIX-shell-primary** (it is
    Python-first). → **Fixed** (Phase 1).
13. **`TECH_DEBT.md` was an empty stub.** → **Fixed** (Phase 1 + 6): seeded with real
    host-gated and deferred items.

### Verified intentional (no change)

- Codex `model_reasoning_effort` / per-agent `mcp_servers` not rendered — doctrine-deferred;
  tracked in TECH_DEBT.
- `portability-audit` (command alias) vs `portability-auditor` (folder/name) — intentional
  renderer metadata; `name` matches the directory per spec.
- `paranoid-reviewer` is the single canonical reviewer (supersedes legacy review flows).
- All 30 skills comply with agentskills.io (name==dir, <500 lines). Local-extension
  frontmatter stays top-level; `metadata.agent_forge.*` migration tracked in TECH_DEBT.

## Validation transcript (Linux dev host, 2026-05-26)

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Branch discipline | `enforce-branch-discipline.sh` | exit 0 |
| 2 | Verifier | `verify-agent-forge.py` | exit 0 |
| 3 | Unit tests | `python3 -m unittest discover -s tests` | 97 pass (was 71; +26) |
| 4 | Shell syntax | `bash -n scripts/*.sh` | all 9 parse |
| 5 | Python compile | `py_compile` all tracked `.py` | all compile |
| 6 | JSON parse | projects/global-mcp/validation-matrix/policies/teams | all ok |
| 7 | Registry sync | `omni_factory.py render-registry` vs `registry.json` | in sync |
| 8 | Export smoke | `factory-export.sh --mode onboarding` | clean COI, no cache/bytecode/.venv, AGENTS.md + `_psutil.ps1` shipped, Windows sidecar present |
| 9 | Triad runtime | bootstrap ephemeral `_audit_probe` + `validate-triad-runtime.py` | bootstrap/sync/registration/symlink ✓; validator completes (bug fixed); claude PASS via CLI; codex/gemini filesystem fallback (fresh-probe bridge gap); probe cleaned up |

Environment note: `gemini skills list --all` hung ~60s in this environment (CLI
behavior, not factory code); the validator now times out gracefully.

## Proven vs. structurally-checked vs. needs-host

- **Proven (Linux):** apt path, verifier, full unit suite, registry sync, export smoke
  (COI/cache/sidecar), bootstrap+sync+registration+POSIX symlink, triad validator runs.
- **Structurally checked only:** RHEL/dnf path (bash -n + static + DNF_BIN subshell);
  Windows PowerShell parity + symlink copy-fallback (static text tests + monkeypatch).
- **Needs a real host:** RHEL EPEL/AppStream/npm-prefix (RHEL/Rocky/Alma/Fedora VM);
  Windows symlink-denial + winget/npm/py-launcher + projects.json round-trip (Windows VM);
  macOS `/onboarding-guide` Beat 0 inline render. All tracked in `docs/TECH_DEBT.md` and
  `docs/SUPPORTED_PLATFORMS.md`.

## Deliverables produced

- Code/test fixes across Phases 0-7 (8 commits on the audit branch).
- This findings report (severity-ordered).
- Skill-retention matrix: `docs/research/skill-retention-matrix-2026-05-26.md`.
- OS support matrix: `docs/SUPPORTED_PLATFORMS.md`.
- 6 append-first lessons in `docs/LESSONS_LEARNED.md`; TECH_DEBT seeded.

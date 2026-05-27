# Agent Forge Handoff

This file is the rolling operator handoff log. The `sprint-harvester` skill appends new sprint summaries here at the end of each sprint. The `handoff-archiver` skill compacts older sprints into `docs/archive/SPRINTS.md` once the file grows past the threshold defined in `policies/distillation.json`. Wisdom is preserved verbatim across both files.

## What Changed

### Sprint: Opt-in Auto-Provisioning (2026-05-27)

- Branch: `feat/auto-provision-prereqs`. Follow-on to the enterprise audit, triggered by a live Windows VM deploy where the box had only the Microsoft Store `python3` alias stub (no real Python).
- **Bug fix:** `Resolve-Python` skips `*\WindowsApps\*` alias stubs and probes defensively (the stub's stderr under `EAP=Stop` was crashing the resolver with `NativeCommandError`).
- **Feature (opt-in):** `-AutoProvision` (Windows) / `--auto-provision` (bash) on the deploy wrappers. `_psutil.ps1` centralizes `Install-WingetPackage`/`Get-NodeMajor` and adds `Find-Python`, `Update-SessionPath`, `Invoke-PrerequisiteProvision` (winget Python 3.12 / Git / Node LTS), plus `Resolve-Python -AutoProvision`. Bash: `bootstrap-workstation.sh --base-deps-only` (+ python3 in apt/dnf base lists; macOS provisions MacPorts python only if absent); `deploy-and-bootstrap.sh --auto-provision` runs it before deploy. Default stays detect-and-fail-clean (locked-down hosts never force-installed).
- **Validation:** 106 unit tests (+9), verifier exit 0, bash -n clean, registry in sync. Live Windows VM run: see Current State.

### Sprint: Enterprise Deployment-Readiness Audit (2026-05-26)

- Branch: `audit/enterprise-readiness-2026-05-26` (off `master`, merged `rc/2026-05-26` to carry the MacPorts + distiller-verification fixes). Plan: `~/.claude/plans/memoized-plotting-volcano.md`. Findings: `docs/research/enterprise-readiness-findings-2026-05-26.md`.
- **Enterprise pivot** (homelab → enterprise). Operator decisions: implement RHEL/dnf now; full PowerShell parity; low-risk proxy/TLS passthrough + document the rest.
- **RHEL-family bootstrap** (`bootstrap-workstation.sh`): dnf/yum path mirroring apt — `detect_platform` 3-arm chain + `DNF_BIN`, EPEL guard for ripgrep/jq (non-Fedora), AppStream `nodejs:20` then consent-gated NodeSource rpm. New `tests/test_bootstrap_workstation_dnf.py` (14 static tests).
- **Full Windows PowerShell parity:** new `scripts/_psutil.ps1` (Resolve-Python 3.10+ gate, Get-RelativePath, New-ManagedLink symlink→copy fallback, Test-Command); `bootstrap-project.ps1` interactive CONOPS / `-Existing` / `-WithLocalSkills` / relpath fix / AGENTS.override stub; `bootstrap-workstation.ps1` winget+npm install parity; `deploy-and-bootstrap.ps1` home flags; both `bootstrap-project.{sh,ps1}` register projects.json via one Python snippet.
- **Windows sync-layer fix** (`omni_factory.py`): `ensure_symlink` falls back to a managed copy on `os.name=='nt'` OSError (WinError 1314); cleanup prunes managed copies. New `tests/test_symlink_fallback.py`.
- **Correctness:** deploy-factory.sh `--codex-home` forwarding; deploy-and-bootstrap.sh `--gemini-home`; README skill tree synced to 30 on-disk skills (dropped 4 ghosts, added e2e-qa-tester + paranoid-reviewer); beat count 7→8 stragglers; EXPLAINERS telemetry-guardian (Python-first); `.forge_state/*.log` untracked; triad validator timeout-handler str+bytes crash.
- **Docs:** `docs/SUPPORTED_PLATFORMS.md` (OS matrix w/ proven/structural/needs-host), WORKSTATION_BOOTSTRAP corporate proxy/TLS section, TECH_DEBT seeded, 6 append-first lessons, skill-retention matrix.
- **Validation (Linux):** verifier exit 0; 97 unit tests pass (was 71); bash -n all 9 scripts; py_compile all .py; JSON parse all configs; registry in sync; export smoke clean (COI/cache/sidecar); ephemeral-probe bootstrap+sync+registration+symlink ✓ and triad validator runs (claude PASS via CLI).

### Sprint: Onboarding Audit + NRC Ship Prep (2026-05-24)

- Branches: `fix/onboarding-guide-terminology-drift` (T1) + `feat/onboarding-multi-agent-story` (T2+T3)
- **T1 — Factual fixes:** Beat 6 install table (3 broken URLs, wrong Claude package name), citation errors (TACL 2023, arXiv venue), host-dirs misframing (.agents/skills/ is agentskills.io standard, not "legacy"), Codex demo ($onboarding-guide invocation syntax).
- **T2 — Multi-agent value-prop:** README "Multi-Agent Workflows" section, Beat 5.5 "The Cross-Host Handoff", DEMO_PATH Step 5b (Claude→Codex→Gemini plan handoff), new docs/MULTI_AGENT_EXAMPLES.md (GSD and research team walkthroughs), reframed docs to reflect "unified memory layer (native on Claude, sidecar bridges on Codex/Gemini)".
- **T3 — Polish quick-wins:** Beat count sync 7→8 across BUNDLE_README/QUICKSTART/DEMO_PATH, single-CLI fallback sentence, deploy-and-bootstrap.ps1 header comment.
- **Deferred to post-NRC:** T3-A MacPorts justification, T3-D Windows Python 3.10+ version check, T3-E npm pre-flight, T3-G EXPLAINERS sidecar naming.
- **Deferred (needs spec):** feat/gsd-extraction-foundation (14 new skills).
- **Validation:** Structural verifier exits 0, all 71 unit tests pass, clean T1→T2 rebase, no stale 2026-05-22 dates.

### Sprint: SOTA 2026 Deep Refactor (2026-05-23)

- Branch: `feat/sota-2026-deep-refactor`
- Plan: `docs/plans/feat-sota-2026-deep-refactor.md`
- Latest task commit before integration: `f792a77` plus final validation/export artifact commit
- Windows ship-blocker: added `scripts/deploy-and-bootstrap.ps1`, `scripts/bootstrap-workstation.ps1`, recursive `Unblock-File` handling, bundle integrity checks, and Windows-first ZIP docs.
- Continuity: added cursor checkpoints, task completion commit recording, memory bridge validation, and outbound Active Cursor State summaries for peer-agent resume.
- Policy/verifier hygiene: moved disabled hook examples to `docs/HOOK_EXAMPLES.md`, warned on empty `projects.json`, rejected legacy `hosts:` frontmatter, warned on stale plans/pointers, and clarified sandbox-skipped triad runtime outcomes.
- SOTA docs: added the 2026-05-23 deep audit delta, prompt-caching explainer, corrected MCP config divergence wording, and deduplicated CONOPS delivery surfaces.
- Validation: Linux verifier/unit/export evidence lives at `runtime/validation/linux-2026-05-23/`; Mac and Windows checklists are staged for operator-run smoke tests.

## Current State
The enterprise-readiness audit (`audit/enterprise-readiness-2026-05-26`, 9 commits on top of the prior `rc/2026-05-26` work) is **merged to `master` and pushed to `origin/master`**. Linux gates are green: verifier exit 0, 97 unit tests pass, registry in sync, export smoke clean. The factory now supports Debian/Ubuntu (apt), RHEL-family (dnf/yum), macOS (MacPorts-only), and native Windows (winget+npm + symlink-copy fallback). The release-candidate suitcase was exported from this merged state (newest bundle under `exports/`).

**Production baseline (NRC 2026-05-25):** Suitcase `agent-forge-suitcase-20260525-153017.*` (commit `95953fe`) — predates all audit fixes (RHEL, Windows symlink, deploy-flag, distiller-log). A re-cut RC + fresh suitcase supersedes it.

## Remaining Weaknesses
- **Windows runtime unproven** — full PowerShell parity + the `omni_factory` symlink→copy fallback are statically verified only. Run `runtime/validation/windows-2026-05-26.md` on a fresh native Windows VM; set `windows.pass` against captured evidence only.
- **RHEL runtime unproven** — dnf path is structurally verified only. Needs a RHEL/Rocky/Alma/Fedora host to confirm EPEL ripgrep/jq (+ CRB/PowerTools), `nodejs:20` AppStream, and whether `npm install -g` needs sudo on the dnf prefix.
- **macOS Beat 0 render** still unobserved; `mac.pass` stays null until seen.
- Environment note: `gemini skills list --all` hung ~60s during triad probing on the Linux dev host (CLI behavior; the validator now times out gracefully rather than crashing).
- All host-gated items tracked in `docs/TECH_DEBT.md` and `docs/SUPPORTED_PLATFORMS.md`.

## Next Evolution
Operator-gated: (1) run the RHEL and Windows host checklists, capture evidence, update `validation-matrix.json`; (2) re-cut the RC from this audit branch, regenerate the suitcase, push with approval; (3) schedule the deferred TECH_DEBT items (Codex `model_reasoning_effort` / per-agent `mcp_servers`, `metadata.agent_forge.*` frontmatter migration).

## Final Verdict
Audit merged to `master` and pushed; RC suitcase exported. Linux-side gates are green. RHEL and Windows are structurally complete but runtime-unproven — both remain host-gated and must pass `runtime/validation/windows-2026-05-26.md` (Windows) and a Rocky/Alma/RHEL run before the RC is treated as fully proven on those platforms. macOS Beat 0 render still unobserved.

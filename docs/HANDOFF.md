# Agent Forge Handoff

This file is the rolling operator handoff log. The `sprint-harvester` skill appends new sprint summaries here at the end of each sprint. The `handoff-archiver` skill compacts older sprints into `docs/archive/SPRINTS.md` once the file grows past the threshold defined in `policies/distillation.json`. Wisdom is preserved verbatim across both files.

## What Changed

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
The NRC ship branches (T1 terminology-drift, T2 multi-agent-story) are merged to `master` and pushed to `origin/master` (HEAD `95953fe`). Linux structural validation is green: verifier exit 0, 71 unit tests pass, COI grep clean. The current production onboarding suitcase is `exports/agent-forge-suitcase-20260525-153017.*` (source commit `95953fe`). macOS smoke test ran on NRC055206R (2026-05-25): all three CLIs confirmed (Claude Code 2.1.150, Codex 0.133.0, Gemini CLI 0.43.0) and `bootstrap-project.sh` passed. MacPorts npm EACCES root cause identified and fixed in branch `fix/macports-npm-sudo` (`npm_global_install()` helper in `scripts/bootstrap-workstation.sh`).

## Remaining Weaknesses
- Windows VM smoke test still needs to be run by the operator with `runtime/validation/windows-2026-05-23.md`.
- macOS: CLIs and project bootstrap confirmed. Fix for MacPorts npm EACCES applied (`fix/macports-npm-sudo`). Remaining gap: Beat 0 inline render in Claude Code not yet tested on Mac; `mac.pass` in `validation-matrix.json` should be set to `true` after that step.
- `scripts/validate-triad-runtime.py --project <name>` was skipped because `projects.json` has no governed projects. Run it after the first project is bootstrapped.

## Next Evolution
After the Windows VM passes the one-shot ZIP deploy, merge the branch, tag the ship artifact, and push with operator approval. Follow-on work should add active policy records for Gemini-only hook semantics and render Codex `model_reasoning_effort` / per-agent `mcp_servers` explicitly.

## Final Verdict
Linux-side ship gates are green. macOS CLIs and bootstrap confirmed; Beat 0 render is the final mac gate. Windows is structurally fixed but still requires the fresh-VM smoke test before the release tag should be treated as fully proven.

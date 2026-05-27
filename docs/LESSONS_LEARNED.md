# Lessons Learned

This file is the append-first knowledge anchor for Agent Forge. Validated workarounds, host quirks, and durable lessons land here before any change to canonical doctrine.

## Rules

- Add normalized entries here before changing durable doctrine.
- Do not overwrite `AGENTS.md` or `docs/CONOPS.md` as part of harvesting.
- Promote a lesson into doctrine only when it is durable, broad, and worth loading by default.
- Keep secrets, local-only residue, and one-off operator trivia out of this ledger.
- Once an entry's `Status:` is `promoted` and its named doctrine reference resolves on disk, the `lesson-distiller` skill is eligible to archive it to `docs/archive/LESSONS_PROMOTED.md`, leaving a one-line index pointer in this file.

## Entry Template

### <date> - <short title>

- `Date:` YYYY-MM-DD
- `Context:` where the issue appeared and why it mattered
- `Lesson:` the reusable learning
- `Architectural Decision:` what Agent Forge should do going forward
- `Evidence:` changed files, commands, or validation artifacts that proved it
- `Promotion Target:` doc or capability to update later, if any
- `Status:` `active`, `promoted`, or `superseded`

## Entries

### 2026-05-23 - Windows ZIP deploy must unblock before extraction

- `Date:` 2026-05-23
- `Context:` Fresh Windows VM smoke testing showed Explorer's "Extract All" path could leave an incomplete `_agent_forge\` tree after a transferred ZIP, causing `deploy-factory.ps1` to fail because docs, policies, and top-level files were missing.
- `Lesson:` Native Windows suitcase deploys need a PowerShell entry point that calls `Unblock-File` on the ZIP before extraction, warns on long paths, validates required top-level contents, recursively unblocks the extracted tree, and only then runs the deploy script.
- `Architectural Decision:` Ship `scripts/deploy-and-bootstrap.ps1` as the Windows-first entry point and generate a matching sidecar script next to every ZIP export. Treat Explorer extraction as a fallback, not the runbook path.
- `Evidence:` `scripts/deploy-and-bootstrap.ps1`, `scripts/deploy-factory.ps1`, `scripts/factory-export.sh`, `BUNDLE_README.md`, `docs/QUICKSTART.md`, `docs/DEMO_PATH.md`, `tests/test_windows_powershell_scripts.py`, and `runtime/validation/windows-2026-05-23.md`.
- `Promotion Target:` Windows deployment runbook (`docs/QUICKSTART.md`, `BUNDLE_README.md`).
- `Status:` promoted

### 2026-05-23 - Codex subagent TOML details need explicit renderer coverage

- `Date:` 2026-05-23
- `Context:` The deep SOTA audit re-checked current Codex subagent docs and confirmed `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` are documented as supported custom-agent TOML fields.
- `Lesson:` "Codex uses TOML" is not enough detail for future renderer work. The factory should document and eventually render the fields that control reasoning effort and per-agent MCP inheritance, instead of relying on Claude/Gemini-style frontmatter assumptions.
- `Architectural Decision:` Keep current flat TOML rendering for now, but track explicit Codex field coverage as follow-on work before claiming full 2026 Codex parity.
- `Evidence:` `docs/SOTA_2026_AUDIT.md` § 7.3 and `skills/global/onboarding-guide/EXPLAINERS.md` state-of-the-field refresh.
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Codex subagent rendering.
- `Status:` active

### 2026-05-23 - Prompt caching is a SOTA cost doctrine, not optional trivia

- `Date:` 2026-05-23
- `Context:` The deeper 2026 SOTA pass found Anthropic's prompt-caching guidance was absent from Agent Forge docs even though the factory already invests heavily in progressive disclosure and stable doctrine files.
- `Lesson:` Long-context agent systems should structure stable prefixes deliberately: tools, system/developer instructions, and durable context before per-turn data. Timestamps, IDs, cursor snippets, and other volatile material near the top destroy cache reuse.
- `Architectural Decision:` Treat stable-prefix ordering as a design rule for future API harnesses, renderer output, and memory summaries. Keep volatile continuity state later in prompts or host-local sidecars.
- `Evidence:` `docs/SOTA_2026_AUDIT.md` § 7.5, `skills/global/onboarding-guide/EXPLAINERS.md` `prompt-caching`, and `docs/research/sota-multi-agent-research-2026.md` § 4.
- `Promotion Target:` Future renderer/API-harness docs when those layers are introduced.
- `Status:` active

### 2026-05-23 - Export bundles must exclude Python bytecode caches

- `Date:` 2026-05-23
- `Context:` Final COI grep against the regenerated onboarding export returned binary matches inside `__pycache__/*.pyc` files. The matches came from machine-local path strings compiled into bytecode, not from source text.
- `Lesson:` `.gitignore` is not a packaging boundary. Export scripts must explicitly exclude runtime and cache artifacts, especially bytecode files that can embed absolute source paths.
- `Architectural Decision:` `scripts/factory-export.sh` now excludes `__pycache__`, `*.pyc`, `*.pyo`, and common Python tool caches before building `.tar.gz` and `.zip` artifacts.
- `Evidence:` `runtime/validation/linux-2026-05-23/export-coi-grep.*` after the fix, `scripts/factory-export.sh`, and `runtime/validation/linux-2026-05-23/bundle-check.md`.
- `Promotion Target:` Export script now enforces bytecode exclusion (`scripts/factory-export.sh`).
- `Status:` promoted

### 2026-05-22 - MCP stdio transport must not use sh-c on Windows

- `Date:` 2026-05-22
- `Context:` Windows VM readiness pass for NRC ship. `global-mcp.json` originally used `"command": "sh", "args": ["-c", "exec python3 \"$HOME/...\""]` to get shell-side `$HOME` expansion. Native Windows (no WSL) has no `sh`, so the MCP server would fail to start on coworker workstations.
- `Lesson:` The canonical authoring file (`global-mcp.json`) should not embed shell wrappers for env-var expansion. The renderer must expand `${HOME}` / `$HOME` / `~` at render time so the rendered host config contains an absolute path and a direct binary invocation. This decouples canonical portability (the file is operator-machine-agnostic) from rendered-config concreteness (the host config is operator-machine-specific by design).
- `Architectural Decision:` `omni_factory.normalize_mcp_server` now passes the transport dict through `_expand_transport_paths` which calls `os.path.expanduser` and `os.path.expandvars` on `command`, `args`, and `cwd`. Canonical files use `${HOME}/...` style placeholders. No `sh -c` wrappers permitted in the canonical.
- `Evidence:` `global-mcp.json:21-26` (canonical change), `scripts/omni_factory.py:_expand_transport_paths` (new helper), `scripts/verify-agent-forge.py` exits 0 after the change, `docs/plans/feat-windows-vm-readiness.md` (Track I plan).
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § MCP rendering rules — once the lesson holds across the first real Windows VM smoke test.
- `Status:` active

### 2026-05-22 - Line endings must be platform-specific by file type

- `Date:` 2026-05-22
- `Context:` Same Windows readiness pass. The repo had no `.gitattributes`, so a Windows operator cloning the repo could get auto-converted line endings that break `.sh` shebang parsing (LF expected) or generate spurious "no newline at end of file" warnings in PowerShell tooling (CRLF expected).
- `Lesson:` Cross-platform repos must explicitly state expected line endings per file type. Default `text=auto` behavior is not deterministic across operating systems.
- `Architectural Decision:` Added `.gitattributes` at repo root. POSIX scripts, Python, JSON, TOML, YAML, and Markdown enforce `eol=lf`. PowerShell, CMD, and BAT enforce `eol=crlf`. Archive types marked binary.
- `Evidence:` `.gitattributes` at repo root.
- `Promotion Target:` None — this is a one-time fix; the file documents the policy on disk.
- `Status:` active

### 2026-05-22 - Host-specific canonical hook events are intentional, not drift

- `Date:` 2026-05-22
- `Context:` SOTA 2026 drift audit (Track 4b of `feat-sota-2026-alignment`). The Phase 1 research found Gemini CLI fires `BeforeAgent`, `AfterAgent`, `BeforeToolSelection`, `AfterModel`, `BeforeModel` lifecycle events that have no Claude / Codex equivalent — they are semantically distinct lifecycle points, not just renames. Audit flagged this as a drift risk: if the canonical schema only represents Claude/Codex's event set, authors cannot write hook records that fire on Gemini-only events.
- `Lesson:` Verification showed all five events were already wired into `scripts/omni_factory.py:_EVENT_ALIASES` by an earlier SOTA pass — `None` aliases for Claude and Codex, PascalCase native names for Gemini. The canonical schema represents the events; the renderer drops them silently for hosts whose alias is `None`. The asymmetric design is intentional: not every canonical event needs all-three coverage. Per-host depth wins over forced symmetry.
- `Architectural Decision:` Document the asymmetry explicitly so future contributors don't try to "fix" it. CONOPS § Hook Governance gains a bullet stating host-specific canonical events are explicitly allowed. `policies/hooks.json` top-level description gains a sentence naming the Gemini-only events as an example of the pattern.
- `Evidence:` `scripts/omni_factory.py:869-873` (Claude `None` aliases), `:909-913` (Codex `None` aliases), `:930-934` (Gemini native aliases). `docs/CONOPS.md` § Hook Governance (new bullet). `policies/hooks.json` description string (updated).
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Unified Hook Lifecycle — already references `_EVENT_ALIASES`; should explicitly list the Gemini-only events with a one-line "no Claude / Codex equivalent" note.
- `Status:` active

### 2026-05-22 - Codex subagents already render as TOML (verified non-drift)

- `Date:` 2026-05-22
- `Context:` SOTA 2026 drift audit (Track 4a of `feat-sota-2026-alignment`). The primary-source research agent inferred that Codex subagents require a `[agent]` TOML section based on Codex 2026 vendor docs, but did not read an actual rendered file. Audit flagged this as a potential drift surface to verify.
- `Lesson:` On verification, `omni_factory.py` already renders `.codex/agents/<skill>.toml` files with the required Codex schema (`agent_forge_managed = true`, top-level `name`, `description`, `sandbox_mode`, `developer_instructions`, and a `[[skills.config]]` table for the referenced `SKILL.md` path). The audit's `[agent]` section guess was a stylistic inference; flat top-level keys are also valid TOML and match Codex's documented expected schema. No drift.
- `Architectural Decision:` Keep the current renderer behavior. If Codex's vendor docs ever explicitly require a `[agent]` wrapper section, that's a deeper rewrite gated on primary-source confirmation; not warranted by inference.
- `Evidence:` `tomllib.load()` succeeds on every `.codex/agents/*.toml` rendered file across multiple governed projects on the verification machine. All files have the same five top-level keys (`agent_forge_managed`, `name`, `description`, `sandbox_mode`, `developer_instructions`) plus a `[[skills.config]]` table for the referenced `SKILL.md` path.
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Codex subagent rendering — document the actual schema so future contributors don't re-investigate.
- `Status:` active

### 2026-05-22 - Plan persistence layer survived its first multi-merge cycle

- `Date:` 2026-05-22
- `Context:` Track F (2026-05-22) introduced `docs/plans/<branch-slug>.md` plan persistence with status frontmatter and `branch-finisher` Step 5b archival on merge. Within the same day, three merges exercised the path: `feat/ship-prep`, `feat/onboarding-overhaul`, and (pending) `feat/windows-vm-readiness`. Each plan transitioned `awaiting-approval` → `approved` → `in-progress` → `completed` and archived to `docs/archive/PLANS_COMPLETED.md`.
- `Lesson:` The new layer is durable under real-world multi-track sprint pressure. The frontmatter status field plus the archive-on-merge contract is enough to let a peer agent re-ground from disk after a session glitch. No additional MCP tool, no policy schema, no validator extension was needed; the layer is pure project-governance convention.
- `Architectural Decision:` Treat plan persistence as the reference pattern for future agent-governance primitives that don't need host-native rendering. The five-step omni-factory pattern (policy + renderers + verifier + validator + skill) is reserved for primitives that are surfaced into host-native config; project-governance concerns get a lighter pattern.
- `Evidence:` `docs/archive/PLANS_COMPLETED.md` entries; commits in master: c5807bf (Track F implementation), c9732a6 (first persisted plan), and the subsequent merge archives.
- `Promotion Target:` Plan persistence doctrine (`docs/CONOPS.md`).
- `Status:` promoted

### 2026-05-24 - Onboarding audit Tier 3 Polish Items (Deferred Post-NRC)

- `Date:` 2026-05-24
- `Context:` Follow-up onboarding audit discovered six polish items across scripts, docs, and explanations. Three were quick wins (beat count sync, demo fallback, ps1 header). Three are heavier and require fresh spec work or host-specific testing (MacPorts rationale, Windows Python version check, npm pre-flight validation, EXPLAINERS vs Beat 5 sidecar specificity). NRC ship deadline is 2026-05-25; these were deferred to post-ship sprint.
- `Lesson:` Beat numbering and cross-doc consistency require careful sync when new beats are inserted mid-stream. Polish passes should include a sweep for "N beats" references across all doc files (BUNDLE_README, QUICKSTART, DEMO_PATH) to catch off-by-one discrepancies early.
- `Architectural Decision:` Implemented quick wins: DEMO_PATH and BUNDLE_README/QUICKSTART now reference "eight beats" (not "seven") to account for the new Beat 5.5. Added fallback sentence to DEMO_PATH Step 3 for single-CLI edge case. Clarified deploy-and-bootstrap.ps1 header comment. Deferred T3-A (MacPorts justification), T3-D (Windows Python 3.10+ version check), T3-E (npm pre-flight check), T3-G (EXPLAINERS sidecar specificity) to future sprint pending deeper spec work or OS-specific validation.
- `Evidence:` Branch `feat/onboarding-multi-agent-story` commits: Beat count sync in BUNDLE_README.md, QUICKSTART.md, DEMO_PATH.md; demo fallback in DEMO_PATH.md line ~55; deploy-and-bootstrap.ps1 header comment refresh.
- `Promotion Target:` Each deferred item (T3-A/D/E/G) should spawn its own post-NRC lesson entry once the rationale is decided (MacPorts decision, Windows Python policy, npm package reliability strategy, memory bridge side-car naming audit). Do not silently slip these into doctrine — spec first, then promote.
- `Status:` active

### 2026-05-26 - MacPorts npm global prefix is root-owned; npm install -g needs sudo on macOS

- `Date:` 2026-05-26
- `Context:` macOS smoke test (NRC055206R, bundle 20260525-153017). `bootstrap-workstation.sh` failed with EACCES when attempting `npm install -g @anthropic-ai/claude-code`. MacPorts installs Node/npm to `/opt/local/`, a root-owned tree. All other MacPorts commands in the script already use `sudo` (`sudo port selfupdate`, `sudo port install`), but the three npm global installs were bare. Running the whole script as `sudo ./bootstrap-workstation.sh` was the workaround that confirmed all three CLIs install correctly.
- `Lesson:` On MacPorts, `npm install -g` requires sudo because the npm global prefix (`/opt/local/lib/node_modules`) is root-owned. On nvm/Homebrew setups the prefix is user-writable. The two behaviours look identical until a real macOS host runs the script.
- `Architectural Decision:` Introduced `npm_global_install()` helper in `scripts/bootstrap-workstation.sh`. When `PACKAGE_MODE=macports` the helper prepends `sudo`; all other modes run bare `npm install -g`. This is consistent with the existing pattern where every other MacPorts install already uses sudo. Keeps apt and nvm paths unchanged.
- `Evidence:` npm EACCES error (`errno -13`, `path /opt/local/lib/node_modules/@anthropic-ai`). All three CLIs confirmed working via sudo workaround (Claude Code 2.1.150, Codex 0.133.0, Gemini CLI 0.43.0). Fix: `scripts/bootstrap-workstation.sh` `npm_global_install()` helper, branch `fix/macports-npm-sudo`.
- `Promotion Target:` `docs/CONOPS.md` or bootstrap runbook if npm prefix strategy ever changes (e.g. switching to a user-writable prefix via `npm config set prefix`).
- `Status:` active

### 2026-05-26 - RHEL-family bootstrap: EPEL for ripgrep/jq, AppStream-first for Node

- `Date:` 2026-05-26
- `Context:` Enterprise pivot. `bootstrap-workstation.sh` rejected all non-Debian/Ubuntu Linux, but enterprise Linux is dominated by RHEL-family (RHEL/Rocky/Alma/Fedora). Added a `dnf`/`yum` path mirroring the apt path.
- `Lesson:` Two RHEL-specific traps differ from Debian: (1) `ripgrep` and `jq` are NOT in base RHEL/CentOS/Rocky/Alma repos — they need EPEL (`epel-release`); Fedora has them in base, so the EPEL step must be guarded to RHEL-family-but-not-Fedora. On minimal images `ripgrep` may further need CodeReady Builder (`crb`/`powertools`), which should be a documented manual step, not auto-enabled (trust-surface discipline). (2) Node 20+ is cleanest via the distro-signed AppStream module (`dnf module enable nodejs:20`), reserving the consent-gated NodeSource rpm as fallback — mirroring the apt prefer-distro-then-consent pattern.
- `Architectural Decision:` `detect_platform` resolves `PACKAGE_MODE=dnf` + `DNF_BIN` (prefer dnf, fall back to yum). New `ensure_base_dependencies_dnf` (with `ensure_epel_if_needed`) and `ensure_node_dnf` (AppStream → consent-gated NodeSource rpm). macOS stays MacPorts-only; apt/macports paths unchanged.
- `Evidence:` `scripts/bootstrap-workstation.sh` (detect_platform 3-arm chain, dnf helpers, main dispatch); `tests/test_bootstrap_workstation_dnf.py` (14 static tests incl. live DNF_BIN subshell). Runtime proof host-gated — see `docs/TECH_DEBT.md` "RHEL-family runtime proof on a real host".
- `Promotion Target:` `docs/SUPPORTED_PLATFORMS.md` and `docs/WORKSTATION_BOOTSTRAP.md` already document the matrix; promote a CONOPS bullet once a real RHEL host confirms EPEL + AppStream + npm-prefix behavior.
- `Status:` active

### 2026-05-26 - omni_factory symlink delivery hard-fails on native Windows

- `Date:` 2026-05-26
- `Context:` Enterprise pivot, full Windows parity pass. `scripts/omni_factory.py:ensure_symlink` called `Path.symlink_to()` unconditionally. On native Windows without Developer Mode/elevation that raises `OSError` WinError 1314, breaking `.claude/skills/` delivery — so `bootstrap-project.ps1`'s auto-sync fails mid-run even though scaffolding succeeded. Any already-shipped suitcase carries this.
- `Lesson:` A Python sync engine that delivers via symlinks is not portable to locked-down Windows. The PowerShell layer cannot fix it — the failure is in the Python `symlink_to`. The fallback must live in the engine itself, and it must stay compatible with the existing reverse-cleanup contract (which only pruned symlinks).
- `Architectural Decision:` On `OSError` when `os.name == 'nt'`, fall back to `shutil.copytree`/`copy2`. Directory copies carry a `.agent_forge_managed_copy` sentinel so `sync_symlink_dir` cleanup prunes stale copies like stale symlinks, and `ensure_symlink` refreshes a prior managed copy idempotently instead of refusing. POSIX keeps real symlinks; a non-Windows symlink `OSError` still propagates.
- `Evidence:` `scripts/omni_factory.py:ensure_symlink`/`sync_symlink_dir`/`_is_managed_copy`; `tests/test_symlink_fallback.py` (simulates Windows via `os.name='nt'` + `symlink_to` raising). Real-Windows proof host-gated — `docs/TECH_DEBT.md` "Windows native runtime proof on a real host".
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Claude skill delivery — once a real Windows host confirms the copy fallback fires and is pruned.
- `Status:` active

### 2026-05-26 - Windows PowerShell parity needs a shared helper + byte-identical projects.json

- `Date:` 2026-05-26
- `Context:` The `.ps1` scripts were a reduced flow vs the `.sh` ones: no interactive CONOPS, no `--existing`/`--with-local-skills`, a hardcoded (wrong) `@../CLAUDE.md` adapter import, a Python 3.10+ floor that was advertised but never enforced, and `bootstrap-project.ps1` registered the project in `projects.json` while `bootstrap-project.sh` did not.
- `Lesson:` (1) Centralize cross-script PowerShell logic in one dot-sourced helper (`_psutil.ps1`) so the Python-version gate, relative-path math, and symlink-or-copy fallback can't drift between four scripts. (2) PS 5.1 has no `[Path]::GetRelativePath`; use `System.Uri.MakeRelativeUri`. (3) When two scripts both write a shared JSON catalog, drive BOTH through the same Python snippet so output is byte-identical (avoids PS `ConvertTo-Json` BOM/escaping/reformat drift). (4) `deploy-and-bootstrap.ps1` ships as a standalone sidecar next to the ZIP, so it cannot dot-source a sibling helper — it must validate Python via the EXTRACTED helper post-extraction.
- `Architectural Decision:` New `scripts/_psutil.ps1` (Resolve-Python with real 3.10+ gate, Get-RelativePath, New-ManagedLink, Test-Command), dot-sourced by the in-tree scripts. `bootstrap-project.sh` now also registers in `projects.json` via the same Python snippet as the `.ps1`. The sidecar dot-sources the extracted helper.
- `Evidence:` `scripts/_psutil.ps1`, `scripts/bootstrap-project.ps1`/`.sh`, `scripts/bootstrap-workstation.ps1`, `scripts/deploy-and-bootstrap.ps1`, `scripts/deploy-factory.ps1`; `tests/test_windows_powershell_scripts.py` (6 new static checks). Runtime host-gated — `docs/TECH_DEBT.md`.
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Windows surfaces, once a Windows VM confirms the flow end-to-end.
- `Status:` active

### 2026-05-26 - Deploy wrappers silently dropped host-home flags

- `Date:` 2026-05-26
- `Context:` `deploy-factory.sh` parsed `--codex-home` but forwarded only `--target` to the codex sync (the value was dropped; `omni_factory.py sync-codex` accepts `--codex-home`). `deploy-and-bootstrap.sh` accepted `--claude-home|--codex-home` but rejected `--gemini-home` (error fallthrough). The `.ps1` `deploy-and-bootstrap.ps1` exposed no home flags at all.
- `Lesson:` A parsed-but-unforwarded flag is worse than an absent one — it looks supported and silently no-ops. Audit the full path from argument parse to the downstream invocation, and keep the three host-home flags symmetric across all deploy entry points (`.sh` and `.ps1`).
- `Architectural Decision:` `deploy-factory.sh` forwards `--codex-home` to the codex sync; `deploy-and-bootstrap.sh` accepts `--gemini-home`; `deploy-and-bootstrap.ps1` gained `-ClaudeHome`/`-CodexHome`/`-GeminiHome` and forwards all three.
- `Evidence:` `scripts/deploy-factory.sh`, `scripts/deploy-and-bootstrap.sh`, `scripts/deploy-and-bootstrap.ps1`; `tests/test_windows_powershell_scripts.py` home-flag parity test.
- `Promotion Target:` None — direct fix; the scripts enforce it on disk.
- `Status:` active

### 2026-05-26 - agentskills.io sanctions metadata for client extensions (verified)

- `Date:` 2026-05-26
- `Context:` Enterprise-readiness standards re-verification against the primary source (https://agentskills.io/specification). Confirmed: a skill is a directory with `SKILL.md`; required frontmatter is `name` (≤64, lowercase/digits/hyphens, must match the parent directory name) and `description` (≤1024); optional standard fields are `license`, `compatibility` (≤500), `metadata` (string→string map), and experimental `allowed-tools`; progressive disclosure recommends `name`+`description` ~100 tokens at startup and the `SKILL.md` body under 500 lines / 5000 tokens. All 30 global skills satisfy name==directory and the size ceiling.
- `Lesson:` The spec explicitly designates `metadata` as the home for client-specific properties "not defined by the Agent Skills spec," recommending unique key names to avoid conflicts. Agent Forge currently carries its local extensions (`targets`, `capability_class`, `delivery_projects`, `context_cost`, `model_tier`, command-name overrides, sandbox, MCP reqs) as TOP-LEVEL frontmatter keys. That is not forbidden, but the spec's sanctioned extension point is `metadata` (e.g. `metadata.agent_forge.*`).
- `Architectural Decision:` Keep top-level local extensions for now — migrating to `metadata.agent_forge.*` is a backward-compatible-renderer-and-verifier change touching all 30 SKILL.md files and is not worth churning mid-audit. Tracked as a TECH_DEBT item. The renderer already strips these before writing host-native skill files, so there is no runtime conflict with hosts that parse the standard.
- `Evidence:` https://agentskills.io/specification (frontmatter table + `metadata` field note); `docs/CONOPS.md` § Standard vs Local Extensions (already documents the fields as local extensions); `docs/TECH_DEBT.md` migration item.
- `Promotion Target:` `docs/CONOPS.md` § Standard vs Local Extensions — add the `metadata.agent_forge.*` recommendation when/if the migration is scheduled.
- `Status:` active

### 2026-05-27 - Windows Store python alias stub + opt-in auto-provisioning

- `Date:` 2026-05-27
- `Context:` Live deploy on a fresh Windows 11 VM. The box had **no real Python — only the Microsoft Store `python3` App Execution Alias stub**. Under `$ErrorActionPreference='Stop'`, the stub's "Python was not found" native stderr crashed `Resolve-Python` with `NativeCommandError` instead of falling through. Static tests could not have caught this (Store-alias + EAP interaction needs a real Windows host).
- `Lesson:` (1) On Windows, candidate interpreters can be alias stubs that error on invocation; a resolver must skip `*\WindowsApps\*` stubs AND wrap each probe in try/finally with local `EAP=Continue` so a bad candidate is skipped, never fatal. (2) "Detect and fail clean" is the right default, but a self-healing deploy should optionally *remediate* — install the missing prerequisite — gated behind an explicit opt-in flag. Auto-install must never be the silent default: locked-down enterprise hosts forbid unsanctioned installs (SCCM/Intune) and may block winget.
- `Architectural Decision:` `_psutil.ps1` skips the alias stub + probes defensively; adds `Find-Python` (no-throw), `Invoke-PrerequisiteProvision` (winget Python 3.12 / Git / Node LTS, idempotent, PATH refresh), and `Resolve-Python -AutoProvision`. `deploy-and-bootstrap.ps1 -AutoProvision` / `deploy-and-bootstrap.sh --auto-provision` (the latter via `bootstrap-workstation.sh --base-deps-only`) provision on opt-in only. winget-installed tools need a session PATH refresh (`Update-SessionPath`) before re-resolving.
- `Evidence:` Live VM run (`win11`@192.168.122.127) showed the NativeCommandError pre-fix; `scripts/_psutil.ps1`, `scripts/deploy-and-bootstrap.{ps1,sh}`, `scripts/bootstrap-workstation.{ps1,sh}`; `tests/test_windows_powershell_scripts.py` + `tests/test_auto_provision.py`.
- `Promotion Target:` `docs/WORKSTATION_BOOTSTRAP.md` and `docs/SUPPORTED_PLATFORMS.md` already document the opt-in flag.
- `Status:` active

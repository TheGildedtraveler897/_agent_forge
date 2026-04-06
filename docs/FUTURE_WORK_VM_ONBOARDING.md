# VM And Operator Onboarding Remediation

> **Status: COMPLETED 2026-04-06**
> All 8 items below were implemented in the operator UX remediation pass.
> This document is retained as an implementation record.
> See `docs/HANDOFF.md` for the full change summary and remaining weaknesses.

This document recorded the remediation batch for the suitcase/operator UX gap discovered during the first manual VM test.

It was the decision-complete spec for the onboarding/portability UX execution pass.

## Problem Summary

The factory deploy now works, but the operator experience is still too easy to misunderstand:

- `deploy-factory.sh` installs the factory into `~/Projects`, but does not launch workstation bootstrap automatically
- a human can reasonably assume "deploy" means "machine ready"
- the bundle README was previously too thin about the required second step
- the difference between folder export, `.tar.gz`, and `.zip` was not explained clearly enough
- unzip location behavior was not explicitly documented for operators
- `bootstrap-project.sh` still stops too early and leaves adapter sync as a manual follow-up step
- project bootstrap does not yet help the operator turn a blank scaffold into a first-pass `CONOPS.md`
- export currently behaves like a portable factory snapshot, but not yet like a clean "new-company/new-machine" bootstrap product

### Core User Concern

The system is technically working but still feels engineer-shaped instead of founder/operator-shaped.

The operator should not need to infer hidden order-of-operations across:

- factory deploy
- workstation bootstrap
- project bootstrap
- adapter sync
- initial project-definition work

The desired experience is:

1. unpack
2. run one obvious command
3. get guided through machine setup
4. get guided through project setup
5. land in a ready-to-build project with the right adapters already wired

Result: the factory can be technically healthy while the operator still feels stuck on a fresh VM.

## Verified Current State

Already completed:

- suitcase export works
- suitcase deploy works
- isolated smoke test passed
- workstation bootstrap exists and is documented
- verifier includes the new scripts and docs

Not yet completed:

- a real Debian VM proof from a human operator perspective
- a real macOS proof
- a tighter end-to-end onboarding flow with fewer chances for operator confusion
- clean-export vs backup-export separation
- guided first-pass project-definition flow

## Remediation Goals

The next remediation batch should make the first-run operator path unambiguous.

Success means a human can:

1. unpack the suitcase anywhere
2. run the right deploy command
3. understand that deploy is only step one
4. run workstation bootstrap as step two
5. authenticate selected CLIs
6. reach a clearly documented "machine ready" state
7. bootstrap the first governed project without reading multiple docs to infer the order

Additional success criteria:

8. project bootstrap automatically wires the right adapter sync without asking the operator to remember extra `.sh` commands
9. operator can choose between a **clean bootstrap export** and a **stateful backup export**
10. clean bootstrap export carries reusable factory capability without carrying prior-machine/project residue by default

## Recommended Improvements

### 1. Add a one-shot machine onboarding wrapper

Create `scripts/deploy-and-bootstrap.sh`.

Required behavior:

- detect whether it is being run from an unpacked suitcase bundle
- run `deploy-factory.sh`
- print a hard stop notice that factory deploy is only step one
- immediately offer to launch `bootstrap-workstation.sh`
- if the operator accepts, run workstation bootstrap in the installed `~/Projects/_agent_forge`
- do not silently install packages or launch auth without operator confirmation

This wrapper becomes the recommended human-first path.

### 2. Add explicit workstation ready checks

Extend `bootstrap-workstation.sh` so the machine setup log and stdout include a ready-state summary.

Required checks:

- `claude --version`
- `codex --version`
- `gemini --version`
- auth status prompt for each selected hosted CLI

Required result categories:

- installed and authenticated
- installed, auth pending
- not selected
- failed

### 3. Expand the machine-bootstrap artifact

Keep writing the machine setup log under `_agent_forge/runtime/machine-setup/`, but make it decision-complete.

Required fields:

- OS detected
- package mode used
- Node version
- selected services
- install result per service
- auth status per service
- final ready-state summary
- next recommended command

### 4. Make project bootstrap operator-shaped

Upgrade `bootstrap-project.sh` so manual adapter sync is no longer a separate operator burden.

Required behavior:

- after scaffold creation, automatically run:
  - `sync-claude-adapters.sh --project <name>`
  - `sync-codex-skills.sh --project <name>`
- if the project was created with no local skills, still sync the relevant global/project-scoped governed delivery
- print a summary of what was synced

### 5. Add interactive project-definition flow

Project bootstrap should offer an optional interactive project-definition step.

Required behavior:

- ask whether the operator wants guided project-definition now
- if yes, collect minimal inputs:
  - project mission
  - audience/users
  - primary deliverable or system role
  - constraints or notable boundaries
- write a first-pass `docs/CONOPS.md`
- update `AGENTS.md` read-order references if needed

First implementation rule:

- do this inside the script using shell prompts and templates
- do not depend on launching Claude/Codex/Gemini during bootstrap

Reason:

- bootstrap must remain useful even if auth is incomplete or a hosted CLI is temporarily unavailable

### 6. Split export modes cleanly

Upgrade `factory-export.sh` to support two explicit export modes.

Required modes:

- `--mode clean`
  - for moving the factory to a fresh machine/company
  - include reusable factory capability only
  - replace inherited machine/project residue with minimal operator guidance
- `--mode backup`
  - preserve current state more faithfully as a founder backup
  - include current operational docs and historical notes as they exist

Default:

- `clean`

### 7. Define what clean export strips vs preserves

For `--mode clean`, preserve:

- canonical `_agent_forge`
- skills
- teams
- adapters
- scripts
- current operator runbooks
- minimal doctrine docs needed for the factory

For `--mode clean`, strip or regenerate:

- prior-machine gotcha accumulation that is not factory-generic
- stale handoff/session residue that only describes the source environment
- historical “what changed on this machine” narrative where it does not help a fresh operator

Implementation rule:

- do not remove factory capability
- do not remove reusable workflow knowledge
- do remove source-environment-specific operational residue by default

### 8. Add a VM-first operator runbook

Create a short dedicated doc for human execution on a fresh Debian VM.

Required content:

- preferred archive choice (`.tar.gz`)
- unpack command
- wrapper command
- alternate manual two-step path
- ready check
- first project bootstrap
- note that unzip location does not matter

### 9. Improve deploy/bootstrap messaging everywhere

The following surfaces must all agree on the operator path:

- bundle `README.md`
- `FACTORY_SUITCASE.md`
- `WORKSTATION_BOOTSTRAP.md`
- `deploy-factory.sh` stdout
- new wrapper stdout
- `bootstrap-project.sh` stdout

## Research Findings Behind The Design

The current design choice remains correct:

- deploy and workstation bootstrap should stay separate because repo deployment and package/auth setup are different risk classes
- hosted subscription auth cannot be fully automated reliably, so the machine bootstrap must guide rather than fake login
- Debian/Ubuntu should stay apt-first
- macOS should stay MacPorts-first
- external Node LTS source should remain explicit opt-in only
- project bootstrap should not depend on a hosted CLI being available just to create a usable first-pass `CONOPS.md`
- clean export and backup export are different products and should not be conflated

## Execution Order

1. Add one-shot `deploy-and-bootstrap.sh`
2. Add workstation ready checks and richer machine setup artifact
3. Upgrade `bootstrap-project.sh` to auto-sync adapters and skills
4. Add interactive first-pass `CONOPS.md` generation in `bootstrap-project.sh`
5. Add `factory-export.sh --mode clean|backup`
6. Add Debian VM operator runbook
7. Run real Debian VM proof
8. Run real macOS proof

## Out Of Scope For This Remediation

- Ollama/OpenRouter implementation
- full cross-platform support beyond Debian/Ubuntu and macOS
- automatic browser auth completion
- project-specific product work such as `reddit-archive` implementation

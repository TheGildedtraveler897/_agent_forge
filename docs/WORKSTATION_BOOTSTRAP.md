# Workstation Bootstrap

The suitcase export and deploy flow copies the Agent Forge factory to a machine. It does **not** make that machine ready for interactive LLM development by itself.

**Recommended:** use the one-shot wrapper from an unpacked suitcase bundle — it deploys the factory then asks whether to run this script:

```bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

Or run this script directly from an already-deployed factory:

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
```

## What This Script Does

- detects the host platform
- installs base dependencies for terminal development
- ensures Node is new enough for the hosted coding CLIs
- installs selected hosted coding CLIs:
  - Claude Code
  - Codex
  - Gemini CLI
- prints and records the authentication steps the operator must complete

The script writes a durable log under:

```text
_agent_forge/runtime/machine-setup/
```

## Supported Platforms

### Debian / Ubuntu

- package manager: `apt`
- base dependencies: `git`, `curl`, `jq`, `ripgrep`, `zip`, `unzip`, `tar`, `ca-certificates`, `build-essential`
- Node policy:
  - use native `apt` packages if the version is sufficient
  - if Node is too old, ask before adding a vetted external Node LTS apt source
  - no silent external repo changes

### macOS

- package manager: MacPorts
- Homebrew is intentionally not the default path
- if MacPorts is missing, the script stops and tells the operator to install it first
- Node is provisioned via MacPorts before npm-based CLI installs

## Hosted CLI Install And Auth

### Claude Code

- install path: `npm install -g @anthropic-ai/claude-code`
- auth: launch `claude` and complete the browser login flow
- alternate enterprise auth paths may use Anthropic Console, Bedrock, or Vertex

### Codex

- install path: `npm install -g @openai/codex`
- auth: run `codex --login` or `codex` and choose Sign in with ChatGPT
- API key auth remains a secondary route

### Gemini CLI

- install path: `npm install -g @google/gemini-cli`
- requires Node 20+
- auth:
  - preferred: `gemini` and Login with Google
  - alternate: `GEMINI_API_KEY`

Gemini-specific pitfalls:

- `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_PROJECT_ID` can force organization entitlement checks
- corporate TLS interception may require:
  - `NODE_USE_SYSTEM_CA=1`
  - or `NODE_EXTRA_CA_CERTS=/path/to/corporate-ca.crt`
- `CI_*` environment variables can suppress interactive mode

## Security Position

- native distro package managers are preferred where possible
- macOS uses MacPorts, not Homebrew
- Debian/Ubuntu uses native apt first
- external Node LTS repo use is explicit opt-in only
- snap is not the primary path for coding CLIs because filesystem/tool execution behavior is often awkward for terminal agents

## Ready State

The bootstrap script runs a ready-state check at the end and prints a summary of which CLIs are installed and whether authentication steps are still pending.

A workstation is considered ready when:

1. suitcase deploy completed successfully
2. selected CLIs are installed and on `PATH` (confirmed by the ready-state check)
3. the operator completed authentication
4. `_agent_forge/runtime/machine-setup/` contains a successful setup log

After the machine is ready, bootstrap a project:

```bash
./scripts/bootstrap-project.sh --name <your-project>
```

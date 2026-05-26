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

### Red Hat family (RHEL / Fedora / CentOS / Rocky / AlmaLinux)

- package manager: `dnf` (falls back to `yum` on RHEL 7)
- base dependencies: `git`, `curl`, `jq`, `ripgrep`, `zip`, `unzip`, `tar`, `ca-certificates`, plus a development toolchain (`gcc`, `gcc-c++`, `make`, and the *Development Tools* group best-effort)
- **EPEL:** `ripgrep` and `jq` are not in the base RHEL/CentOS/Rocky/Alma repos (Fedora ships them in base). The script enables `epel-release` automatically on RHEL-family-but-not-Fedora hosts, idempotently.
- **CodeReady Builder / PowerTools:** on some minimal RHEL images `ripgrep` additionally needs CRB. The script does **not** auto-enable it (trust-surface discipline). If `ripgrep` fails to resolve, enable it manually and re-run:
  - RHEL/Rocky/Alma 9: `sudo dnf config-manager --set-enabled crb`
  - RHEL/Rocky/Alma 8: `sudo dnf config-manager --set-enabled powertools`
- Node policy:
  - preferred: the distro AppStream module `nodejs:20` (distro-signed, no external source)
  - if unavailable/too old, ask before adding the vetted external NodeSource **rpm** source
  - no silent external repo changes

### macOS

- package manager: MacPorts
- Homebrew is intentionally not the default path
- if MacPorts is missing, the script stops and tells the operator to install it first
- Node is provisioned via MacPorts before npm-based CLI installs

### Windows (native, no WSL)

- the bash script is not used; run the PowerShell entry points instead:
  - `scripts\bootstrap-workstation.ps1 -Install` installs base tools via `winget` (Python 3.10+, Git, Node.js LTS) and the selected hosted CLIs via `npm install -g`
  - `scripts\bootstrap-project.ps1 -Name <name>` scaffolds a governed project (full parity with the bash flow)
- Python 3.10+ is enforced (not merely existence-checked)
- `.claude\CLAUDE.md` is created as a symbolic link, or — when Windows refuses one without Developer Mode/elevation — a managed file copy with a warning

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

## Corporate Proxy / TLS Interception (enterprise pre-flight)

The bootstrap scripts never scrub the environment, and the NodeSource install
lines use `sudo -E` so proxy and CA settings survive the privilege boundary.
That means proxy/TLS support is mostly a matter of configuring the environment
before you run the script — not editing the script.

- **Shell proxy:** export `http_proxy`, `https_proxy`, and `no_proxy` before running. These flow to `curl`, `npm`, and (where configured) the package manager.
- **Package-manager proxy:** plain `sudo` resets the environment for package installs, so configure the proxy in the package manager itself:
  - `apt`: `/etc/apt/apt.conf.d/` (an `Acquire::http::Proxy "...";` drop-in)
  - `dnf`/`yum`: `proxy=` in `/etc/dnf/dnf.conf`
- **Custom TLS roots (TLS-inspection networks):**
  - `NODE_EXTRA_CA_CERTS=/path/to/corporate-ca.pem` so Node-based CLIs trust the corporate root
  - or `NODE_USE_SYSTEM_CA=1` to trust the OS trust store
  - `npm config set cafile /path/to/corporate-ca.pem` (and `npm config set proxy` / `https-proxy`) for npm itself
- **Non-admin hosts:** the script requires `sudo` for package installs on apt/dnf/macports. On a locked-down host without sudo, install the base tools through your managed software portal first, then re-run — the script skips package installs it cannot perform and proceeds to the npm-based CLI installs (npm global prefix is user-writable on apt/dnf/Windows).

These are operator/environment responsibilities; the factory documents them
rather than hard-coding site-specific proxy or certificate values.

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

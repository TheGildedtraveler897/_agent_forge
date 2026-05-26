# Supported Platforms

Last updated: 2026-05-26 (enterprise-readiness audit)

Agent Forge targets four operating-system families. This matrix states what is
**proven** (run end-to-end on a real host), **structurally checked** (static
analysis, `bash -n`, unit tests, renderer/verifier — but not run on that OS),
and what still **needs a real host** before it can be called proven.

## Package-manager / install matrix

| Platform | Manager | Base deps | Node 20+ strategy | Hosted-CLI install | Status |
|---|---|---|---|---|---|
| Debian / Ubuntu | `apt` | `git curl jq ripgrep zip unzip tar ca-certificates build-essential` | native apt → consent-gated NodeSource apt | `npm install -g` (user prefix) | **proven** (Linux dev host) |
| RHEL / Fedora / CentOS / Rocky / Alma | `dnf` (`yum` on RHEL 7) | same + `gcc gcc-c++ make` + Dev Tools; **EPEL** for ripgrep/jq on non-Fedora | distro AppStream `nodejs:20` → consent-gated NodeSource rpm | `npm install -g` (user prefix) | **structurally checked**; runtime **needs a RHEL/Rocky/Alma/Fedora host** |
| macOS | MacPorts only (no Homebrew) | `git curl jq ripgrep zip unzip npm10` | MacPorts `nodejs20` | `sudo npm install -g` (MacPorts prefix is root-owned) | CLIs + project bootstrap **proven** (NRC055206R, 2026-05-25); Beat 0 inline render **needs the Mac** |
| Windows (native, no WSL) | `winget` + `npm` | `winget` Python 3.10+, Git, Node.js LTS | `winget OpenJS.NodeJS.LTS`, Node-major gate | `npm install -g` (user prefix) | **structurally checked**; runtime **needs a Windows VM** |

## What is proven vs. host-gated

**Proven (Linux dev host, this audit):**
- apt bootstrap path, verifier exit 0, full unit suite, suitcase export + COI/cache checks.
- The dnf path's structure: `bash -n`, branch/dispatch presence, EPEL guard placement, DNF_BIN prefer-dnf/fallback-yum logic (live subshell test).
- The Windows PowerShell parity constructs and the `omni_factory` symlink→copy fallback: static text tests + a `symlink_to`-raises monkeypatch test.

**Needs a real RHEL/Rocky/Alma/Fedora host:**
- EPEL actually providing `ripgrep`/`jq` (and any CRB/PowerTools dependency).
- `nodejs:20` AppStream module existing for the target minor version.
- `dnf module reset/enable` succeeding; NodeSource rpm behind a proxy.
- Whether `npm install -g` hits EACCES on the dnf global prefix (fix = add `dnf` to the MacPorts sudo branch, mirroring the macOS fix).

**Needs a real Windows VM (no WSL):**
- `New-Item -ItemType SymbolicLink` denial → copy fallback firing.
- `Resolve-Python` parsing `py -3 --version`; the `py` launcher present.
- `winget` + `npm install -g` placing `claude`/`codex`/`gemini` on PATH (new shell for PATH refresh).
- `MakeRelativeUri` producing the expected `..\..\CLAUDE.md`; `projects.json` round-trip + `verify` on a Windows-registered project.

**Needs the operator's Mac:**
- `/onboarding-guide` Beat 0 rendering inline in Claude Code (set `mac.pass` only after observing it).

## Enterprise network constraints

Corporate proxy / TLS-interception handling is documented in
[`WORKSTATION_BOOTSTRAP.md`](WORKSTATION_BOOTSTRAP.md) § Corporate Proxy / TLS
Interception. The scripts preserve proxy/CA environment (`sudo -E`); site-specific
proxy URLs and CA roots are operator-configured, never hard-coded.

## Tracking

Host-gated items are tracked as open entries in [`TECH_DEBT.md`](TECH_DEBT.md) and
in `runtime/validation-matrix.json`. `*.pass` flags are set only against captured
evidence from a real host.

# Windows workstation bootstrap for Agent Forge — install parity with
# scripts/bootstrap-workstation.sh. Detection is safe by default. With -Install,
# uses winget for base tools (Python/Git/Node) and `npm install -g` for the
# hosted CLIs (Claude Code, Codex, Gemini), enforces Python 3.10+ and Node 20+,
# offers the same 1-7 service menu, writes a durable setup log, and prints the
# same authentication guidance. Native Windows; no WSL required.

[CmdletBinding()]
param(
    [switch]$Install,
    [ValidateSet('1', '2', '3', '4', '5', '6', '7')]
    [string]$Service = '',
    [switch]$IncludeClaudeCode,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: bootstrap-workstation.ps1 [-Install] [-Service <1-7>] [-IncludeClaudeCode]

Checks a native Windows workstation for Agent Forge prerequisites. With
-Install, uses winget to install Python 3.10+, Git, and Node.js LTS (20+), then
installs the selected hosted coding CLIs via npm. If winget is unavailable,
prints official install URLs.

Service selections (1-7):
  1) Claude Code only       5) Claude Code + Gemini CLI
  2) Codex only             6) Codex + Gemini CLI
  3) Gemini CLI only        7) All three
  4) Claude Code + Codex

Pass -Service to select non-interactively; omit it to be prompted when -Install.
"@
    exit 0
}

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir '_psutil.ps1')

$factoryRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
$machineSetupDir = Join-Path $factoryRoot 'runtime\machine-setup'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logPath = Join-Path $machineSetupDir "bootstrap-$stamp.md"

function Install-WingetPackage {
    param(
        [Parameter(Mandatory=$true)][string]$Id,
        [Parameter(Mandatory=$true)][string]$Name
    )
    if (-not (Test-Command 'winget')) {
        Write-Warning "winget is not available. Install $Name manually."
        return
    }
    Write-Host "Installing $Name with winget..."
    winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements
}

function Get-NodeMajor {
    if (-not (Test-Command 'node')) { return 0 }
    $v = (& node --version) 2>$null
    if ($v -match 'v?(\d+)\.') { return [int]$matches[1] }
    return 0
}

# npm has no sudo on Windows (the global prefix is user-writable), unlike the
# MacPorts path in the .sh. Mirrors install_claude/codex/gemini.
function Install-NpmGlobal {
    param(
        [Parameter(Mandatory=$true)][string]$Package,
        [Parameter(Mandatory=$true)][string]$Binary,
        [Parameter(Mandatory=$true)][string]$Label
    )
    if (-not (Test-Command 'npm')) {
        Write-Warning "npm is not on PATH; install Node.js LTS first, reopen PowerShell, and re-run."
        return $false
    }
    Write-Host "Installing $Label ($Package)..."
    & npm install -g $Package
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$Label install failed (npm exit $LASTEXITCODE)."
        return $false
    }
    if (-not (Test-Command $Binary)) {
        Write-Warning "$Label installed but '$Binary' is not on PATH yet. Reopen PowerShell, then run: $Binary --version"
        return $false
    }
    return $true
}

function Read-ServiceSelection {
    Write-Host "Select which hosted coding CLIs to install:"
    Write-Host "  1) Claude Code only"
    Write-Host "  2) Codex only"
    Write-Host "  3) Gemini CLI only"
    Write-Host "  4) Claude Code + Codex"
    Write-Host "  5) Claude Code + Gemini CLI"
    Write-Host "  6) Codex + Gemini CLI"
    Write-Host "  7) All three"
    do {
        $choice = Read-Host "Enter selection [1-7]"
    } until ($choice -match '^[1-7]$')
    return $choice
}

Write-Host "Agent Forge Windows workstation check"
Write-Host ""

# Base tools: winget id + advisory URL. Enforce Python 3.10+ / Node 20+ below.
$checks = @(
    @{ Command = 'python'; Name = 'Python 3.10+'; Winget = 'Python.Python.3'; Url = 'https://www.python.org/downloads/windows/' },
    @{ Command = 'git'; Name = 'Git'; Winget = 'Git.Git'; Url = 'https://git-scm.com/download/win' },
    @{ Command = 'node'; Name = 'Node.js LTS'; Winget = 'OpenJS.NodeJS.LTS'; Url = 'https://nodejs.org/en/download' }
)

foreach ($check in $checks) {
    if (Test-Command $check.Command) {
        Write-Host "[OK]   $($check.Name): $($check.Command) is on PATH"
        continue
    }
    Write-Warning "$($check.Name) is missing from PATH."
    if ($Install) {
        Install-WingetPackage -Id $check.Winget -Name $check.Name
    } else {
        Write-Host "       Install: $($check.Url)"
    }
}

# Enforce the advertised Python 3.10+ floor (previously only existence-checked).
$pythonOk = $false
try {
    $py = Resolve-Python
    Write-Host "[OK]   Python floor satisfied: $($py.Version)"
    $pythonOk = $true
} catch {
    Write-Warning $_
    Write-Host "       Install Python 3.10+ from https://www.python.org/downloads/windows/"
}

# Enforce Node 20+ (required by Gemini CLI; recommended for the others).
$nodeMajor = Get-NodeMajor
if ($nodeMajor -ge 20) {
    Write-Host "[OK]   Node.js major version: $nodeMajor"
} elseif (Test-Command 'node') {
    Write-Warning "Node.js $nodeMajor detected; 20+ is required. Update via winget OpenJS.NodeJS.LTS or https://nodejs.org/en/download"
}

if (-not $Install) {
    Write-Host ""
    Write-Host "Detection only. Re-run with -Install to install base tools and hosted CLIs."
    Write-Host "Codex and Gemini run natively in PowerShell; WSL2 remains an optional fallback if a native CLI misbehaves."
    Write-Host ""
    Write-Host "Next:"
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File .\scripts\bootstrap-workstation.ps1 -Install"
    exit 0
}

# ── Install path ───────────────────────────────────────────────────────────────

$selection = if ($Service) { $Service } else { Read-ServiceSelection }
$installClaude = $selection -in @('1', '4', '5', '7')
$installCodex  = $selection -in @('2', '4', '6', '7')
$installGemini = $selection -in @('3', '5', '6', '7')
if ($IncludeClaudeCode) { $installClaude = $true }

# Durable setup log.
New-Item -ItemType Directory -Force -Path $machineSetupDir | Out-Null
$header = @"
# Workstation Bootstrap Log

- Generated: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
- Host OS: Windows (native PowerShell)
- Package mode: winget + npm
- Factory root: $factoryRoot

## Selected Services

- Claude Code: $installClaude
- Codex: $installCodex
- Gemini CLI: $installGemini

## Install Results

"@
[System.IO.File]::WriteAllText($logPath, $header)

$results = @()
if ($installClaude) {
    if (Install-NpmGlobal -Package '@anthropic-ai/claude-code' -Binary 'claude' -Label 'Claude Code') {
        $results += "- Claude Code installed: $((Get-Command claude -ErrorAction SilentlyContinue).Source)"
    } else { $results += "- Claude Code: install incomplete (see warnings above)" }
}
if ($installCodex) {
    if (Install-NpmGlobal -Package '@openai/codex' -Binary 'codex' -Label 'Codex') {
        $results += "- Codex installed: $((Get-Command codex -ErrorAction SilentlyContinue).Source)"
    } else { $results += "- Codex: install incomplete (see warnings above)" }
}
if ($installGemini) {
    if (Install-NpmGlobal -Package '@google/gemini-cli' -Binary 'gemini' -Label 'Gemini CLI') {
        $results += "- Gemini CLI installed: $((Get-Command gemini -ErrorAction SilentlyContinue).Source)"
    } else { $results += "- Gemini CLI: install incomplete (see warnings above)" }
}
Add-Content -Path $logPath -Encoding UTF8 -Value ($results -join "`n")

# ── Authentication guidance (ported from bootstrap-workstation.sh) ─────────────

Write-Host ""
Write-Host "## Authentication Guidance"
$auth = @("`n## Authentication Guidance`n")
if ($installClaude) {
    Write-Host ""
    Write-Host "Claude Code authentication:"
    Write-Host "- Preferred: launch 'claude' and complete the browser-based sign-in with your Claude.ai subscription."
    Write-Host "- Alternate enterprise routes: Anthropic Console API, Bedrock, or Vertex."
    $auth += "- Claude Code auth: run ``claude`` and complete the login flow."
}
if ($installCodex) {
    Write-Host ""
    Write-Host "Codex authentication:"
    Write-Host "- Preferred: run 'codex --login' or 'codex' and choose Sign in with ChatGPT."
    Write-Host "- Alternate route: API key mode if subscription sign-in is not available."
    $auth += "- Codex auth: run ``codex --login`` or ``codex`` and choose Sign in with ChatGPT."
}
if ($installGemini) {
    Write-Host ""
    Write-Host "Gemini CLI authentication:"
    Write-Host "- Preferred: run 'gemini' and choose Login with Google."
    Write-Host "- Alternate route: set GEMINI_API_KEY."
    Write-Host "- If login fails: unset GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_PROJECT_ID; on corporate TLS"
    Write-Host "  networks try NODE_USE_SYSTEM_CA=1 or NODE_EXTRA_CA_CERTS=C:\path\to\corporate-ca.crt."
    $auth += "- Gemini CLI auth: run ``gemini`` and choose Login with Google or set GEMINI_API_KEY."
    $auth += "- Gemini CLI pitfall: unset GOOGLE_CLOUD_PROJECT* if org entitlement checks appear unexpectedly."
    $auth += "- Gemini CLI pitfall: set NODE_USE_SYSTEM_CA=1 or NODE_EXTRA_CA_CERTS on corporate TLS-inspection networks."
}
Add-Content -Path $logPath -Encoding UTF8 -Value ($auth -join "`n")

Write-Host ""
Write-Host "Codex and Gemini run natively in PowerShell; WSL2 remains an optional fallback if a native CLI misbehaves."
Write-Host "PATH changes from winget/npm may require closing and reopening PowerShell."
Write-Host ""
Write-Host "Log written to: $logPath"
Write-Host "Next:"
Write-Host "  powershell.exe -ExecutionPolicy Bypass -File .\scripts\bootstrap-project.ps1 -Name <your-project>"

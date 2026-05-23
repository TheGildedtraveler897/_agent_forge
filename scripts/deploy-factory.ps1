# Deploy an exported Agent Forge suitcase on native Windows (no WSL required).
# Mirrors deploy-factory.sh for Linux/macOS; calls python3 omni_factory.py for
# the actual sync work, which already runs on Windows.

[CmdletBinding()]
param(
    [string]$ProjectsRoot = (Join-Path $env:USERPROFILE 'Projects'),
    [string]$ClaudeHome = (Join-Path $env:USERPROFILE '.claude'),
    [string]$CodexHome = (Join-Path $env:USERPROFILE '.codex'),
    [string]$GeminiHome = (Join-Path $env:USERPROFILE '.gemini'),
    [switch]$OverwriteRootDocs,
    [switch]$ReplaceFactory,
    [switch]$ClaudeOnly,
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: deploy-factory.ps1 [-ProjectsRoot DIR] [-ClaudeHome DIR] [-CodexHome DIR]
                          [-GeminiHome DIR] [-OverwriteRootDocs] [-ReplaceFactory]
                          [-ClaudeOnly] [-DryRun]

Deploy an exported Agent Forge suitcase on native Windows.

Defaults target the current user's home (USERPROFILE). The script copies the
canonical _agent_forge tree into ProjectsRoot, then invokes
python3 omni_factory.py sync-claude (and optionally Codex/Gemini) to write
the host-native skills/agents/commands into the relevant home directories.

Options:
  -ProjectsRoot      Target Projects root (default: %USERPROFILE%\Projects)
  -ClaudeHome        Target Claude home (default: %USERPROFILE%\.claude)
  -CodexHome         Target Codex home (default: %USERPROFILE%\.codex)
  -GeminiHome        Target Gemini home (default: %USERPROFILE%\.gemini)
  -OverwriteRootDocs Replace shared root docs if they already exist
  -ReplaceFactory    Replace an existing target _agent_forge snapshot
  -ClaudeOnly        Skip Codex and Gemini sync. Recommended for Windows
                     coworkers who use Claude Code only.
  -DryRun            Print the actions that would be taken; make no changes.
  -Help              Show this message and exit.
"@
    exit 0
}

$ErrorActionPreference = 'Stop'

function Resolve-PythonCommand {
    foreach ($candidate in @('python3', 'python', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            if ($candidate -eq 'py') {
                return @('py', '-3')
            }
            return @($cmd.Source)
        }
    }
    throw "Python 3 not found on PATH. Install Python 3.10+ from python.org and re-run."
}

$python = Resolve-PythonCommand

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceFactoryRoot = Resolve-Path (Join-Path $scriptDir '..')
$packageRoot = Resolve-Path (Join-Path $sourceFactoryRoot '..')
$targetFactoryRoot = Join-Path $ProjectsRoot '_agent_forge'

Write-Host "Source factory root: $sourceFactoryRoot"
Write-Host "Package root:        $packageRoot"
Write-Host "Target factory root: $targetFactoryRoot"
Write-Host "Claude home:         $ClaudeHome"
if (-not $ClaudeOnly) {
    Write-Host "Codex home:          $CodexHome"
    Write-Host "Gemini home:         $GeminiHome"
}
if ($DryRun) {
    Write-Host "(dry run — no changes will be made)"
}

# Locate shared-root doctrine.
$sharedRoot = $null
$sharedRootInPackage = Join-Path $packageRoot 'shared-root'
if (Test-Path $sharedRootInPackage) {
    $sharedRoot = $sharedRootInPackage
} elseif ((Test-Path (Join-Path $packageRoot 'AGENTS.md')) -and `
          (Test-Path (Join-Path $packageRoot 'CLAUDE.md'))) {
    $sharedRoot = $packageRoot.Path
} else {
    Write-Warning "No shared-root/ doctrine files found next to the factory payload. Continuing without shared-root copy."
}

function Copy-FileIfNeeded {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )
    if (-not (Test-Path $Source)) {
        return
    }
    $destDir = Split-Path -Parent $Destination
    if (-not (Test-Path $destDir)) {
        if ($DryRun) {
            Write-Host "  [dry] mkdir $destDir"
        } else {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
    }
    if ((Test-Path $Destination) -and (-not $OverwriteRootDocs)) {
        Write-Host "  skip: $Destination (already exists; pass -OverwriteRootDocs to replace)"
        return
    }
    if ($DryRun) {
        Write-Host "  [dry] cp $Source -> $Destination"
    } else {
        Copy-Item -Force $Source $Destination
    }
}

# ProjectsRoot.
if (-not (Test-Path $ProjectsRoot)) {
    if ($DryRun) {
        Write-Host "[dry] mkdir $ProjectsRoot"
    } else {
        New-Item -ItemType Directory -Force -Path $ProjectsRoot | Out-Null
    }
}

# Existing factory check.
if (Test-Path $targetFactoryRoot) {
    if (-not $ReplaceFactory) {
        throw "Target factory already exists: $targetFactoryRoot. Re-run with -ReplaceFactory to refresh."
    }
    Write-Host "Removing existing factory at $targetFactoryRoot"
    if (-not $DryRun) {
        Remove-Item -Recurse -Force $targetFactoryRoot
    }
}

# Copy _agent_forge tree.
Write-Host "Copying canonical factory to $targetFactoryRoot"
if (-not $DryRun) {
    Copy-Item -Recurse -Force $sourceFactoryRoot $targetFactoryRoot
    # Strip machine-local residue from the copy.
    foreach ($residue in @('.git', 'exports', 'dev', 'dist', 'runtime\managed-state.json', 'runtime\validation')) {
        $path = Join-Path $targetFactoryRoot $residue
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
        }
    }
}

# Shared root doctrine.
if ($sharedRoot) {
    Copy-FileIfNeeded -Source (Join-Path $sharedRoot 'AGENTS.md') -Destination (Join-Path $ProjectsRoot 'AGENTS.md')
    Copy-FileIfNeeded -Source (Join-Path $sharedRoot 'CLAUDE.md') -Destination (Join-Path $ProjectsRoot 'CLAUDE.md')
    Copy-FileIfNeeded -Source (Join-Path $sharedRoot 'docs\gotchas.md') -Destination (Join-Path $ProjectsRoot 'docs\gotchas.md')
    Copy-FileIfNeeded -Source (Join-Path $sharedRoot 'docs\port_ledger.md') -Destination (Join-Path $ProjectsRoot 'docs\port_ledger.md')
}

# Sync host surfaces via python3 omni_factory.py. The sync engine handles
# every host-native path resolution itself, including %USERPROFILE%\.claude\
# layout on Windows.
function Invoke-Sync {
    param(
        [Parameter(Mandatory)][string[]]$Args
    )
    if ($DryRun) {
        Write-Host "  [dry] $($python -join ' ') $($Args -join ' ')"
        return
    }
    & $python[0] $python[1..($python.Length - 1)] @Args
    if ($LASTEXITCODE -ne 0) {
        throw "sync failed: $($Args -join ' ')"
    }
}

$omniFactory = Join-Path $targetFactoryRoot 'scripts\omni_factory.py'

Write-Host "Syncing Claude surfaces..."
Invoke-Sync -Args @($omniFactory, 'sync-claude')

if (-not $ClaudeOnly) {
    Write-Host "Syncing Codex surfaces..."
    try {
        Invoke-Sync -Args @($omniFactory, 'sync-codex')
    } catch {
        Write-Warning "Codex sync failed (Codex CLI may not be installed): $_"
    }
    Write-Host "Syncing Gemini surfaces..."
    try {
        Invoke-Sync -Args @($omniFactory, 'sync-gemini')
    } catch {
        Write-Warning "Gemini sync failed (Gemini CLI may not be installed): $_"
    }
}

Write-Host ""
Write-Host "Agent Forge deployed to $targetFactoryRoot"
Write-Host "Next steps:"
Write-Host "  1. cd $targetFactoryRoot"
Write-Host "  2. pwsh -File .\scripts\bootstrap-project.ps1 -Name <your-project>"
Write-Host "  3. In Claude Code at the new project, invoke: /onboarding-guide"

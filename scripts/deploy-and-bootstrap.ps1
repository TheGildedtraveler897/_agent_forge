# One-shot Windows ZIP deploy for an Agent Forge suitcase.
# Run this from a directory that contains the suitcase .zip. It unblocks the
# archive before extraction, validates the extracted tree, then delegates to
# deploy-factory.ps1 for the canonical sync.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BundleZip,
    [string]$DestinationRoot = (Join-Path (Get-Location) 'agent-forge-suitcase-expanded'),
    [string]$ProjectsRoot = (Join-Path $env:USERPROFILE 'Projects'),
    [switch]$AllHosts,
    [switch]$ReplaceFactory,
    [switch]$OverwriteRootDocs,
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: deploy-and-bootstrap.ps1 -BundleZip <agent-forge-suitcase.zip> [options]

Safely deploys an Agent Forge suitcase on native Windows:
  1. Unblocks the ZIP file.
  2. Extracts it with Expand-Archive.
  3. Verifies the _agent_forge payload is complete.
  4. Unblocks extracted scripts and files.
  5. Runs deploy-factory.ps1.

Options:
  -BundleZip         Path to the suitcase .zip.
  -DestinationRoot   Extraction destination. Keep this short, for example C:\af.
  -ProjectsRoot      Target Projects root. Default: %USERPROFILE%\Projects.
  -AllHosts          Sync Claude, Codex, and Gemini. Default is Claude only.
  -ReplaceFactory    Replace existing %USERPROFILE%\Projects\_agent_forge.
  -OverwriteRootDocs Replace shared root docs if they already exist.
  -DryRun            Print deploy-factory actions where supported.
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

function Test-BundleIntegrity {
    param([Parameter(Mandatory=$true)][string]$FactoryRoot)

    $required = @(
        'AGENTS.md',
        'CLAUDE.md',
        'GEMINI.md',
        'docs',
        'policies',
        'scripts',
        'skills',
        'teams',
        'runtime',
        'evals',
        'projects.json',
        'global-mcp.json'
    )
    $missing = @()
    foreach ($item in $required) {
        $candidate = Join-Path $FactoryRoot $item
        if (-not (Test-Path $candidate)) {
            $missing += $item
        }
    }
    if ($missing.Count -gt 0) {
        throw "Incomplete Agent Forge extraction. Missing: $($missing -join ', '). This usually means Windows Mark of the Web or MAX_PATH blocked extraction. Re-run this script from a short path such as C:\af after Unblock-File succeeds."
    }
}

$bundlePath = (Resolve-Path -LiteralPath $BundleZip).Path
$destinationPath = $DestinationRoot

if ($destinationPath.Length -gt 150) {
    Write-Warning "Destination path is long ($($destinationPath.Length) chars). MAX_PATH extraction failures are more likely. Prefer a short path such as C:\af."
}

Write-Host "Unblocking bundle ZIP: $bundlePath"
if (-not $DryRun) {
    Unblock-File -LiteralPath $bundlePath -ErrorAction SilentlyContinue
}

if (-not (Test-Path $destinationPath)) {
    New-Item -ItemType Directory -Force -Path $destinationPath | Out-Null
}

Write-Host "Extracting bundle to: $destinationPath"
if (-not $DryRun) {
    Expand-Archive -LiteralPath $bundlePath -DestinationPath $destinationPath -Force
}

$factoryRoot = $null
$directFactory = Join-Path $destinationPath '_agent_forge'
if (Test-Path $directFactory) {
    $factoryRoot = (Resolve-Path -LiteralPath $directFactory).Path
} else {
    $match = Get-ChildItem -LiteralPath $destinationPath -Recurse -Directory -Filter '_agent_forge' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) {
        $factoryRoot = $match.FullName
    }
}

if (-not $factoryRoot) {
    throw "Could not find _agent_forge after extraction. Re-run from a short destination path and confirm the ZIP is the Agent Forge suitcase."
}

Test-BundleIntegrity -FactoryRoot $factoryRoot

Write-Host "Unblocking extracted Agent Forge tree..."
if (-not $DryRun) {
    Get-ChildItem -LiteralPath $factoryRoot -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue
}

$python = Resolve-PythonCommand
Write-Host "Python resolver: $($python -join ' ')"

$deployScript = Join-Path $factoryRoot 'scripts\deploy-factory.ps1'
if (-not (Test-Path $deployScript)) {
    throw "Missing deploy script: $deployScript"
}

$deployArgs = @(
    '-ProjectsRoot', $ProjectsRoot
)
if ($ReplaceFactory) {
    $deployArgs += '-ReplaceFactory'
}
if ($OverwriteRootDocs) {
    $deployArgs += '-OverwriteRootDocs'
}
if (-not $AllHosts) {
    $deployArgs += '-ClaudeOnly'
}
if ($DryRun) {
    $deployArgs += '-DryRun'
}

Write-Host "Running deploy-factory.ps1..."
& powershell.exe -ExecutionPolicy Bypass -File $deployScript @deployArgs
if ($LASTEXITCODE -ne 0) {
    throw "deploy-factory.ps1 failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Agent Forge deployed successfully."
Write-Host "Next steps:"
Write-Host "  1. cd $ProjectsRoot\_agent_forge"
Write-Host "  2. powershell.exe -ExecutionPolicy Bypass -File .\scripts\bootstrap-project.ps1 -Name <your-project>"
Write-Host "  3. Open Claude Code in that project and invoke: /onboarding-guide"
if (-not $AllHosts) {
    Write-Host ""
    Write-Host "Defaulted to -ClaudeOnly. Re-run with -AllHosts after Codex/Gemini are installed."
}

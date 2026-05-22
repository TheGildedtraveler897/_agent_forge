# Bootstrap a governed Agent Forge project on native Windows.
# Minimal counterpart to scripts/bootstrap-project.sh — scaffolds the minimum
# required files and runs the Python sync engine. The bash script remains the
# fuller flow (interactive project-definition, --existing standardization,
# local-skill scaffolding); for Windows-coworker demo flows the minimal flow
# below is sufficient.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$Path = "",
    [string]$ProjectsRoot = (Join-Path $env:USERPROFILE 'Projects'),
    [switch]$ClaudeOnly,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: bootstrap-project.ps1 -Name <name> [-Path <relative>] [-ProjectsRoot <dir>]
                              [-ClaudeOnly]

Scaffolds a new governed project under -ProjectsRoot with the minimum
Agent Forge contracts (AGENTS.md, CLAUDE.md, GEMINI.md, docs/CONOPS.md,
docs/HANDOFF.md), appends to projects.json, then runs the Python sync.

Options:
  -Name         Project display name (required).
  -Path         Relative directory name under -ProjectsRoot. Defaults to -Name.
  -ProjectsRoot Override projects root (default: %USERPROFILE%\Projects).
  -ClaudeOnly   Skip Codex and Gemini sync (recommended for Windows demo).
  -Help         Show this message.
"@
    exit 0
}

$ErrorActionPreference = 'Stop'

if (-not $Path) { $Path = $Name }

function Resolve-PythonCommand {
    foreach ($candidate in @('python3', 'python', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            if ($candidate -eq 'py') { return @('py', '-3') }
            return @($cmd.Source)
        }
    }
    throw "Python 3 not found on PATH. Install Python 3.10+ from python.org."
}

$python = Resolve-PythonCommand

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$factoryRoot = Resolve-Path (Join-Path $scriptDir '..')
$targetRoot = Join-Path $ProjectsRoot $Path

Write-Host "Bootstrapping project '$Name' at $targetRoot"

if (Test-Path $targetRoot) {
    Write-Warning "$targetRoot already exists; will leave existing files in place and only add missing scaffolding."
} else {
    New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
}

# Subdirectories.
foreach ($sub in @('docs', '.claude\agents', '.claude\commands', '.claude\skills',
                   '.codex\agents', '.gemini\agents', '.gemini\commands', '.gemini\skills',
                   '.agents\skills')) {
    $dir = Join-Path $targetRoot $sub
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

# Helper to write a file only if missing.
function New-StubFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Body
    )
    if (Test-Path $Path) {
        Write-Host "  skip: $Path (already exists)"
        return
    }
    [System.IO.File]::WriteAllText($Path, $Body)
    Write-Host "  wrote: $Path"
}

$agentsBody = @"
# $Name

Multi-agent contract for $Name.

## Context

TODO: describe what $Name is for, who it serves, and where it fits in the wider system.

## Required Reading Order

1. This file (\`AGENTS.md\`)
2. \`docs/CONOPS.md\`
3. \`docs/HANDOFF.md\`
4. The Agent Forge canonical \`AGENTS.md\` for shared workflow doctrine.

## Workflow Discipline

Follow the canonical chain: spec-architect -> execution-planner -> tdd-engineer ->
verification-gate -> branch-finisher. See the global skill catalog for definitions.
"@

$claudeBody = @"
# Claude Adapter

@AGENTS.md
@docs/CONOPS.md
@docs/HANDOFF.md

## Claude-Specific Notes

Keep this file thin and Claude-native. Shared workflow policy belongs in \`AGENTS.md\`.
"@

$geminiBody = @"
# Gemini Adapter

@AGENTS.md
@docs/CONOPS.md
@docs/HANDOFF.md

## Gemini-Specific Notes

Keep this file thin and Gemini-native.
"@

$conopsBody = @"
# $Name CONOPS

## Mission

TODO: describe the project mission, audience, and system role.

## Architecture

TODO: describe the major components, data flow, and source-of-truth docs.

## Operating Rules

- Canonical-first authoring.
- Append-first lessons.
- Triad runtime gate after canonical changes.
"@

$handoffBody = @"
# $Name Handoff

Last updated: $(Get-Date -Format 'yyyy-MM-dd')

## What Changed

- Project scaffolded via bootstrap-project.ps1.

## Current State

- Minimal Agent Forge contracts in place.

## Next Steps

1. Populate \`docs/CONOPS.md\` with the project mission and architecture.
2. Run the onboarding-guide skill inside Claude Code for a guided tour.
3. Use the workflow chain (\`spec-architect\` -> \`execution-planner\` -> \`tdd-engineer\` -> ...) for your first sprint.
"@

$claudeAdapterBody = @"
# Claude project adapter

@../AGENTS.md
@../CLAUDE.md
"@

New-StubFile -Path (Join-Path $targetRoot 'AGENTS.md') -Body $agentsBody
New-StubFile -Path (Join-Path $targetRoot 'CLAUDE.md') -Body $claudeBody
New-StubFile -Path (Join-Path $targetRoot 'GEMINI.md') -Body $geminiBody
New-StubFile -Path (Join-Path $targetRoot 'docs\CONOPS.md') -Body $conopsBody
New-StubFile -Path (Join-Path $targetRoot 'docs\HANDOFF.md') -Body $handoffBody
New-StubFile -Path (Join-Path $targetRoot '.claude\CLAUDE.md') -Body $claudeAdapterBody

# Append entry to projects.json if not already present.
$projectsJson = Join-Path $factoryRoot 'projects.json'
$payload = Get-Content -Raw $projectsJson | ConvertFrom-Json
if (-not ($payload.governed_projects | Where-Object { $_.name -eq $Name })) {
    $newEntry = [pscustomobject]@{
        name = $Name
        root = $Path
        trusted_workspace = $false
        required_files = @(
            'AGENTS.md',
            'CLAUDE.md',
            'docs/CONOPS.md',
            'docs/HANDOFF.md',
            '.claude/CLAUDE.md'
        )
    }
    $payload.governed_projects = @($payload.governed_projects) + @($newEntry)
    $payload | ConvertTo-Json -Depth 10 | Set-Content -Path $projectsJson -Encoding UTF8
    Write-Host "Added '$Name' to projects.json"
} else {
    Write-Host "Project '$Name' already present in projects.json; not modifying."
}

# Sync via the Python engine.
$omniFactory = Join-Path $factoryRoot 'scripts\omni_factory.py'

function Invoke-Sync {
    param([Parameter(Mandatory)][string[]]$Args)
    & $python[0] $python[1..($python.Length - 1)] @Args
    if ($LASTEXITCODE -ne 0) {
        throw "sync failed: $($Args -join ' ')"
    }
}

Write-Host "Syncing Claude surfaces for $Name..."
Invoke-Sync -Args @($omniFactory, 'sync-claude', '--project', $Name)

if (-not $ClaudeOnly) {
    Write-Host "Syncing Codex surfaces..."
    try { Invoke-Sync -Args @($omniFactory, 'sync-codex', '--project', $Name) }
    catch { Write-Warning "Codex sync failed: $_" }
    Write-Host "Syncing Gemini surfaces..."
    try { Invoke-Sync -Args @($omniFactory, 'sync-gemini', '--project', $Name) }
    catch { Write-Warning "Gemini sync failed: $_" }
}

Write-Host ""
Write-Host "Project '$Name' bootstrapped at $targetRoot"
Write-Host "Next:"
Write-Host "  1. cd $targetRoot"
Write-Host "  2. Open Claude Code here and invoke /onboarding-guide tour"

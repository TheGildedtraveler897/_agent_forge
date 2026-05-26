# Bootstrap a governed Agent Forge project on native Windows.
# Full parity with scripts/bootstrap-project.sh: interactive project-definition,
# -Existing standardization, -WithLocalSkills scaffolding, dynamic relative-path
# adapters, and a symlink-or-copy .claude\CLAUDE.md adapter. Shares the Python
# resolver (with a real 3.10+ gate), relative-path, and managed-link helpers via
# scripts/_psutil.ps1.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$Path = "",
    [string]$ProjectsRoot = (Join-Path $env:USERPROFILE 'Projects'),
    [switch]$Existing,
    [switch]$WithLocalSkills,
    [switch]$Define,
    [switch]$NoDefine,
    [switch]$ClaudeOnly,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: bootstrap-project.ps1 -Name <name> [-Path <relative>] [-ProjectsRoot <dir>]
                              [-Existing] [-WithLocalSkills] [-Define | -NoDefine]
                              [-ClaudeOnly]

Scaffolds a governed project under -ProjectsRoot with the Agent Forge contracts
(AGENTS.md, AGENTS.override.md, CLAUDE.md, GEMINI.md, docs/CONOPS.md,
docs/HANDOFF.md, .claude\CLAUDE.md), registers it in projects.json, runs the
Python sync, and offers an interactive project-definition flow.

Options:
  -Name             Project display name (required).
  -Path             Relative directory name under -ProjectsRoot. Defaults to -Name.
  -ProjectsRoot     Override projects root (default: %USERPROFILE%\Projects).
  -Existing         Standardize an existing project dir instead of creating one.
  -WithLocalSkills  Create local skill source dirs under _agent_forge\skills\projects\<Name>.
  -Define           Always run the interactive project-definition flow.
  -NoDefine         Never run the interactive project-definition flow.
  -ClaudeOnly       Skip Codex and Gemini sync (recommended for Windows demo).
  -Help             Show this message.
"@
    exit 0
}

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDir '_psutil.ps1')

if (-not $Path) { $Path = $Name }

# Resolve-Python enforces the advertised >= 3.10 floor (see scripts/_psutil.ps1).
$py = Resolve-Python
$pythonExe = $py.Exe
$pythonArgs = $py.Pre

$factoryRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
# Resolve ProjectsRoot to an absolute path without requiring it to exist yet.
$projectsRootAbs = [System.IO.Path]::GetFullPath($ProjectsRoot)
$targetRoot = Join-Path $projectsRootAbs $Path

# Relative-path adapters (computed lexically; targets need not exist yet).
$rootAgentsRel = (Get-RelativePath -FromDir $targetRoot -ToPath (Join-Path $projectsRootAbs 'AGENTS.md')).Replace('\', '/')
$claudeDir = Join-Path $targetRoot '.claude'
$rootClaudeRelFwd = (Get-RelativePath -FromDir $claudeDir -ToPath (Join-Path $projectsRootAbs 'CLAUDE.md')).Replace('\', '/')
$rootClaudeRelBack = Get-RelativePath -FromDir $claudeDir -ToPath (Join-Path $projectsRootAbs 'CLAUDE.md')

Write-Host "Bootstrapping project '$Name' at $targetRoot"

if ($Existing) {
    if (-not (Test-Path $targetRoot)) {
        throw "Existing mode requested but target does not exist: $targetRoot"
    }
    Write-Host "Standardizing existing project at $targetRoot"
} elseif (Test-Path $targetRoot) {
    Write-Warning "$targetRoot already exists; will leave existing files in place and only add missing scaffolding."
} else {
    New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
}

# Subdirectories — kept identical to bootstrap-project.sh so re-running either
# script yields the same tree.
foreach ($sub in @('docs', '.claude\agents', '.claude\skills', '.codex\agents',
                   '.gemini\agents', '.gemini\skills', '.agents\skills')) {
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
<!-- Managed by Agent Forge bootstrap. The sync script will replace this stub. -->

# Gemini Adapter

@$rootAgentsRel
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

# AGENTS.override.md — Codex 2026 precedence stub. Idempotent (New-StubFile skips
# if present), so re-running never clobbers operator-authored Codex overrides.
$agentsOverrideBody = @"
<!-- Project-local Codex overrides. Codex reads this file BEFORE the parent-tree AGENTS.md. -->
<!-- This stub is created by bootstrap-project.ps1 and is NOT regenerated by the omni-factory sync. -->
<!-- If you want a project-local override of any rule in ..\AGENTS.md or this project's AGENTS.md, write it here. -->
<!-- Empty / comment-only overrides have no effect; only non-comment content is parsed by Codex. -->
"@

# Fallback body for .claude\CLAUDE.md when a Windows symlink cannot be created.
# Carries the 'Managed by Agent Forge' sentinel so New-ManagedLink treats it as
# managed (skips it idempotently) and imports the root Claude adapter.
$claudeAdapterBody = @"
<!-- Managed by Agent Forge bootstrap. Fallback COPY because a Windows symlink could not be created.
     Enable Developer Mode or run elevated and re-run for a real symlink. -->
# Claude project adapter

@$rootClaudeRelFwd
"@

New-StubFile -Path (Join-Path $targetRoot 'AGENTS.md') -Body $agentsBody
New-StubFile -Path (Join-Path $targetRoot 'AGENTS.override.md') -Body $agentsOverrideBody
New-StubFile -Path (Join-Path $targetRoot 'CLAUDE.md') -Body $claudeBody
New-StubFile -Path (Join-Path $targetRoot 'GEMINI.md') -Body $geminiBody
New-StubFile -Path (Join-Path $targetRoot 'docs\CONOPS.md') -Body $conopsBody
New-StubFile -Path (Join-Path $targetRoot 'docs\HANDOFF.md') -Body $handoffBody

# .claude\CLAUDE.md adapter: symlink to the root Claude adapter, or a managed
# copy when native Windows refuses the symlink (no Developer Mode / elevation).
New-ManagedLink -LinkPath (Join-Path $claudeDir 'CLAUDE.md') -TargetRelative $rootClaudeRelBack -FallbackBody $claudeAdapterBody

if ($WithLocalSkills) {
    $localSkillsRoot = Join-Path $factoryRoot ('skills\projects\' + $Name)
    if (-not (Test-Path $localSkillsRoot)) {
        New-Item -ItemType Directory -Force -Path $localSkillsRoot | Out-Null
        Write-Host "  created local skill source dir: $localSkillsRoot"
    } else {
        Write-Host "  skip: $localSkillsRoot (already exists)"
    }
}

# Register the project in projects.json. Driven through the SAME Python snippet
# as bootstrap-project.sh so both scripts produce byte-identical catalog output
# (json.dump indent=2 + trailing newline), avoiding PS 5.1 JSON quirks (BOM,
# forward-slash escaping, reformatting existing entries).
$projectsJson = Join-Path $factoryRoot 'projects.json'
$registerScript = @'
import json, sys
catalog, name, root = sys.argv[1], sys.argv[2], sys.argv[3]
with open(catalog) as fh:
    data = json.load(fh)
gp = data.setdefault("governed_projects", [])
if not any(e.get("name") == name for e in gp):
    gp.append({"name": name, "root": root, "trusted_workspace": False,
               "required_files": ["AGENTS.md", "CLAUDE.md", "docs/CONOPS.md",
                                   "docs/HANDOFF.md", ".claude/CLAUDE.md"]})
    with open(catalog, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print("registered")
else:
    print("present")
'@
$regResult = ($registerScript | & $pythonExe @pythonArgs - $projectsJson $Name $Path)
if ($LASTEXITCODE -ne 0) { throw "projects.json registration failed for '$Name'" }
if ($regResult -match 'registered') {
    Write-Host "Added '$Name' to projects.json"
} else {
    Write-Host "Project '$Name' already present in projects.json; not modifying."
}

# Sync via the Python engine.
$omniFactory = Join-Path $factoryRoot 'scripts\omni_factory.py'

function Invoke-Sync {
    param([Parameter(Mandatory)][string[]]$Args)
    & $pythonExe @pythonArgs @Args
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

# ── Interactive project-definition flow (parity with bootstrap-project.sh) ─────

function Invoke-ProjectDefinition {
    param(
        [Parameter(Mandatory)][string]$ConopsPath,
        [Parameter(Mandatory)][string]$ProjectName
    )
    Write-Host "-- Define this project --"
    Write-Host "Answer each prompt (press Enter to leave as a placeholder):"
    Write-Host ""
    $mission     = Read-Host "Project mission (1-2 sentences - what is this for?)"
    $audience    = Read-Host "Primary audience or users"
    $deliverable = Read-Host "Primary deliverable or system role"
    $constraints = Read-Host "Key constraints or notable boundaries"
    if ([string]::IsNullOrWhiteSpace($mission))     { $mission     = "TODO: describe the project mission and audience." }
    if ([string]::IsNullOrWhiteSpace($audience))    { $audience    = "TODO: describe who this project serves." }
    if ([string]::IsNullOrWhiteSpace($deliverable)) { $deliverable = "TODO: describe the primary deliverable or system role." }
    if ([string]::IsNullOrWhiteSpace($constraints)) { $constraints = "TODO: describe key constraints, boundaries, or assumptions." }
    $today = Get-Date -Format 'yyyy-MM-dd'
    $body = @"
# $ProjectName CONOPS
Last updated: $today

## Mission

$mission

## Audience

$audience

## Primary Deliverable

$deliverable

## Constraints

$constraints

## Current State

- Governance scaffold bootstrapped from Agent Forge
- First-pass definition captured at bootstrap time

## Architecture

TODO: describe the major components, data flow, and source-of-truth docs.
"@
    [System.IO.File]::WriteAllText($ConopsPath, $body)
    Write-Host "  CONOPS.md written with your inputs."
}

# TTY detection: only prompt when stdin is an interactive console.
$isInteractive = (-not [System.Console]::IsInputRedirected) -and [Environment]::UserInteractive
$conopsPath = Join-Path $targetRoot 'docs\CONOPS.md'
$runDefine = $false
if ($NoDefine) {
    $runDefine = $false
} elseif ($Define) {
    $runDefine = $true
} elseif ($isInteractive) {
    $ans = Read-Host "Would you like to fill in the project definition now? [y/n]"
    if ($ans -match '^(y|yes)$') { $runDefine = $true }
    else { Write-Host "  Skipped. Edit docs\CONOPS.md whenever you are ready." }
}
if ($runDefine) { Invoke-ProjectDefinition -ConopsPath $conopsPath -ProjectName $Name }

Write-Host ""
Write-Host "Project '$Name' bootstrapped at $targetRoot"
Write-Host "Next:"
Write-Host "  1. cd $targetRoot"
Write-Host "  2. Open Claude Code here and invoke /onboarding-guide"

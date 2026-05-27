# Shared PowerShell helpers for Agent Forge bootstrap/deploy scripts.
# Dot-sourced by bootstrap-project.ps1, bootstrap-workstation.ps1,
# deploy-factory.ps1, and deploy-and-bootstrap.ps1.
#
# PowerShell 5.1-compatible. No external modules. Centralizes the Python
# resolver (with a real 3.10+ version gate), relative-path computation, the
# Windows symlink-or-copy fallback, a command-presence check, and opt-in
# winget provisioning of base prerequisites, so the entry scripts stay
# consistent.

function Test-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Install a package via winget. Returns $true on success, $false if winget is
# unavailable or the install reports failure. Idempotent (winget skips
# already-installed packages). Shared by bootstrap-workstation.ps1 and the
# opt-in provisioning path.
function Install-WingetPackage {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if (-not (Test-Command 'winget')) {
        Write-Warning "winget is not available. Install $Name manually."
        return $false
    }
    Write-Host "Installing $Name with winget ($Id)..."
    winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements
    return ($LASTEXITCODE -eq 0)
}

# Return the installed Node major version, or 0 if Node is absent.
function Get-NodeMajor {
    if (-not (Test-Command 'node')) { return 0 }
    $v = (& node --version) 2>$null
    if ($v -match 'v?(\d+)\.') { return [int]$matches[1] }
    return 0
}

# Refresh the current session's PATH from the Machine + User environment.
# winget-installed tools land in the persistent PATH but not the running
# session, so call this after an install before re-resolving a tool.
function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
}

# Scan PATH for a Python interpreter meeting the >= MinMajor.MinMinor floor.
# Returns an object with Exe (string), Pre (string[] prefix args, @('-3') for the
# py launcher else @()), and Version - or $null if none qualifies. Never throws.
function Find-Python {
    param(
        [int]$MinMajor = 3,
        [int]$MinMinor = 10
    )
    foreach ($candidate in @('python3', 'python', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        # Skip the Windows Store "App Execution Alias" stub: it prints
        # "Python was not found..." and, under ErrorActionPreference=Stop, that
        # native stderr would terminate the probe instead of falling through.
        if ($cmd.Source -and $cmd.Source -like '*\WindowsApps\*') { continue }
        if ($candidate -eq 'py') {
            $exe = 'py'
            $pre = @('-3')
        } else {
            $exe = $cmd.Source
            $pre = @()
        }
        # Probe defensively: a misbehaving candidate (alias stub, broken install)
        # must be skipped, never crash the caller.
        $verText = ''
        $savedEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try { $verText = (& $exe @pre --version 2>&1 | Out-String).Trim() }
        catch { $verText = '' }
        finally { $ErrorActionPreference = $savedEAP }
        if ($verText -match 'Python\s+(\d+)\.(\d+)') {
            $maj = [int]$matches[1]
            $min = [int]$matches[2]
            if ($maj -gt $MinMajor -or ($maj -eq $MinMajor -and $min -ge $MinMinor)) {
                return [pscustomobject]@{ Exe = $exe; Pre = $pre; Version = $verText }
            } else {
                Write-Warning "$candidate is $verText; need $MinMajor.$MinMinor+. Trying next candidate."
            }
        }
    }
    return $null
}

# Resolve a Python interpreter and ENFORCE the >= 3.10 floor the scripts advertise.
# With -AutoProvision, if no qualifying Python is found, install it via winget,
# refresh the session PATH, and re-scan once before giving up. Throws a clear
# message if still unavailable. Callers keep the `& $pythonExe @pythonArgs` shape.
function Resolve-Python {
    param(
        [int]$MinMajor = 3,
        [int]$MinMinor = 10,
        [switch]$AutoProvision
    )
    $found = Find-Python -MinMajor $MinMajor -MinMinor $MinMinor
    if ($found) { return $found }
    if ($AutoProvision) {
        Write-Host "Python $MinMajor.$MinMinor+ not found; auto-provisioning via winget (opt-in)..."
        [void](Install-WingetPackage -Id 'Python.Python.3.12' -Name 'Python 3.12')
        Update-SessionPath
        $found = Find-Python -MinMajor $MinMajor -MinMinor $MinMinor
        if ($found) { return $found }
    }
    throw "Python $MinMajor.$MinMinor+ not found on PATH. Install from https://www.python.org/downloads/windows/ and re-run (or pass -AutoProvision on a host where winget installs are permitted)."
}

# Opt-in: install missing base prerequisites (Python 3.10+, Git, Node 20+) via
# winget. Idempotent (winget skips installed). Refreshes the session PATH after
# installs. On a host without winget (or where it is policy-blocked), warns and
# returns so the caller's clean detect-and-fail path takes over - we never force
# an install on a locked-down enterprise machine.
function Invoke-PrerequisiteProvision {
    [CmdletBinding()]
    param(
        [int]$MinPyMajor = 3,
        [int]$MinPyMinor = 10
    )
    if (-not (Test-Command 'winget')) {
        Write-Warning "winget unavailable; cannot auto-provision. On a locked-down host, install Python 3.10+, Git, and Node.js LTS via your managed software portal, then re-run without -AutoProvision."
        return
    }
    if (-not (Find-Python -MinMajor $MinPyMajor -MinMinor $MinPyMinor)) {
        [void](Install-WingetPackage -Id 'Python.Python.3.12' -Name 'Python 3.12')
    }
    if (-not (Test-Command 'git')) {
        [void](Install-WingetPackage -Id 'Git.Git' -Name 'Git')
    }
    if ((Get-NodeMajor) -lt 20) {
        [void](Install-WingetPackage -Id 'OpenJS.NodeJS.LTS' -Name 'Node.js LTS')
    }
    Update-SessionPath
}

# Compute a relative path from a directory to a target file. PowerShell 5.1 has
# no [System.IO.Path]::GetRelativePath (PS7/.NET Core only), so use Uri.
# Returns a backslash-separated path. Falls back to the absolute target path on
# cross-drive inputs, where a relative path is impossible.
function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FromDir,
        [Parameter(Mandatory = $true)][string]$ToPath
    )
    $fromWithSep = if ($FromDir.EndsWith('\') -or $FromDir.EndsWith('/')) { $FromDir } else { $FromDir + '\' }
    $fromUri = [System.Uri]$fromWithSep
    $toUri = [System.Uri]$ToPath
    $rel = [System.Uri]::UnescapeDataString($fromUri.MakeRelativeUri($toUri).ToString())
    if ($rel -match '^[a-zA-Z]:' -or $rel -match '^file:') {
        return $ToPath
    }
    return $rel.Replace('/', '\')
}

# Create a managed link, falling back to a marked file copy when the OS refuses
# a symbolic link (native Windows without Developer Mode or elevation raises
# WinError 1314). Idempotent: skips an existing symlink, an existing managed
# copy, or an operator-authored file.
function New-ManagedLink {
    param(
        [Parameter(Mandatory = $true)][string]$LinkPath,
        [Parameter(Mandatory = $true)][string]$TargetRelative,
        [Parameter(Mandatory = $true)][string]$FallbackBody
    )
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LinkPath) | Out-Null

    $existing = Get-Item -LiteralPath $LinkPath -ErrorAction SilentlyContinue
    if ($existing -and $existing.LinkType -eq 'SymbolicLink') {
        Write-Host "  skip: $LinkPath (symlink already present)"
        return
    }
    if ((Test-Path $LinkPath) -and ((Get-Content -Raw $LinkPath) -match 'Managed by Agent Forge')) {
        Write-Host "  skip: $LinkPath (managed copy already present)"
        return
    }
    if (Test-Path $LinkPath) {
        Write-Host "  skip: $LinkPath (operator file present; not overwriting)"
        return
    }

    try {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $TargetRelative -ErrorAction Stop | Out-Null
        Write-Host "  linked: $LinkPath -> $TargetRelative"
        return
    } catch {
        Write-Warning "Symbolic link failed (needs Administrator or Windows Developer Mode). Falling back to a managed file copy."
    }

    [System.IO.File]::WriteAllText($LinkPath, $FallbackBody)
    Write-Warning "  '$LinkPath' is a COPY, not a link. Enable Developer Mode or run elevated and re-run for a real symlink."
}

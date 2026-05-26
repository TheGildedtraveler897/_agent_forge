# Shared PowerShell helpers for Agent Forge bootstrap/deploy scripts.
# Dot-sourced by bootstrap-project.ps1, bootstrap-workstation.ps1,
# deploy-factory.ps1, and deploy-and-bootstrap.ps1.
#
# PowerShell 5.1-compatible. No external modules. Centralizes the Python
# resolver (with a real 3.10+ version gate), relative-path computation, the
# Windows symlink-or-copy fallback, and a command-presence check so the four
# entry scripts stay consistent.

function Test-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Resolve a Python interpreter and ENFORCE the >= 3.10 floor that the scripts
# advertise. Returns an object with Exe (string), Pre (string[] prefix args,
# @('-3') for the py launcher else @()), and Version. Callers keep the
# `& $pythonExe @pythonArgs ...` invocation shape.
function Resolve-Python {
    param(
        [int]$MinMajor = 3,
        [int]$MinMinor = 10
    )
    foreach ($candidate in @('python3', 'python', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        if ($candidate -eq 'py') {
            $exe = 'py'
            $pre = @('-3')
        } else {
            $exe = $cmd.Source
            $pre = @()
        }
        $verText = (& $exe @pre --version 2>&1 | Out-String).Trim()
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
    throw "Python $MinMajor.$MinMinor+ not found on PATH. Install from https://www.python.org/downloads/windows/ and re-run."
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

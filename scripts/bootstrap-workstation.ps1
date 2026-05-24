# Windows workstation readiness helper for Agent Forge.
# Detection is safe by default. Pass -Install to use winget for common tools.

[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$IncludeClaudeCode,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: bootstrap-workstation.ps1 [-Install] [-IncludeClaudeCode]

Checks a native Windows workstation for Agent Forge prerequisites. With
-Install, uses winget when available to install Python, Git, and Node.js LTS.
If winget is unavailable, prints official install URLs.

Codex and Gemini runtime work on Windows is still best through WSL2 unless
their CLIs already work in native PowerShell.
"@
    exit 0
}

$ErrorActionPreference = 'Stop'

function Test-Command {
    param([Parameter(Mandatory=$true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

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

Write-Host "Agent Forge Windows workstation check"
Write-Host ""

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

if ($IncludeClaudeCode) {
    Write-Host ""
    Write-Host "Claude Code: install using Anthropic's current Windows instructions."
    Write-Host "After install, close this terminal, open a new PowerShell window, and run: claude --version"
}

Write-Host ""
Write-Host "Codex and Gemini on native Windows:"
Write-Host "  - Use WSL2 for Codex runtime validation unless codex --version already works here."
Write-Host "  - Use WSL2 for Gemini runtime validation unless gemini --version already works here."
Write-Host "  - PATH changes from winget may require closing and reopening PowerShell."
Write-Host ""
Write-Host "Next:"
Write-Host "  powershell.exe -ExecutionPolicy Bypass -File .\scripts\bootstrap-project.ps1 -Name <your-project>"

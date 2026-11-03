# Install the ESP32 skills into an agent harness on Windows.
#
#   .\install.ps1                          # into $HOME\.claude\skills
#   .\install.ps1 -Target C:\path\skills
#   .\install.ps1 -List                    # print skill names and exit
#   .\install.ps1 -DryRun                  # show what would be copied
#
# Copies only; it never deletes, and it leaves an existing skill directory
# alone unless -Force is given.

param(
    [string]$Target = (Join-Path $HOME ".claude\skills"),
    [switch]$List,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = Join-Path $Root "skills"

if (-not (Test-Path $SkillsDir)) {
    Write-Error "no skills directory next to this script"
    exit 1
}

$dirs = Get-ChildItem -Path $SkillsDir -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
        Sort-Object Name

if ($List) {
    $dirs | ForEach-Object { $_.Name }
    exit 0
}

$installed = 0
$skipped = 0

foreach ($dir in $dirs) {
    $dest = Join-Path $Target $dir.Name

    if ((Test-Path $dest) -and -not $Force) {
        $skipped++
        continue
    }

    if ($DryRun) {
        Write-Output "would install $($dir.Name) -> $dest"
        $installed++
        continue
    }

    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $dir.FullName "SKILL.md") -Destination (Join-Path $dest "SKILL.md") -Force

    $license = Join-Path $dir.FullName "LICENSE.txt"
    if (Test-Path $license) {
        Copy-Item $license -Destination (Join-Path $dest "LICENSE.txt") -Force
    }

    $reference = Join-Path $dir.FullName "reference"
    if (Test-Path $reference) {
        Copy-Item $reference -Destination $dest -Recurse -Force
    }

    $installed++
}

if ($DryRun) {
    Write-Output "$installed skill(s) would be installed into $Target"
} else {
    Write-Output "$installed skill(s) installed into $Target"
}
if ($skipped -gt 0) {
    Write-Output "$skipped already present, left alone (use -Force to overwrite)"
}

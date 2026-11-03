# Install ESP32 Agent Skills into a supported agent harness on Windows.
#
#   .\install.ps1 -Harness claude
#   .\install.ps1 -Harness codex
#   .\install.ps1 -Harness opencode
#   .\install.ps1 -Harness all
#   .\install.ps1 -Target C:\custom\skills -DryRun

param(
    [ValidateSet("claude", "codex", "opencode", "all")]
    [string]$Harness = "claude",
    [string]$Target,
    [switch]$List,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = Join-Path $Root "skills"

if (-not (Test-Path $SkillsDir)) {
    throw "no skills directory next to this script"
}

$dirs = Get-ChildItem -Path $SkillsDir -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($List) {
    $dirs | ForEach-Object { $_.Name }
    exit 0
}

if ($PSBoundParameters.ContainsKey("Target")) {
    $targets = @($Target)
} else {
    $targets = switch ($Harness) {
        "claude"   { @((Join-Path $HOME ".claude\skills")) }
        "codex"    { @((Join-Path $HOME ".agents\skills")) }
        "opencode" { @((Join-Path $HOME ".config\opencode\skills")) }
        "all"      { @(
            (Join-Path $HOME ".claude\skills"),
            (Join-Path $HOME ".agents\skills"),
            (Join-Path $HOME ".config\opencode\skills")
        ) }
    }
}

foreach ($destination in $targets) {
    $installed = 0
    $skipped = 0
    foreach ($dir in $dirs) {
        $dest = Join-Path $destination $dir.Name
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
            $targetReference = Join-Path $dest "reference"
            if (Test-Path $targetReference) {
                Remove-Item $targetReference -Recurse -Force
            }
            Copy-Item $reference -Destination $dest -Recurse -Force
        }
        $installed++
    }
    if ($DryRun) {
        Write-Output "$installed skill(s) would be installed into $destination"
    } else {
        Write-Output "$installed skill(s) installed into $destination"
    }
    if ($skipped -gt 0) {
        Write-Output "$skipped already present, left alone (use -Force to overwrite)"
    }
}

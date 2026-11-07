# Installs the Humming Bird plugin into the Hermes plugins directory.
param(
    [string]$HermesHome = ""
)

$ErrorActionPreference = "Stop"

if (-not $HermesHome) {
    if ($env:HERMES_HOME) {
        $HermesHome = $env:HERMES_HOME
    } else {
        $HermesHome = Join-Path $env:LOCALAPPDATA "hermes"
    }
}

$sourceDir = Resolve-Path (Join-Path $PSScriptRoot "..\plugins\humming_bird")
$pluginsDir = Join-Path $HermesHome "plugins"
$targetDir = Join-Path $pluginsDir "humming_bird"

if (-not (Test-Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
}

Write-Host "Installing Humming Bird plugin..."
Write-Host "  Source: $sourceDir"
Write-Host "  Destination: $targetDir"

if (Test-Path $targetDir) {
    Remove-Item -Recurse -Force $targetDir
}

try {
    New-Item -ItemType Junction -Path $targetDir -Target $sourceDir -Force -ErrorAction Stop | Out-Null
    Write-Host "Linked via directory junction to $sourceDir"
} catch {
    Copy-Item -Path $sourceDir -Destination $targetDir -Recurse -Force
    Write-Host "Copied plugin files to $targetDir"
}

Write-Host "Humming Bird plugin installed successfully."


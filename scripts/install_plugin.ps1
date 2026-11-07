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

# Also install into hummingbird profile plugins if profile exists
$hbProfilePlugins = Join-Path $HermesHome "profiles\hummingbird\plugins"
if (Test-Path (Join-Path $HermesHome "profiles\hummingbird")) {
    if (-not (Test-Path $hbProfilePlugins)) {
        New-Item -ItemType Directory -Path $hbProfilePlugins -Force | Out-Null
    }
    $hbTargetDir = Join-Path $hbProfilePlugins "humming_bird"
    if (Test-Path $hbTargetDir) {
        Remove-Item -Recurse -Force $hbTargetDir
    }
    try {
        New-Item -ItemType Junction -Path $hbTargetDir -Target $sourceDir -Force -ErrorAction Stop | Out-Null
        Write-Host "Linked to hummingbird profile via directory junction"
    } catch {
        Copy-Item -Path $sourceDir -Destination $hbTargetDir -Recurse -Force
        Write-Host "Copied plugin files to hummingbird profile: $hbTargetDir"
    }
}

# Also install cron script into Hermes scripts directories
$cronScriptSrc = Resolve-Path (Join-Path $PSScriptRoot "check_dse_market_open.py")
$baseScriptsDir = Join-Path $HermesHome "scripts"
if (-not (Test-Path $baseScriptsDir)) {
    New-Item -ItemType Directory -Path $baseScriptsDir -Force | Out-Null
}
Copy-Item -Path $cronScriptSrc -Destination (Join-Path $baseScriptsDir "check_dse_market_open.py") -Force

if (Test-Path (Join-Path $HermesHome "profiles\hummingbird")) {
    $hbScriptsDir = Join-Path $HermesHome "profiles\hummingbird\scripts"
    if (-not (Test-Path $hbScriptsDir)) {
        New-Item -ItemType Directory -Path $hbScriptsDir -Force | Out-Null
    }
    Copy-Item -Path $cronScriptSrc -Destination (Join-Path $hbScriptsDir "check_dse_market_open.py") -Force
    Write-Host "Installed check_dse_market_open.py to hummingbird scripts directory"
}

Write-Host "Humming Bird plugin installed successfully."


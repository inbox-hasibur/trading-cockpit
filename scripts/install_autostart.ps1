<#
.SYNOPSIS
    Installs Humming Bird Trading Cockpit autostart via Windows Task Scheduler.

.DESCRIPTION
    1. Registers a Windows Task Scheduler entry ("HummingBirdTradingCockpit") to run at user logon.
    2. Configures auto-restart on failure (RestartCount: 3, RestartInterval: 1 minute).
    3. Configures powercfg to prevent system sleep/hibernation while plugged into AC power.
    4. Explains the post-reboot WAITING recovery lifecycle.

.EXAMPLE
    .\scripts\install_autostart.ps1
    .\scripts\install_autostart.ps1 -Uninstall
#>

[CmdletBinding()]
param(
    [string]$TaskName = "HummingBirdTradingCockpit",
    [switch]$Uninstall,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$workspaceRoot = (Get-Item $PSScriptRoot).Parent.FullName
$venvPython = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
$runScript = Join-Path $workspaceRoot "run.py"

if ($Uninstall) {
    Write-Host "Removing scheduled task: $TaskName..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Scheduled task $TaskName uninstalled." -ForegroundColor Green
    return
}

# 1. Validation
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment python not found at $venvPython. Run poetry install or setup .venv first."
    exit 1
}
if (-not (Test-Path $runScript)) {
    Write-Error "Supervisor script not found at $runScript."
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Humming Bird Autostart & Power Management Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 2. Configure Power Settings (Prevent sleep & hibernation on AC)
Write-Host "[1/3] Configuring Windows power settings..." -ForegroundColor Yellow
try {
    # Disable standby timeout on AC (Never sleep)
    powercfg /change standby-timeout-ac 0
    # Disable hibernate timeout on AC (Never hibernate)
    powercfg /change hibernate-timeout-ac 0
    Write-Host "  -> powercfg: Standby on AC set to NEVER (0)" -ForegroundColor Green
    Write-Host "  -> powercfg: Hibernate on AC set to NEVER (0)" -ForegroundColor Green
    Write-Host "  -> Note: Monitor standby remains untouched for display sleep." -ForegroundColor DarkGray
} catch {
    Write-Warning "Failed to set powercfg parameters (may require administrative privileges): $_"
}

# 3. Create Scheduled Task Action & Trigger
Write-Host "[2/3] Configuring Task Scheduler entry for user: $env:USERNAME..." -ForegroundColor Yellow

# Action: launch supervisor run.py with --no-reload
$action = New-ScheduledTaskAction `
    -Execute $venvPython `
    -Argument "`"$runScript`" --no-reload" `
    -WorkingDirectory $workspaceRoot

# Trigger: at logon of current user
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: restart on failure up to 3 times, interval 1 minute
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# Register or overwrite task
try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        if ($Force) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        } else {
            Write-Host "  -> Updating existing scheduled task $TaskName..." -ForegroundColor DarkYellow
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
    }

    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Humming Bird DSE Trading Cockpit & Hermes Gateway supervisor autostart" | Out-Null

    Write-Host "  -> Scheduled task '$TaskName' registered successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to register scheduled task: $_"
    exit 1
}

# 4. Post-Reboot Lifecycle Information
Write-Host "[3/3] Autostart Verification & Post-Reboot Lifecycle:" -ForegroundColor Yellow
Write-Host "  1. On PC reboot or user logon, Windows Task Scheduler launches 'run.py --no-reload'."
Write-Host "  2. run.py starts Hermes Gateway on 127.0.0.1:8642, then starts Cockpit on 127.0.0.1:8000."
Write-Host "  3. In case of unexpected process crash, Task Scheduler automatically restarts up to 3 times (1m interval)."
Write-Host "  4. SAFETY INVARIANT: If automation was active, it is restored into a 'WAITING' state."
Write-Host "     AutoTrader skips order cycles until startup health verification (DB, StockNow, Caps) passes."
Write-Host "     Once health checks pass, state transitions to 'READY', resuming automated operations."
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete! Autostart is ready and power sleep is prevented." -ForegroundColor Green


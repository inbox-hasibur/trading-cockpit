# Unified launcher for Humming Bird Trading Cockpit and Hermes Agent Gateway.
# Starts Hermes Gateway on 127.0.0.1:8642 and FastAPI/Uvicorn on 127.0.0.1:8000.
# Handles automatic gateway restarts (up to 3) and clean shutdown on Ctrl+C.

$ErrorActionPreference = "Continue"

# 1. Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = Get-Location }
Set-Location $ScriptDir

# Set HERMES_HOME explicitly (known Windows default bug where CLI confuses AppData vs ~/.hermes)
$LocalApp = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::LocalApplicationData)
if (-not $env:HERMES_HOME) {
    $env:HERMES_HOME = Join-Path $LocalApp "hermes"
}

# Locate hermes executable
$HermesBin = Join-Path $env:HERMES_HOME "bin\hermes.exe"
if (-not (Test-Path $HermesBin)) {
    $HermesCmd = Get-Command "hermes" -ErrorAction SilentlyContinue
    if ($HermesCmd) {
        $HermesBin = $HermesCmd.Source
    } else {
        Write-Error "Could not locate hermes executable at $HermesBin or in PATH."
        exit 1
    }
}

# Locate python virtualenv
$PythonBin = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    $PythonBin = "python"
}

# 2. Load environment variables from .env if present
$EnvFiles = @(Join-Path $ScriptDir ".env", Join-Path $ScriptDir "backend\.env")
foreach ($ef in $EnvFiles) {
    if (Test-Path $ef) {
        Get-Content $ef | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
                $parts = $line.Split("=", 2)
                $name = $parts[0].Trim()
                $val = $parts[1].Trim().Trim('"').Trim("'")
                if (-not [System.Environment]::GetEnvironmentVariable($name, "Process")) {
                    [System.Environment]::SetEnvironmentVariable($name, $val, "Process")
                }
            }
        }
    }
}

# Ensure critical defaults
if (-not $env:KERNEL_TOKEN) { $env:KERNEL_TOKEN = "hb-kernel-local-token-2026" }
if (-not $env:API_SERVER_KEY) { $env:API_SERVER_KEY = "hb-hermes-local-key-2026" }
$env:API_SERVER_ENABLED = "true"
$env:API_SERVER_PORT = "8642"
$env:API_SERVER_HOST = "127.0.0.1"
$env:HERMES_GATEWAY_URL = "http://127.0.0.1:8642"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Humming Bird Cockpit & Hermes Gateway Unified Runner   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "HERMES_HOME : $env:HERMES_HOME" -ForegroundColor DarkGray
Write-Host "Hermes Bin  : $HermesBin" -ForegroundColor DarkGray
Write-Host "Profile     : hummingbird" -ForegroundColor DarkGray
Write-Host "Gateway URL : http://127.0.0.1:8642" -ForegroundColor DarkGray
Write-Host "Cockpit URL : http://127.0.0.1:8000" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

$Global:GatewayProc = $null
$Global:BackendProc = $null
$Global:MaxRestarts = 3
$Global:RestartCount = 0
$Global:ShutdownRequested = $false

function Stop-AllProcesses {
    $Global:ShutdownRequested = $true
    Write-Host "`nStopping Humming Bird Cockpit and Hermes Gateway..." -ForegroundColor Yellow

    if ($Global:BackendProc -and -not $Global:BackendProc.HasExited) {
        try {
            $Global:BackendProc.Kill()
            Write-Host "Stopped Uvicorn backend (PID $($Global:BackendProc.Id))" -ForegroundColor DarkGray
        } catch {}
    }
    if ($Global:GatewayProc -and -not $Global:GatewayProc.HasExited) {
        try {
            $Global:GatewayProc.Kill()
            Write-Host "Stopped Hermes Gateway (PID $($Global:GatewayProc.Id))" -ForegroundColor DarkGray
        } catch {}
    }
}

# Register Ctrl+C handler
[Console]::TreatControlCAsInput = $false
$cancelHandler = [ConsoleCancelEventHandler]{
    param($sender, $e)
    $e.Cancel = $true
    Stop-AllProcesses
}
[Console]::add_CancelKeyPress($cancelHandler)

function Start-GatewayProcess {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $HermesBin
    $psi.Arguments = "-p hummingbird gateway run --force"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $false
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError = $false

    # Propagate process environment
    foreach ($de in [System.Environment]::GetEnvironmentVariables("Process").GetEnumerator()) {
        if (-not $psi.EnvironmentVariables.ContainsKey($de.Key)) {
            $psi.EnvironmentVariables.Add($de.Key, $de.Value)
        }
    }

    $proc = [System.Diagnostics.Process]::Start($psi)
    return $proc
}

function Wait-ForGatewayHealth([int]$TimeoutSec = 30) {
    Write-Host "Waiting for Hermes Gateway on 127.0.0.1:8642..." -NoNewline -ForegroundColor Gray
    $elapsed = 0
    while ($elapsed -lt $TimeoutSec) {
        if ($Global:GatewayProc.HasExited) {
            Write-Host " FAILED (Gateway process exited unexpectedly)" -ForegroundColor Red
            return $false
        }
        try {
            $req = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:8642/health")
            $req.Timeout = 1000
            $req.Method = "GET"
            $resp = $req.GetResponse()
            if ($resp.StatusCode -eq [System.Net.HttpStatusCode]::OK) {
                $resp.Close()
                Write-Host " HEALTHY" -ForegroundColor Green
                return $true
            }
            $resp.Close()
        } catch {
            Start-Sleep -Milliseconds 500
            $elapsed += 0.5
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    Write-Host " TIMEOUT" -ForegroundColor Red
    return $false
}

try {
    # Start Gateway initially
    Write-Host "Starting Hermes Gateway (profile: hummingbird)..." -ForegroundColor Yellow
    $Global:GatewayProc = Start-GatewayProcess

    $healthy = Wait-ForGatewayHealth -TimeoutSec 30
    if (-not $healthy) {
        Write-Error "Hermes Gateway failed to start or report healthy on http://127.0.0.1:8642"
        Stop-AllProcesses
        exit 1
    }

    # Start Uvicorn backend
    Write-Host "Starting Cockpit Uvicorn backend on 127.0.0.1:8000..." -ForegroundColor Yellow
    $upsi = New-Object System.Diagnostics.ProcessStartInfo
    $upsi.FileName = $PythonBin
    $upsi.Arguments = "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
    $upsi.UseShellExecute = $false
    $upsi.CreateNoWindow = $false

    foreach ($de in [System.Environment]::GetEnvironmentVariables("Process").GetEnumerator()) {
        if (-not $upsi.EnvironmentVariables.ContainsKey($de.Key)) {
            $upsi.EnvironmentVariables.Add($de.Key, $de.Value)
        }
    }

    $Global:BackendProc = [System.Diagnostics.Process]::Start($upsi)

    Write-Host "`nAll services active!" -ForegroundColor Green
    Write-Host "Cockpit UI available at: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to terminate all services.`n" -ForegroundColor DarkGray

    # Supervisor monitoring loop
    while (-not $Global:ShutdownRequested) {
        Start-Sleep -Seconds 1

        # Check backend
        if ($Global:BackendProc.HasExited) {
            Write-Host "Backend server exited with code $($Global:BackendProc.ExitCode). Shutting down." -ForegroundColor Red
            break
        }

        # Check gateway
        if ($Global:GatewayProc.HasExited -and -not $Global:ShutdownRequested) {
            $Global:RestartCount++
            Write-Host "`n[ALERT] Hermes Gateway process exited unexpectedly (Exit code: $($Global:GatewayProc.ExitCode))" -ForegroundColor Red
            if ($Global:RestartCount -le $Global:MaxRestarts) {
                Write-Host "[SUPERVISOR] Restarting Hermes Gateway (Attempt $Global:RestartCount of $Global:MaxRestarts)..." -ForegroundColor Yellow
                $Global:GatewayProc = Start-GatewayProcess
                $healthy = Wait-ForGatewayHealth -TimeoutSec 20
                if ($healthy) {
                    Write-Host "[SUPERVISOR] Gateway successfully recovered and healthy!" -ForegroundColor Green
                } else {
                    Write-Host "[SUPERVISOR] Gateway recovery failed to reach healthy state." -ForegroundColor Red
                }
            } else {
                Write-Host "[ERROR] Hermes Gateway has crashed repeatedly (exceeded $Global:MaxRestarts restarts)." -ForegroundColor Red
                Write-Host "Please check the gateway logs and configuration." -ForegroundColor Red
                break
            }
        }
    }
} finally {
    Stop-AllProcesses
}

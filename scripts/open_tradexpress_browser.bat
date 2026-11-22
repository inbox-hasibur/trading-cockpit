@echo off
REM ============================================================================
REM TradeXpress 2.0 Safe Isolated Browser Launcher for Humming Bird CDP Spy
REM
REM ZERO-BAN MANDATE:
REM Launches Microsoft Edge or Google Chrome with an isolated user-data-dir and
REM exposes Chrome DevTools Protocol (CDP) on port 9222.
REM
REM The operator must log in MANUALLY on https://itrade.lbsbd.com.
REM Humming Bird connects passively over port 9222 to read incoming WebSocket
REM frames and DOM tables with ZERO active HTTP scraping or automated typing.
REM ============================================================================

setlocal EnableDelayedExpansion

set "CDP_PORT=9222"
set "USER_DATA_DIR=%LOCALAPPDATA%\HummingBird\TradeXpressBrowser"
set "TARGET_URL=https://itrade.lbsbd.com"

echo ============================================================================
echo   Humming Bird -- TradeXpress 2.0 Safe Isolated Browser Launcher
echo ============================================================================
echo.
echo CDP Debug Port: %CDP_PORT%
echo User Data Dir:  %USER_DATA_DIR%
echo Target URL:     %TARGET_URL%
echo.

if not exist "%USER_DATA_DIR%" (
    mkdir "%USER_DATA_DIR%"
)

set "BROWSER_EXE="

if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER_EXE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER_EXE=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

if "%BROWSER_EXE%"=="" (
    echo [ERROR] Neither Microsoft Edge nor Google Chrome was found at standard locations.
    echo Please install Microsoft Edge or Google Chrome to use TradeXpress CDP Spy.
    pause
    exit /b 1
)

echo [OK] Launching browser: "%BROWSER_EXE%"
echo.
echo ============================================================================
echo NEXT STEPS FOR OPERATOR:
echo   1. The browser will open to https://itrade.lbsbd.com
echo   2. Log in MANUALLY with your LankaBangla account credentials (e.g. H9210)
echo   3. Keep this browser window OPEN while Humming Bird runs
echo   4. In Humming Bird Cockpit, click 'Passive Spy: ON' or call the bridge API
echo ============================================================================
echo.

start "" "%BROWSER_EXE%" --remote-debugging-port=%CDP_PORT% --user-data-dir="%USER_DATA_DIR%" --no-first-run --no-default-browser-check "%TARGET_URL%"

exit /b 0

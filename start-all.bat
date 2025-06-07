@echo off
REM Cumpair - Quick Start Batch File
REM Simple wrapper for PowerShell startup script

echo.
echo ========================================
echo    🔍 CUMPAIR QUICK LAUNCHER
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ PowerShell not found! Please install PowerShell.
    pause
    exit /b 1
)

REM Parse command line arguments
set "ARGS="
if "%1"=="-full" set "ARGS=-Full"
if "%1"=="-minimal" set "ARGS=-Minimal"
if "%1"=="-stop" set "ARGS=-Stop"
if "%1"=="-status" set "ARGS=-Status"
if "%1"=="-help" set "ARGS=-Help"
if "%1"=="--help" set "ARGS=-Help"
if "%1"=="/?" set "ARGS=-Help"

REM If no arguments, show help
if "%1"=="" (
    echo Usage:
    echo   start-all.bat [option]
    echo.
    echo Options:
    echo   -full      Start all services ^(recommended^)
    echo   -minimal   Start core services only
    echo   -stop      Stop all services
    echo   -status    Check service status
    echo   -help      Show detailed help
    echo.
    echo Examples:
    echo   start-all.bat -full     ^(Start everything^)
    echo   start-all.bat -minimal  ^(Quick start^)
    echo.
    set /p choice="Press Enter to start with full configuration, or Ctrl+C to cancel: "
    set "ARGS=-Full"
)

REM Run PowerShell script
echo Starting Cumpair services...
powershell -ExecutionPolicy Bypass -File "start-all.ps1" %ARGS%

if %errorlevel% neq 0 (
    echo.
    echo ❌ Something went wrong! Check the output above.
    pause
) else (
    echo.
    echo ✅ Done! Check the output above for service URLs.
    echo Press any key to exit...
    pause >nul
)

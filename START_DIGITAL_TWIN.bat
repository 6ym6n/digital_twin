@echo off
REM ==============================================================================
REM DIGITAL TWIN - ONE-CLICK LAUNCHER
REM Double-cliquez sur ce fichier pour lancer tout le système
REM ==============================================================================

title Digital Twin - Launcher
color 0B

echo.
echo ===============================================================
echo   DIGITAL TWIN - GRUNDFOS CR 15 PUMP
echo   Demarrage automatique du systeme...
echo ===============================================================
echo.

cd /d "%~dp0"

REM Lancer le script PowerShell
powershell -ExecutionPolicy Bypass -File "%~dp0start_system.ps1" -Source matlab

pause

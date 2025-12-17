@echo off
echo.
echo ================================================
echo   MATLAB Digital Twin - Auto Start Script
echo   MQTT Pump Simulation
echo ================================================
echo.

cd /d "%~dp0"

echo Starting MATLAB and loading MQTT Digital Twin...
echo.
echo NOTE: This script will attempt to launch MATLAB and run the simulation.
echo       If MATLAB is not in your PATH, you may need to:
echo       1. Open MATLAB manually
echo       2. Navigate to this project folder
echo       3. Run: addpath('matlab'); mqtt_digital_twin;
echo.

:: Try to find MATLAB executable
set MATLAB_EXE=matlab.exe

:: Check if MATLAB is in PATH
where %MATLAB_EXE% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found MATLAB in system PATH
    echo Launching MATLAB with simulation script...
    echo.
    %MATLAB_EXE% -r "addpath('matlab'); mqtt_digital_twin; disp('MQTT Digital Twin is running. Press Ctrl+C to stop.');"
) else (
    echo.
    echo ⚠️  MATLAB not found in system PATH
    echo.
    echo Please start MATLAB manually and run these commands:
    echo.
    echo    ^> addpath('matlab');
    echo    ^> mqtt_digital_twin;
    echo.
    echo Or configure explicitly with:
    echo    ^> mqtt_digital_twin('Host','localhost','Port',1883,'PumpId','pump01');
    echo.
    pause
)

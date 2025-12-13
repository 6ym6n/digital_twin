@echo off
REM ================================================================
REM Digital Twin - Start Backend with MATLAB Source
REM ================================================================

echo.
echo ===============================================================
echo   DIGITAL TWIN - MATLAB MODE
echo ===============================================================
echo.

REM Set environment variable for MATLAB data source
set DT_DATA_SOURCE=matlab
set DT_TCP_PORT=5555

echo Data Source: MATLAB
echo TCP Port: %DT_TCP_PORT%
echo.
echo Starting backend server...
echo (Make sure to start MATLAB simulation after this)
echo.
echo In MATLAB, run:
echo   ^>^> cd matlab
echo   ^>^> startup_digital_twin
echo.
echo ===============================================================
echo.

cd /d %~dp0
python backend\api.py

pause

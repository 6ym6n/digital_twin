@echo off
REM ================================================================
REM Digital Twin - Start MATLAB Bridge Standalone
REM ================================================================

echo.
echo ===============================================================
echo   MATLAB BRIDGE - STANDALONE TCP SERVER
echo ===============================================================
echo.
echo This starts only the TCP server for MATLAB communication.
echo Use this for testing or when running frontend separately.
echo.
echo TCP Server will listen on port 5555
echo.
echo In MATLAB, run:
echo   ^>^> run_simulation('port', 5555)
echo.
echo ===============================================================
echo.

cd /d %~dp0
python -m src.matlab_bridge --server --port 5555

pause

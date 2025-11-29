@echo off
echo.
echo ================================================
echo   DIGITAL TWIN - Frontend Dev Server
echo   React on http://localhost:3000
echo ================================================
echo.

cd /d "%~dp0\frontend"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

:: Start dev server
call npm run dev

@echo off
echo.
echo ================================================
echo   DIGITAL TWIN - Backend Server
echo   FastAPI on http://localhost:8000
echo ================================================
echo.

cd /d "%~dp0"

:: Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Run the backend
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload

pause

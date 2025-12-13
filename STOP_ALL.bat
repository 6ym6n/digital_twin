@echo off
chcp 65001 >nul
title 🛑 Digital Twin - Arrêt
color 0C

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🛑 ARRÊT DU SYSTÈME DIGITAL TWIN                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo Arrêt des processus...

REM Arrêter les processus sur le port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Arrêt du Backend (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Arrêter les processus sur le port 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo   Arrêt du Frontend (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Arrêter les processus sur le port 5555 (TCP MATLAB)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5555 ^| findstr LISTENING') do (
    echo   Arrêt du TCP Server (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Fermer les fenêtres de commande associées
taskkill /F /FI "WINDOWTITLE eq 🐍 Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ⚛️ Frontend*" >nul 2>&1

echo.
echo ✅ Tous les services ont été arrêtés.
echo.
timeout /t 3

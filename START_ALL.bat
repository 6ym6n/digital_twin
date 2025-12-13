@echo off
chcp 65001 >nul
title 🏭 Digital Twin - Grundfos CR 15
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║   🏭  DIGITAL TWIN - GRUNDFOS CR 15 PUMP                     ║
echo ║       Système de Maintenance Prédictive                      ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ================================================================
REM ÉTAPE 1: Vérifications préliminaires
REM ================================================================
echo [1/5] Vérifications préliminaires...

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo     ❌ ERREUR: Python n'est pas installé ou pas dans le PATH
    echo     Installez Python 3.10+ depuis https://python.org
    pause
    exit /b 1
)
echo     ✓ Python trouvé

REM Vérifier Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo     ❌ ERREUR: Node.js n'est pas installé ou pas dans le PATH
    echo     Installez Node.js depuis https://nodejs.org
    pause
    exit /b 1
)
echo     ✓ Node.js trouvé

REM Vérifier le virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo     ❌ ERREUR: Virtual environment non trouvé
    echo     Créez-le avec: python -m venv venv
    pause
    exit /b 1
)
echo     ✓ Virtual environment trouvé

REM Vérifier les dépendances frontend
if not exist "frontend\node_modules" (
    echo     ⚠ Modules frontend manquants, installation...
    cd frontend
    call npm install
    cd ..
)
echo     ✓ Dépendances frontend OK

echo.

REM ================================================================
REM ÉTAPE 2: Arrêt des processus existants
REM ================================================================
echo [2/5] Arrêt des processus existants...

REM Tuer les processus sur les ports utilisés
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5555 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo     ✓ Ports libérés (8000, 3000, 5555)
echo.

REM ================================================================
REM ÉTAPE 3: Démarrage du Backend Python
REM ================================================================
echo [3/5] Démarrage du Backend Python...

start "🐍 Backend Python - Port 8000" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python backend\api.py"

REM Attendre que le backend soit prêt
echo     ⏳ Attente du backend...
set /a count=0
:wait_backend
timeout /t 1 /nobreak >nul
set /a count+=1
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    if %count% LSS 30 (
        goto wait_backend
    ) else (
        echo     ❌ ERREUR: Le backend n'a pas démarré après 30 secondes
        pause
        exit /b 1
    )
)
echo     ✓ Backend démarré sur http://localhost:8000
echo.

REM ================================================================
REM ÉTAPE 4: Démarrage du Frontend React
REM ================================================================
echo [4/5] Démarrage du Frontend React...

start "⚛️ Frontend React - Port 3000" cmd /k "cd /d "%~dp0%frontend" && npm run dev"

REM Attendre que le frontend soit prêt
echo     ⏳ Attente du frontend...
set /a count=0
:wait_frontend
timeout /t 1 /nobreak >nul
set /a count+=1
curl -s http://localhost:3000/ >nul 2>&1
if errorlevel 1 (
    if %count% LSS 20 (
        goto wait_frontend
    ) else (
        echo     ⚠ Frontend peut prendre plus de temps, continuons...
    )
)
echo     ✓ Frontend démarré sur http://localhost:3000
echo.

REM ================================================================
REM ÉTAPE 5: Ouverture du navigateur
REM ================================================================
echo [5/5] Ouverture du Dashboard...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ✅ SYSTÈME PRÊT !                        ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║   🌐 Dashboard:  http://localhost:3000                       ║
echo ║   🔌 API:        http://localhost:8000                       ║
echo ║   📡 TCP MATLAB: Port 5555                                   ║
echo ║                                                              ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║   📋 ÉTAPE SUIVANTE - Dans MATLAB, exécutez:                 ║
echo ║                                                              ║
echo ║   cd('C:\projetMaintenanceV2\digital_twin\matlab')           ║
echo ║   run_simulation('scenario', 'demo', 'duration', 300)        ║
echo ║                                                              ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║   Scénarios disponibles:                                     ║
echo ║     • 'demo'       - Demo 5 min avec pannes                  ║
echo ║     • 'normal'     - Fonctionnement normal                   ║
echo ║     • 'winding'    - Défaut bobinage                         ║
echo ║     • 'cavitation' - Cavitation                              ║
echo ║     • 'bearing'    - Usure roulement                         ║
echo ║     • 'overload'   - Surcharge                               ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Appuyez sur une touche pour fermer cette fenêtre...
echo (Les serveurs continueront à fonctionner)
pause >nul

#==============================================================================
# DIGITAL TWIN - SYSTEM LAUNCHER
# Script PowerShell pour démarrer tout le système automatiquement
#==============================================================================

param(
    [Parameter()]
    [ValidateSet("python", "matlab")]
    [string]$Source = "matlab",
    
    [Parameter()]
    [switch]$NoFrontend,
    
    [Parameter()]
    [switch]$LaunchMatlab
)

$Host.UI.RawUI.WindowTitle = "Digital Twin Launcher"

# Couleurs
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) { Write-Output $args }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Banner {
    Write-Host ""
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host "  🏭  DIGITAL TWIN - GRUNDFOS CR 15 PUMP" -ForegroundColor Cyan
    Write-Host "  🚀  System Launcher" -ForegroundColor Cyan
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status($message, $status) {
    $icon = switch ($status) {
        "OK" { "✅" }
        "WAIT" { "⏳" }
        "ERROR" { "❌" }
        "INFO" { "ℹ️" }
        default { "•" }
    }
    Write-Host "  $icon $message"
}

function Stop-ExistingProcesses {
    Write-Host "`n📋 Arrêt des processus existants..." -ForegroundColor Yellow
    
    # Arrêter les serveurs Node.js sur port 3000
    $nodeProcesses = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | 
                     Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $nodeProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Status "Arrêt du processus Node.js (PID: $pid)" "OK"
    }
    
    # Arrêter les serveurs Python sur port 8000
    $pythonProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
                       Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pythonProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Status "Arrêt du processus Python (PID: $pid)" "OK"
    }
    
    Start-Sleep -Seconds 2
}

function Test-Port($port) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Wait-ForBackend {
    Write-Host "`n⏳ Attente du backend..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET -TimeoutSec 2 -ErrorAction Stop
            if ($response.status -eq "online") {
                Write-Status "Backend prêt!" "OK"
                return $true
            }
        } catch {
            # Ignorer l'erreur et réessayer
        }
        $attempt++
        Start-Sleep -Milliseconds 500
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    Write-Status "Backend non disponible après $maxAttempts tentatives" "ERROR"
    return $false
}

function Switch-ToMatlabSource {
    Write-Host "`n🔄 Configuration de la source MATLAB..." -ForegroundColor Yellow
    try {
        $body = '{"source": "matlab"}'
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/switch-source" `
                                      -Method POST `
                                      -ContentType "application/json" `
                                      -Body $body `
                                      -ErrorAction Stop
        Write-Status "Source configurée: MATLAB" "OK"
        return $true
    } catch {
        Write-Status "Erreur lors du switch: $_" "ERROR"
        return $false
    }
}

function Start-Backend {
    Write-Host "`n🐍 Démarrage du Backend Python..." -ForegroundColor Yellow
    
    $backendPath = Join-Path $PSScriptRoot "backend\api.py"
    $venvActivate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
    
    if (-not (Test-Path $venvActivate)) {
        Write-Status "Virtual environment non trouvé!" "ERROR"
        return $false
    }
    
    # Démarrer le backend dans une nouvelle fenêtre
    $command = "cd '$PSScriptRoot'; & '$venvActivate'; python backend\api.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $command -WindowStyle Normal
    
    Write-Status "Backend lancé dans une nouvelle fenêtre" "OK"
    return $true
}

function Start-Frontend {
    Write-Host "`n⚛️  Démarrage du Frontend React..." -ForegroundColor Yellow
    
    $frontendPath = Join-Path $PSScriptRoot "frontend"
    
    if (-not (Test-Path (Join-Path $frontendPath "package.json"))) {
        Write-Status "Frontend non trouvé!" "ERROR"
        return $false
    }
    
    # Démarrer le frontend dans une nouvelle fenêtre
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev" -WindowStyle Normal
    
    Write-Status "Frontend lancé dans une nouvelle fenêtre" "OK"
    return $true
}

function Show-MatlabInstructions {
    Write-Host ""
    Write-Host "===============================================================" -ForegroundColor Green
    Write-Host "  📡 INSTRUCTIONS MATLAB" -ForegroundColor Green
    Write-Host "===============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Dans MATLAB, exécutez ces commandes:" -ForegroundColor White
    Write-Host ""
    Write-Host "    cd('$PSScriptRoot\matlab')" -ForegroundColor Cyan
    Write-Host "    run_simulation('scenario', 'demo', 'duration', 300)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Scénarios disponibles:" -ForegroundColor White
    Write-Host "    • 'normal'     - Fonctionnement normal" -ForegroundColor Gray
    Write-Host "    • 'demo'       - Demo 5 min avec pannes" -ForegroundColor Gray
    Write-Host "    • 'winding'    - Défaut bobinage" -ForegroundColor Gray
    Write-Host "    • 'cavitation' - Cavitation" -ForegroundColor Gray
    Write-Host "    • 'bearing'    - Usure roulement" -ForegroundColor Gray
    Write-Host "    • 'overload'   - Surcharge" -ForegroundColor Gray
    Write-Host ""
}

function Show-SystemStatus {
    Write-Host ""
    Write-Host "===============================================================" -ForegroundColor Green
    Write-Host "  ✅ SYSTÈME PRÊT" -ForegroundColor Green
    Write-Host "===============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  🌐 Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "  🔌 Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "  📡 TCP Port:  5555 (pour MATLAB)" -ForegroundColor White
    Write-Host ""
}

# =============================================================================
# MAIN
# =============================================================================

Write-Banner

Write-Host "  Mode: $Source" -ForegroundColor White
Write-Host "  Frontend: $(if ($NoFrontend) { 'Désactivé' } else { 'Activé' })" -ForegroundColor White

# 1. Arrêter les processus existants
Stop-ExistingProcesses

# 2. Démarrer le backend
if (-not (Start-Backend)) {
    Write-Host "`n❌ Impossible de démarrer le backend" -ForegroundColor Red
    exit 1
}

# 3. Attendre que le backend soit prêt
if (-not (Wait-ForBackend)) {
    Write-Host "`n❌ Le backend n'a pas démarré correctement" -ForegroundColor Red
    exit 1
}

# 4. Configurer la source si MATLAB
if ($Source -eq "matlab") {
    if (-not (Switch-ToMatlabSource)) {
        Write-Host "`n⚠️ Avertissement: impossible de configurer MATLAB" -ForegroundColor Yellow
    }
}

# 5. Démarrer le frontend
if (-not $NoFrontend) {
    if (-not (Start-Frontend)) {
        Write-Host "`n⚠️ Avertissement: impossible de démarrer le frontend" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 3
}

# 6. Afficher le statut
Show-SystemStatus

# 7. Afficher les instructions MATLAB si nécessaire
if ($Source -eq "matlab") {
    Show-MatlabInstructions
}

Write-Host "  Appuyez sur une touche pour fermer ce launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

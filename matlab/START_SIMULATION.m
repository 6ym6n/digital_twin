%% =========================================================================
%  DIGITAL TWIN - QUICK START SCRIPT
%  Lancez ce script pour démarrer rapidement la simulation
%  =========================================================================
%
%  PRÉREQUIS:
%  1. Lancez d'abord START_DIGITAL_TWIN.bat dans le dossier du projet
%  2. Attendez que le message "SYSTÈME PRÊT" apparaisse
%  3. Exécutez ce script dans MATLAB
%
%  =========================================================================

%% Configuration
scenario = 'demo';      % Options: 'normal', 'demo', 'winding', 'cavitation', 'bearing', 'overload'
duration = 300;         % Durée en secondes (300 = 5 minutes)

%% Afficher les instructions
fprintf('\n');
fprintf('═══════════════════════════════════════════════════════════════\n');
fprintf('  🏭  DIGITAL TWIN - QUICK START\n');
fprintf('═══════════════════════════════════════════════════════════════\n');
fprintf('\n');
fprintf('  📋 Scénario: %s\n', scenario);
fprintf('  ⏱️  Durée: %d secondes (%.1f minutes)\n', duration, duration/60);
fprintf('\n');
fprintf('═══════════════════════════════════════════════════════════════\n');
fprintf('\n');

%% S'assurer qu'on est dans le bon dossier
scriptPath = fileparts(mfilename('fullpath'));
if ~isempty(scriptPath)
    cd(scriptPath);
end

%% Vérifier que les fichiers existent
if ~exist('run_simulation.m', 'file')
    error('Fichier run_simulation.m non trouvé. Vérifiez que vous êtes dans le dossier matlab/');
end

%% Lancer la simulation
fprintf('🚀 Lancement de la simulation...\n\n');
run_simulation('scenario', scenario, 'duration', duration);

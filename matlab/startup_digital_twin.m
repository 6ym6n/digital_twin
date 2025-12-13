%% =========================================================================
%  QUICK START SCRIPT FOR DIGITAL TWIN
%  Run this script to start the MATLAB simulation
%  =========================================================================

% Clear workspace and command window
clear; clc;

fprintf('\n');
fprintf('╔════════════════════════════════════════════════════════════════╗\n');
fprintf('║      GRUNDFOS CR 15 DIGITAL TWIN - MATLAB QUICK START         ║\n');
fprintf('╚════════════════════════════════════════════════════════════════╝\n\n');

%% Check prerequisites
fprintf('📋 Checking prerequisites...\n');

% Check MATLAB version
v = version('-release');
year = str2double(v(1:4));
if year < 2020
    warning('MATLAB R2020a or later recommended for full features.');
end
fprintf('   MATLAB Version: %s ✓\n', version);

% Check for required files
required_files = {
    'GrundfosCR15_Parameters.m'
    'GrundfosCR15_Model.m'
    'TCPCommunication.m'
    'run_simulation.m'
};

all_present = true;
for i = 1:length(required_files)
    if exist(required_files{i}, 'file')
        fprintf('   %s ✓\n', required_files{i});
    else
        fprintf('   %s ✗ MISSING!\n', required_files{i});
        all_present = false;
    end
end

if ~all_present
    error('Missing required files. Please ensure all MATLAB files are in the path.');
end

fprintf('\n✅ All prerequisites met!\n\n');

%% Display instructions
fprintf('═══════════════════════════════════════════════════════════════════\n');
fprintf('📖 INSTRUCTIONS:\n');
fprintf('═══════════════════════════════════════════════════════════════════\n\n');

fprintf('1️⃣  First, start the Python backend:\n');
fprintf('    > cd path/to/digital_twin\n');
fprintf('    > python backend/api.py\n\n');

fprintf('2️⃣  Or start the Python TCP bridge directly:\n');
fprintf('    > python -m src.matlab_bridge --server\n\n');

fprintf('3️⃣  Then run the simulation (this script or manually):\n');
fprintf('    >> run_simulation()\n\n');

fprintf('═══════════════════════════════════════════════════════════════════\n');
fprintf('⚙️  AVAILABLE SCENARIOS:\n');
fprintf('═══════════════════════════════════════════════════════════════════\n\n');

fprintf('   Normal operation:     run_simulation(''scenario'', ''normal'')\n');
fprintf('   Demo with faults:     run_simulation(''scenario'', ''demo'')\n');
fprintf('   Winding defect:       run_simulation(''scenario'', ''winding'')\n');
fprintf('   Cavitation:           run_simulation(''scenario'', ''cavitation'')\n');
fprintf('   Bearing wear:         run_simulation(''scenario'', ''bearing'')\n');
fprintf('   Overload:             run_simulation(''scenario'', ''overload'')\n');
fprintf('   Supply fault:         run_simulation(''scenario'', ''supply'')\n');
fprintf('   Stress test:          run_simulation(''scenario'', ''stress'')\n\n');

fprintf('═══════════════════════════════════════════════════════════════════\n');
fprintf('🔧 CONFIGURATION OPTIONS:\n');
fprintf('═══════════════════════════════════════════════════════════════════\n\n');

fprintf('   Custom port:          run_simulation(''port'', 5556)\n');
fprintf('   Custom host:          run_simulation(''host'', ''192.168.1.100'')\n');
fprintf('   Run for 5 minutes:    run_simulation(''duration'', 300)\n');
fprintf('   Faster updates:       run_simulation(''sendrate'', 10)\n\n');

fprintf('═══════════════════════════════════════════════════════════════════\n\n');

%% Ask user what to do
fprintf('🎯 What would you like to do?\n\n');
fprintf('   [1] Start simulation (normal)\n');
fprintf('   [2] Start demo scenario (with faults)\n');
fprintf('   [3] View pump parameters\n');
fprintf('   [4] Test TCP connection\n');
fprintf('   [5] Exit\n\n');

choice = input('Enter choice (1-5): ');

switch choice
    case 1
        fprintf('\n▶️  Starting normal simulation...\n');
        run_simulation();
        
    case 2
        fprintf('\n▶️  Starting demo scenario...\n');
        run_simulation('scenario', 'demo', 'duration', 300);
        
    case 3
        fprintf('\n📊 Grundfos CR 15 Parameters:\n');
        fprintf('─────────────────────────────────────────────────────────────────\n');
        params = GrundfosCR15_Parameters;
        fprintf('   Model: %s\n', params.MODEL);
        fprintf('   Motor Power: %.1f kW\n', params.MOTOR_POWER);
        fprintf('   Motor Voltage: %d V\n', params.MOTOR_VOLTAGE);
        fprintf('   Motor Current: %.1f A\n', params.MOTOR_CURRENT);
        fprintf('   Nominal Speed: %d RPM\n', params.NOMINAL_SPEED);
        fprintf('   Nominal Flow: %.1f m³/h\n', params.NOMINAL_FLOW_RATE);
        fprintf('   Nominal Pressure: %.1f bar\n', params.NOMINAL_DISCHARGE_PRESSURE);
        fprintf('─────────────────────────────────────────────────────────────────\n');
        
    case 4
        fprintf('\n🔌 Testing TCP connection to Python...\n');
        tcp = TCPSender('localhost', 5555);
        if tcp.connect()
            fprintf('✅ Connection successful!\n');
            tcp.disconnect();
        else
            fprintf('❌ Connection failed. Is Python server running?\n');
        end
        
    case 5
        fprintf('\n👋 Goodbye!\n\n');
        
    otherwise
        fprintf('\n⚠️  Invalid choice.\n\n');
end

%% =========================================================================
%  DIGITAL TWIN MAIN SIMULATION SCRIPT
%  Real-time Grundfos CR 15 Pump Simulation with TCP Streaming
%  =========================================================================
%
%  This is the main entry point for running the MATLAB simulation.
%  It creates the pump model, runs the simulation loop, and streams
%  sensor data to Python via TCP.
%
%  Usage:
%    1. Start Python TCP receiver first: python -m src.matlab_bridge
%    2. Run this script in MATLAB: run_simulation
%
%  Controls:
%    - Press Ctrl+C to stop simulation
%    - Use injectFault() to simulate failures
%
%  Author: Digital Twin Project
%  Date: December 2025
%  =========================================================================

function run_simulation(varargin)
    %RUN_SIMULATION Main simulation entry point
    %
    %   Optional parameters (Name-Value pairs):
    %   'host'      - Python server host (default: 'localhost')
    %   'port'      - Python server port (default: 5555)
    %   'duration'  - Simulation duration in seconds (default: inf)
    %   'timestep'  - Simulation timestep (default: 0.1)
    %   'sendrate'  - Data send rate in Hz (default: 1)
    %   'scenario'  - Fault scenario to run (default: 'normal')
    %
    %   Examples:
    %     run_simulation()                           % Default settings
    %     run_simulation('duration', 300)            % Run for 5 minutes
    %     run_simulation('scenario', 'demo')         % Run demo with faults
    %     run_simulation('port', 5556)               % Custom port
    
    %% Parse input arguments
    p = inputParser;
    addParameter(p, 'host', 'localhost', @ischar);
    addParameter(p, 'port', 5555, @isnumeric);
    addParameter(p, 'duration', 900, @isnumeric);  % 15 minutes = 900 seconds (use inf for unlimited)
    addParameter(p, 'timestep', 0.1, @isnumeric);
    addParameter(p, 'sendrate', 1, @isnumeric);
    addParameter(p, 'scenario', 'normal', @ischar);
    parse(p, varargin{:});
    
    config = p.Results;
    
    %% Display banner
    fprintf('\n');
    fprintf('═══════════════════════════════════════════════════════════════\n');
    fprintf('  🏭  GRUNDFOS CR 15 DIGITAL TWIN - MATLAB SIMULATION\n');
    fprintf('═══════════════════════════════════════════════════════════════\n');
    fprintf('  Host: %s:%d\n', config.host, config.port);
    fprintf('  Timestep: %.2f s | Send Rate: %.1f Hz\n', config.timestep, config.sendrate);
    fprintf('  Scenario: %s\n', config.scenario);
    fprintf('═══════════════════════════════════════════════════════════════\n\n');
    
    %% Initialize pump model
    fprintf('📦 Initializing pump model...\n');
    pump = GrundfosCR15_Model();
    
    %% Initialize TCP communication
    fprintf('\n📡 Setting up TCP connection...\n');
    tcp = TCPSender(config.host, config.port);
    
    % Attempt connection with retries (more attempts, longer wait)
    max_retries = 10;
    retry_delay = 3;
    
    fprintf('   💡 Tip: Assurez-vous que Python backend est lancé\n');
    fprintf('      Utilisez START_DIGITAL_TWIN.bat pour tout lancer\n\n');
    
    for attempt = 1:max_retries
        fprintf('   Connection attempt %d/%d...\n', attempt, max_retries);
        
        if tcp.connect()
            break;
        end
        
        if attempt < max_retries
            fprintf('   ⏳ Retrying in %d seconds...\n', retry_delay);
            pause(retry_delay);
        else
            fprintf('\n❌ Failed to connect after %d attempts.\n', max_retries);
            fprintf('   \n');
            fprintf('   🔧 SOLUTION:\n');
            fprintf('   1. Lancez START_DIGITAL_TWIN.bat dans le dossier du projet\n');
            fprintf('   2. Attendez que le système soit prêt\n');
            fprintf('   3. Relancez cette simulation\n\n');
            return;
        end
    end
    
    %% Initialize fault injection handler for Python commands
    fprintf('\n🎮 Setting up fault injection handler...\n');
    fault_handler = FaultInjectionHandler(tcp);
    
    %% Set up fault scenario
    scenario_faults = setupScenario(config.scenario);
    next_fault_idx = 1;
    
    %% Calculate timing
    send_interval = 1.0 / config.sendrate;
    last_send_time = 0;
    
    %% Main simulation loop
    fprintf('\n▶️  Starting simulation loop...\n');
    fprintf('   Press Ctrl+C to stop\n\n');
    
    cleanup = onCleanup(@() cleanupSimulation(tcp, pump));
    
    try
        while pump.simulation_time < config.duration
            % Step the physics model
            pump.step(config.timestep);
            
            % === CHECK FOR PYTHON COMMANDS ===
            % This allows Python to inject faults via the UI
            fault_handler.checkForCommands(pump);
            
            % Check for scheduled faults (from MATLAB scenario)
            if next_fault_idx <= length(scenario_faults)
                fault_event = scenario_faults{next_fault_idx};
                if pump.simulation_time >= fault_event.time
                    if strcmp(fault_event.type, 'clear')
                        pump.clearFault();
                        fault_handler.handleResetFault(pump);
                    else
                        pump.injectFault(fault_event.type);
                        % Also update fault handler for consistency
                        fault_handler.current_fault = fault_event.type;
                        fault_handler.applyDefaultFaultEffects(fault_event.type, 1.0);
                    end
                    next_fault_idx = next_fault_idx + 1;
                end
            end
            
            % Send data at specified rate
            if pump.simulation_time - last_send_time >= send_interval
                % Get sensor data
                data = pump.getSensorData();
                
                % === APPLY FAULT EFFECTS FROM PYTHON ===
                % This modifies sensor data based on injected faults
                data = fault_handler.applySensorEffects(data);
                
                % Send via TCP
                if tcp.isConnected()
                    tcp.send(data);
                    
                    % Display status periodically
                    if mod(tcp.packets_sent, 10) == 0
                        printStatus(pump, data, fault_handler.current_fault);
                    end
                else
                    fprintf('⚠️  Connection lost. Attempting reconnect...\n');
                    if ~tcp.connect()
                        fprintf('❌ Reconnection failed. Stopping simulation.\n');
                        break;
                    end
                end
                
                last_send_time = pump.simulation_time;
            end
            
            % Small pause to prevent CPU overload
            pause(config.timestep * 0.9);
        end
        
    catch ME
        if strcmp(ME.identifier, 'MATLAB:class:InvalidHandle')
            fprintf('\n\n⏹️  Simulation stopped by user.\n');
        else
            rethrow(ME);
        end
    end
    
    fprintf('\n✅ Simulation complete!\n');
    fprintf('   Total time: %.1f seconds\n', pump.simulation_time);
    fprintf('   Packets sent: %d\n', tcp.packets_sent);
end


%% =========================================================================
%  HELPER FUNCTIONS
%  =========================================================================

function scenario = setupScenario(name)
    %SETUPSCENARIO Create fault injection schedule for scenarios
    
    scenario = {};
    
    switch lower(name)
        case 'normal'
            % No faults
            scenario = {};
            
        case 'demo'
            % Demonstration with multiple faults (5 minutes / 300 seconds)
            scenario = {
                struct('time', 30,  'type', 'Winding Defect')
                struct('time', 70,  'type', 'clear')
                struct('time', 100, 'type', 'Cavitation')
                struct('time', 150, 'type', 'clear')
                struct('time', 180, 'type', 'Bearing Wear')
                struct('time', 230, 'type', 'clear')
                struct('time', 260, 'type', 'Overload')
                struct('time', 290, 'type', 'clear')
            };
            
        case 'winding'
            scenario = {
                struct('time', 10, 'type', 'Winding Defect')
            };
            
        case 'cavitation'
            scenario = {
                struct('time', 10, 'type', 'Cavitation')
            };
            
        case 'bearing'
            scenario = {
                struct('time', 10, 'type', 'Bearing Wear')
            };
            
        case 'overload'
            scenario = {
                struct('time', 10, 'type', 'Overload')
            };
            
        case 'supply'
            scenario = {
                struct('time', 10, 'type', 'Supply Fault')
            };
            
        case 'stress'
            % Stress test with rapid fault changes
            scenario = {
                struct('time', 10,  'type', 'Winding Defect')
                struct('time', 20,  'type', 'Cavitation')
                struct('time', 30,  'type', 'Bearing Wear')
                struct('time', 40,  'type', 'Overload')
                struct('time', 50,  'type', 'Supply Fault')
                struct('time', 60,  'type', 'clear')
            };
            
        otherwise
            fprintf('⚠️  Unknown scenario: %s. Using normal.\n', name);
    end
    
    if ~isempty(scenario)
        fprintf('📋 Scenario "%s" loaded with %d events:\n', name, length(scenario));
        for i = 1:length(scenario)
            event = scenario{i};
            fprintf('   [%3.0fs] %s\n', event.time, event.type);
        end
        fprintf('\n');
    end
end


function printStatus(pump, data, current_fault)
    %PRINTSTATUS Display current pump status
    
    if nargin < 3
        current_fault = data.fault_state;
    end
    
    % Color code based on fault
    if strcmp(current_fault, 'Normal')
        status_icon = '✅';
    elseif contains(current_fault, 'Overload') || contains(current_fault, 'Seizure')
        status_icon = '🔴';
    else
        status_icon = '⚠️';
    end
    
    fprintf('─────────────────────────────────────────────────────────\n');
    fprintf('⏱️  Time: %.1fs | %s Status: %s\n', ...
        pump.simulation_time, status_icon, current_fault);
    fprintf('   ⚡ Current: A=%.2fA B=%.2fA C=%.2fA (Imb: %.1f%%)\n', ...
        data.amperage.phase_a, data.amperage.phase_b, ...
        data.amperage.phase_c, data.amperage.imbalance_pct);
    fprintf('   🔌 Voltage: %.1fV | 🌡️ Temp: %.1f°C\n', ...
        data.voltage, data.temperature);
    fprintf('   📊 Vibration: %.2f mm/s | 💧 Pressure: %.2f bar\n', ...
        data.vibration, data.pressure);
    fprintf('   🔄 Flow: %.2f m³/h | ⚙️ RPM: %d\n', ...
        data.flow_rate, data.rpm);
end


function cleanupSimulation(tcp, pump)
    %CLEANUPSIMULATION Clean up resources on exit
    
    fprintf('\n🧹 Cleaning up...\n');
    
    if ~isempty(tcp) && isvalid(tcp)
        tcp.disconnect();
    end
    
    if ~isempty(pump) && isvalid(pump)
        pump.stop();
    end
    
    fprintf('👋 Goodbye!\n\n');
end

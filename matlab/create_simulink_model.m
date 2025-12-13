%% =========================================================================
%  SIMULINK MODEL BUILDER FOR GRUNDFOS CR 15
%  Creates Simscape Fluids model programmatically
%  =========================================================================
%
%  This script creates a Simulink/Simscape model for the Grundfos CR 15 pump.
%  It uses Simscape Fluids library for realistic hydraulic simulation.
%
%  Requirements:
%  - MATLAB R2020a or later
%  - Simulink
%  - Simscape
%  - Simscape Fluids
%
%  The model includes:
%  - Centrifugal pump block with CR 15 parameters
%  - Pressure sensors (inlet/outlet)
%  - Flow sensor
%  - Motor model
%  - Temperature estimation
%
%  Author: Digital Twin Project
%  Date: December 2025
%  =========================================================================

function create_simulink_model(model_name)
    %CREATE_SIMULINK_MODEL Build Simscape Fluids model for CR 15 pump
    %   model_name: Name for the Simulink model (default: 'GrundfosCR15_Simulink')
    
    if nargin < 1
        model_name = 'GrundfosCR15_Simulink';
    end
    
    fprintf('\n');
    fprintf('═══════════════════════════════════════════════════════════════\n');
    fprintf('  🔧 CREATING SIMULINK MODEL: %s\n', model_name);
    fprintf('═══════════════════════════════════════════════════════════════\n\n');
    
    %% Check for required toolboxes
    fprintf('📋 Checking required toolboxes...\n');
    
    required = {'Simulink', 'Simscape', 'Simscape Fluids'};
    missing = {};
    
    v = ver;
    installed = {v.Name};
    
    for i = 1:length(required)
        if ~any(contains(installed, required{i}))
            missing{end+1} = required{i}; %#ok<AGROW>
        end
    end
    
    if ~isempty(missing)
        fprintf('❌ Missing required toolboxes:\n');
        for i = 1:length(missing)
            fprintf('   - %s\n', missing{i});
        end
        fprintf('\n⚠️  Cannot create Simulink model without these toolboxes.\n');
        fprintf('   The MATLAB-only model (GrundfosCR15_Model.m) will be used instead.\n');
        return;
    end
    
    fprintf('   ✅ All required toolboxes found!\n\n');
    
    %% Create new model
    fprintf('📦 Creating new Simulink model...\n');
    
    % Close if already open
    if bdIsLoaded(model_name)
        close_system(model_name, 0);
    end
    
    % Create new model
    new_system(model_name);
    open_system(model_name);
    
    %% Add Solver Configuration
    fprintf('   Adding solver configuration...\n');
    add_block('nesl_utility/Solver Configuration', ...
        [model_name '/Solver Configuration'], ...
        'Position', [50, 50, 100, 100]);
    
    %% Add Hydraulic Fluid
    fprintf('   Adding hydraulic fluid (water)...\n');
    add_block('fl_lib/Hydraulic (Isothermal)/Hydraulic Fluid', ...
        [model_name '/Water'], ...
        'Position', [50, 150, 100, 200]);
    
    %% Add Centrifugal Pump
    fprintf('   Adding centrifugal pump...\n');
    
    % Check if Simscape Fluids has the pump block
    try
        add_block('fl_lib/Hydraulic (Isothermal)/Pumps & Motors/Centrifugal Pump', ...
            [model_name '/CR15_Pump'], ...
            'Position', [300, 150, 400, 250]);
        
        % Set pump parameters based on CR 15 specs
        params = GrundfosCR15_Parameters;
        
        set_param([model_name '/CR15_Pump'], ...
            'q_nom', sprintf('%g[m^3/h]', params.NOMINAL_FLOW_RATE), ...
            'p_nom', sprintf('%g[bar]', params.NOMINAL_DISCHARGE_PRESSURE), ...
            'omega_nom', sprintf('%g[rpm]', params.NOMINAL_SPEED));
            
    catch ME
        fprintf('   ⚠️  Centrifugal Pump block not available: %s\n', ME.message);
        fprintf('   Using generic pump representation...\n');
        
        % Alternative: Use hydraulic source
        add_block('fl_lib/Hydraulic (Isothermal)/Sources/Hydraulic Flow Rate Source', ...
            [model_name '/Flow_Source'], ...
            'Position', [300, 150, 400, 250]);
    end
    
    %% Add Pressure Sensors
    fprintf('   Adding pressure sensors...\n');
    
    % Inlet pressure sensor
    add_block('fl_lib/Hydraulic (Isothermal)/Sensors/Pressure Sensor', ...
        [model_name '/P_Inlet'], ...
        'Position', [200, 100, 250, 130]);
    
    % Outlet pressure sensor
    add_block('fl_lib/Hydraulic (Isothermal)/Sensors/Pressure Sensor', ...
        [model_name '/P_Outlet'], ...
        'Position', [500, 100, 550, 130]);
    
    %% Add Flow Sensor
    fprintf('   Adding flow sensor...\n');
    add_block('fl_lib/Hydraulic (Isothermal)/Sensors/Flow Rate Sensor', ...
        [model_name '/Flow_Sensor'], ...
        'Position', [500, 200, 550, 230]);
    
    %% Add Motor Block
    fprintf('   Adding motor model...\n');
    
    % Mechanical rotational source for motor
    add_block('fl_lib/Mechanical/Rotational Elements/Ideal Angular Velocity Source', ...
        [model_name '/Motor'], ...
        'Position', [150, 200, 200, 250]);
    
    %% Add RPM Input
    fprintf('   Adding RPM control...\n');
    add_block('simulink/Sources/Constant', ...
        [model_name '/RPM_Setpoint'], ...
        'Position', [50, 220, 80, 240], ...
        'Value', '2900');
    
    % RPM to rad/s conversion
    add_block('simulink/Math Operations/Gain', ...
        [model_name '/RPM_to_RadS'], ...
        'Position', [100, 215, 130, 245], ...
        'Gain', 'pi/30');
    
    %% Add Simulink-PS and PS-Simulink Converters
    fprintf('   Adding signal converters...\n');
    
    add_block('nesl_utility/Simulink-PS Converter', ...
        [model_name '/S-PS'], ...
        'Position', [140, 215, 160, 245]);
    
    % Output converters
    add_block('nesl_utility/PS-Simulink Converter', ...
        [model_name '/PS-S_P_In'], ...
        'Position', [270, 100, 290, 120]);
    
    add_block('nesl_utility/PS-Simulink Converter', ...
        [model_name '/PS-S_P_Out'], ...
        'Position', [570, 100, 590, 120]);
    
    add_block('nesl_utility/PS-Simulink Converter', ...
        [model_name '/PS-S_Flow'], ...
        'Position', [570, 200, 590, 220]);
    
    %% Add Output Scopes/Displays
    fprintf('   Adding output displays...\n');
    
    add_block('simulink/Sinks/Display', ...
        [model_name '/Display_P_In'], ...
        'Position', [620, 95, 680, 125]);
    
    add_block('simulink/Sinks/Display', ...
        [model_name '/Display_P_Out'], ...
        'Position', [620, 145, 680, 175]);
    
    add_block('simulink/Sinks/Display', ...
        [model_name '/Display_Flow'], ...
        'Position', [620, 195, 680, 225]);
    
    %% Add To Workspace blocks for TCP output
    fprintf('   Adding data logging...\n');
    
    add_block('simulink/Sinks/To Workspace', ...
        [model_name '/Log_P_In'], ...
        'Position', [650, 60, 710, 80], ...
        'VariableName', 'P_inlet', ...
        'SaveFormat', 'Timeseries');
    
    add_block('simulink/Sinks/To Workspace', ...
        [model_name '/Log_P_Out'], ...
        'Position', [650, 130, 710, 150], ...
        'VariableName', 'P_outlet', ...
        'SaveFormat', 'Timeseries');
    
    add_block('simulink/Sinks/To Workspace', ...
        [model_name '/Log_Flow'], ...
        'Position', [650, 230, 710, 250], ...
        'VariableName', 'Flow_rate', ...
        'SaveFormat', 'Timeseries');
    
    %% Connect blocks (basic connections)
    fprintf('   Connecting blocks...\n');
    
    % Connect RPM chain
    add_line(model_name, 'RPM_Setpoint/1', 'RPM_to_RadS/1');
    add_line(model_name, 'RPM_to_RadS/1', 'S-PS/1');
    
    % Connect sensor outputs to displays
    add_line(model_name, 'PS-S_P_In/1', 'Display_P_In/1');
    add_line(model_name, 'PS-S_P_Out/1', 'Display_P_Out/1');
    add_line(model_name, 'PS-S_Flow/1', 'Display_Flow/1');
    
    % Connect to logging
    add_line(model_name, 'PS-S_P_In/1', 'Log_P_In/1');
    add_line(model_name, 'PS-S_P_Out/1', 'Log_P_Out/1');
    add_line(model_name, 'PS-S_Flow/1', 'Log_Flow/1');
    
    %% Configure simulation parameters
    fprintf('   Configuring simulation parameters...\n');
    
    set_param(model_name, ...
        'Solver', 'ode23t', ...
        'StopTime', '100', ...
        'MaxStep', '0.1', ...
        'RelTol', '1e-3');
    
    %% Save model
    fprintf('\n💾 Saving model...\n');
    save_system(model_name);
    
    fprintf('\n✅ Simulink model created successfully!\n');
    fprintf('   Model: %s.slx\n', model_name);
    fprintf('   Location: %s\n', pwd);
    fprintf('\n📝 Notes:\n');
    fprintf('   - You may need to manually connect Simscape physical network\n');
    fprintf('   - Adjust pump parameters in block dialog for exact CR 15 specs\n');
    fprintf('   - Add thermal and electrical subsystems as needed\n\n');
end


%% =========================================================================
%  ALTERNATIVE: Create model specification file for manual building
%  =========================================================================

function create_model_specification()
    %CREATE_MODEL_SPECIFICATION Generate specification for manual Simulink model
    
    fprintf('\n');
    fprintf('═══════════════════════════════════════════════════════════════\n');
    fprintf('  📋 SIMULINK MODEL SPECIFICATION - GRUNDFOS CR 15\n');
    fprintf('═══════════════════════════════════════════════════════════════\n\n');
    
    params = GrundfosCR15_Parameters;
    
    fprintf('PUMP PARAMETERS (for Simscape Centrifugal Pump block):\n');
    fprintf('─────────────────────────────────────────────────────────────────\n');
    fprintf('  Nominal flow rate:       %g m³/h\n', params.NOMINAL_FLOW_RATE);
    fprintf('  Nominal pressure rise:   %g bar\n', params.NOMINAL_DISCHARGE_PRESSURE);
    fprintf('  Nominal shaft speed:     %d RPM\n', params.NOMINAL_SPEED);
    fprintf('  Fluid density:           %g kg/m³\n', params.FLUID_DENSITY);
    fprintf('\n');
    
    fprintf('MOTOR PARAMETERS (for electrical subsystem):\n');
    fprintf('─────────────────────────────────────────────────────────────────\n');
    fprintf('  Rated power:             %.1f kW\n', params.MOTOR_POWER);
    fprintf('  Rated voltage:           %d V (3-phase)\n', params.MOTOR_VOLTAGE);
    fprintf('  Rated current:           %.1f A\n', params.MOTOR_CURRENT);
    fprintf('  Power factor:            %.2f\n', params.POWER_FACTOR);
    fprintf('  Motor efficiency:        %.0f%%\n', params.MOTOR_EFFICIENCY * 100);
    fprintf('  Rotor inertia:           %.4f kg.m²\n', params.ROTOR_INERTIA);
    fprintf('\n');
    
    fprintf('SENSOR BLOCKS REQUIRED:\n');
    fprintf('─────────────────────────────────────────────────────────────────\n');
    fprintf('  1. Pressure Sensor (inlet)  - Simscape Fluids\n');
    fprintf('  2. Pressure Sensor (outlet) - Simscape Fluids\n');
    fprintf('  3. Flow Rate Sensor         - Simscape Fluids\n');
    fprintf('  4. Speed Sensor             - Simscape Mechanical\n');
    fprintf('  5. Current Sensor (x3)      - Simscape Electrical (optional)\n');
    fprintf('  6. Temperature Sensor       - Custom/Simscape Thermal\n');
    fprintf('\n');
    
    fprintf('RECOMMENDED SOLVER SETTINGS:\n');
    fprintf('─────────────────────────────────────────────────────────────────\n');
    fprintf('  Solver:                  ode23t (stiff)\n');
    fprintf('  Max step size:           0.1 s\n');
    fprintf('  Relative tolerance:      1e-3\n');
    fprintf('  Fixed-step for RT:       0.01 s\n');
    fprintf('\n');
    
    fprintf('TCP OUTPUT BLOCK:\n');
    fprintf('─────────────────────────────────────────────────────────────────\n');
    fprintf('  Use "To Workspace" blocks to log data\n');
    fprintf('  Then use run_simulation.m for TCP streaming\n');
    fprintf('  Alternative: Use MATLAB Function block with tcpclient\n');
    fprintf('\n');
end

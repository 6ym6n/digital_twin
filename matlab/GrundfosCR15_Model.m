%% =========================================================================
%  GRUNDFOS CR 15 PUMP PHYSICAL MODEL
%  Main simulation class for Digital Twin
%  =========================================================================
%
%  This class implements a physics-based model of the Grundfos CR 15 pump
%  using fundamental fluid dynamics and electrical equations.
%
%  Features:
%  - Realistic pump curve (H-Q characteristic)
%  - Motor electrical model (3-phase induction)
%  - Thermal model for motor temperature
%  - Vibration model based on mechanical condition
%  - Fault injection capabilities
%
%  Author: Digital Twin Project
%  Date: December 2025
%  =========================================================================

classdef GrundfosCR15_Model < handle
    %GRUNDFOSCR15_MODEL Physical simulation model for Grundfos CR 15 pump
    
    properties
        % Operating conditions
        rpm                 % Current rotational speed (RPM)
        flow_rate           % Current flow rate (m³/h)
        discharge_pressure  % Outlet pressure (bar)
        inlet_pressure      % Inlet pressure (bar)
        temperature         % Motor winding temperature (°C)
        vibration           % Vibration level (mm/s RMS)
        
        % Electrical
        voltage             % Supply voltage (V)
        current_a           % Phase A current (A)
        current_b           % Phase B current (A)
        current_c           % Phase C current (A)
        power               % Electrical power (kW)
        torque              % Shaft torque (Nm)
        
        % State variables
        fault_state         % Current fault condition
        fault_duration      % Duration of current fault (s)
        simulation_time     % Total simulation time (s)
        running             % Pump running status
        
        % Thermal state
        thermal_energy      % Accumulated thermal energy
        
        % Parameters reference
        params              % GrundfosCR15_Parameters reference
    end
    
    properties (Constant)
        % Fault types enumeration
        FAULT_NORMAL = 'Normal';
        FAULT_WINDING_DEFECT = 'Winding Defect';
        FAULT_SUPPLY_FAULT = 'Supply Fault';
        FAULT_CAVITATION = 'Cavitation';
        FAULT_BEARING_WEAR = 'Bearing Wear';
        FAULT_OVERLOAD = 'Overload';
    end
    
    methods
        function obj = GrundfosCR15_Model()
            %GRUNDFOSCR15_MODEL Constructor - Initialize pump model
            
            obj.params = GrundfosCR15_Parameters;
            obj.reset();
            
            fprintf('🏭 Grundfos CR 15 Physical Model Initialized\n');
            fprintf('   Motor Power: %.1f kW\n', obj.params.MOTOR_POWER);
            fprintf('   Nominal Speed: %d RPM\n', obj.params.NOMINAL_SPEED);
            fprintf('   Nominal Flow: %.1f m³/h\n', obj.params.NOMINAL_FLOW_RATE);
        end
        
        function reset(obj)
            %RESET Reset model to initial conditions
            
            % Operating point - nominal conditions
            obj.rpm = obj.params.NOMINAL_SPEED;
            obj.flow_rate = obj.params.NOMINAL_FLOW_RATE;
            obj.inlet_pressure = 1.0;  % 1 bar inlet
            obj.voltage = obj.params.MOTOR_VOLTAGE;
            obj.temperature = obj.params.AMBIENT_TEMPERATURE;
            obj.vibration = obj.params.VIBRATION_GOOD * 0.8;
            
            % Calculate initial discharge pressure
            H = obj.params.calculateHead(obj.flow_rate, obj.rpm);
            obj.discharge_pressure = obj.params.calculatePressure(H);
            
            % Calculate initial electrical values
            eta = obj.params.calculateEfficiency(obj.flow_rate);
            P_shaft = obj.params.calculateShaftPower(obj.flow_rate, H, eta);
            I_nom = obj.params.calculateCurrent(P_shaft, obj.voltage, ...
                obj.params.POWER_FACTOR, obj.params.MOTOR_EFFICIENCY);
            
            obj.current_a = I_nom;
            obj.current_b = I_nom;
            obj.current_c = I_nom;
            obj.power = P_shaft / obj.params.MOTOR_EFFICIENCY;
            obj.torque = P_shaft * 1000 / (obj.rpm * 2 * pi / 60);
            
            % State
            obj.fault_state = obj.FAULT_NORMAL;
            obj.fault_duration = 0;
            obj.simulation_time = 0;
            obj.running = true;
            obj.thermal_energy = 0;
            
            fprintf('✅ Model reset to nominal conditions\n');
        end
        
        function injectFault(obj, fault_type)
            %INJECTFAULT Inject a fault condition
            %   fault_type: One of the FAULT_* constants
            
            obj.fault_state = fault_type;
            obj.fault_duration = 0;
            
            fprintf('\n⚠️  FAULT INJECTED: %s\n', fault_type);
        end
        
        function clearFault(obj)
            %CLEARFAULT Return to normal operation
            
            obj.fault_state = obj.FAULT_NORMAL;
            obj.fault_duration = 0;
            fprintf('\n✅ Fault cleared - Normal operation\n');
        end
        
        function step(obj, dt)
            %STEP Advance simulation by one timestep
            %   dt: Time step in seconds
            
            if ~obj.running
                return;
            end
            
            obj.simulation_time = obj.simulation_time + dt;
            
            % Update fault duration
            if ~strcmp(obj.fault_state, obj.FAULT_NORMAL)
                obj.fault_duration = obj.fault_duration + dt;
            end
            
            % Update physics based on current state and faults
            obj.updateHydraulics(dt);
            obj.updateElectrical(dt);
            obj.updateThermal(dt);
            obj.updateVibration(dt);
            
            % Add sensor noise
            obj.addSensorNoise();
        end
        
        function updateHydraulics(obj, dt)
            %UPDATEHYDRAULICS Update hydraulic state
            
            % Base flow rate with small variations
            Q_base = obj.params.NOMINAL_FLOW_RATE;
            
            switch obj.fault_state
                case obj.FAULT_CAVITATION
                    % Cavitation: fluctuating flow, reduced efficiency
                    Q_fluct = 0.3 * sin(obj.simulation_time * 10) + ...
                              0.1 * sin(obj.simulation_time * 25);
                    obj.flow_rate = Q_base * (0.85 + Q_fluct * 0.15);
                    
                    % Pressure fluctuations
                    P_fluct = 0.2 * sin(obj.simulation_time * 15);
                    obj.inlet_pressure = 0.3 + P_fluct * 0.2;  % Low NPSH
                    
                case obj.FAULT_OVERLOAD
                    % Overload: high flow demand
                    obj.flow_rate = Q_base * 1.3;
                    
                otherwise
                    % Normal operation with small variations
                    obj.flow_rate = Q_base * (1 + 0.02 * randn());
            end
            
            % Calculate head and pressure
            H = obj.params.calculateHead(obj.flow_rate, obj.rpm);
            obj.discharge_pressure = obj.params.calculatePressure(H) + obj.inlet_pressure;
            
            % Apply cavitation pressure drop
            if strcmp(obj.fault_state, obj.FAULT_CAVITATION)
                obj.discharge_pressure = obj.discharge_pressure * 0.7;
            end
        end
        
        function updateElectrical(obj, dt)
            %UPDATEELECTRICAL Update electrical parameters
            
            % Base current calculation
            H = obj.params.calculateHead(obj.flow_rate, obj.rpm);
            eta = obj.params.calculateEfficiency(obj.flow_rate);
            P_shaft = obj.params.calculateShaftPower(obj.flow_rate, H, eta);
            
            I_base = obj.params.calculateCurrent(P_shaft, obj.voltage, ...
                obj.params.POWER_FACTOR, obj.params.MOTOR_EFFICIENCY);
            
            switch obj.fault_state
                case obj.FAULT_WINDING_DEFECT
                    % Phase imbalance - one phase deviates
                    imbalance = 0.05 + obj.fault_duration * 0.005;  % Progressive
                    imbalance = min(imbalance, 0.25);
                    
                    % Random phase affected
                    phase = mod(floor(obj.simulation_time), 3);
                    direction = sign(randn());
                    
                    obj.current_a = I_base * (1 + 0.02 * randn());
                    obj.current_b = I_base * (1 + 0.02 * randn());
                    obj.current_c = I_base * (1 + 0.02 * randn());
                    
                    if phase == 0
                        obj.current_a = I_base * (1 + direction * imbalance);
                    elseif phase == 1
                        obj.current_b = I_base * (1 + direction * imbalance);
                    else
                        obj.current_c = I_base * (1 + direction * imbalance);
                    end
                    
                case obj.FAULT_SUPPLY_FAULT
                    % Low voltage supply
                    obj.voltage = obj.params.MOTOR_VOLTAGE * (0.85 + 0.05 * randn());
                    
                    % Current increases to compensate (up to thermal limit)
                    I_comp = I_base * (obj.params.MOTOR_VOLTAGE / obj.voltage);
                    obj.current_a = I_comp * (1 + 0.02 * randn());
                    obj.current_b = I_comp * (1 + 0.02 * randn());
                    obj.current_c = I_comp * (1 + 0.02 * randn());
                    
                case obj.FAULT_OVERLOAD
                    % High current due to overload
                    overload_factor = 1.25;
                    obj.current_a = I_base * overload_factor * (1 + 0.02 * randn());
                    obj.current_b = I_base * overload_factor * (1 + 0.02 * randn());
                    obj.current_c = I_base * overload_factor * (1 + 0.02 * randn());
                    
                otherwise
                    % Normal balanced operation
                    obj.voltage = obj.params.MOTOR_VOLTAGE * (1 + 0.01 * randn());
                    obj.current_a = I_base * (1 + 0.02 * randn());
                    obj.current_b = I_base * (1 + 0.02 * randn());
                    obj.current_c = I_base * (1 + 0.02 * randn());
            end
            
            % Calculate power and torque
            I_avg = (obj.current_a + obj.current_b + obj.current_c) / 3;
            obj.power = sqrt(3) * obj.voltage * I_avg * obj.params.POWER_FACTOR / 1000;
            obj.torque = obj.power * 1000 / (obj.rpm * 2 * pi / 60);
        end
        
        function updateThermal(obj, dt)
            %UPDATETHERMAL Update temperature model
            
            I_avg = (obj.current_a + obj.current_b + obj.current_c) / 3;
            I_nom = obj.params.MOTOR_CURRENT;
            
            % Base temperature rise from current
            T_target = obj.params.NOMINAL_OPERATING_TEMP;
            
            switch obj.fault_state
                case obj.FAULT_WINDING_DEFECT
                    % Hot spot due to uneven current distribution
                    T_target = T_target + 15 + obj.fault_duration * 0.5;
                    
                case obj.FAULT_OVERLOAD
                    % Higher temperature from excess current
                    T_target = T_target + 10 * (I_avg / I_nom - 1);
                    
                case obj.FAULT_BEARING_WEAR
                    % Friction heat
                    T_target = T_target + 5 + obj.fault_duration * 0.2;
                    
                otherwise
                    % Normal operation - target is nominal
                    T_target = obj.params.NOMINAL_OPERATING_TEMP;
            end
            
            % First-order thermal dynamics
            tau_thermal = 300;  % 5 minute time constant
            obj.temperature = obj.temperature + ...
                (T_target - obj.temperature) * dt / tau_thermal;
            
            % Add some noise
            obj.temperature = obj.temperature + 0.2 * randn();
        end
        
        function updateVibration(obj, dt)
            %UPDATEVIBRATION Update vibration model
            
            V_base = obj.params.VIBRATION_GOOD;
            
            switch obj.fault_state
                case obj.FAULT_CAVITATION
                    % High, erratic vibration
                    V_base = obj.params.VIBRATION_ALARM;
                    spike = rand() < 0.3;  % 30% chance of spike
                    if spike
                        V_base = V_base + 3 * rand();
                    end
                    
                case obj.FAULT_BEARING_WEAR
                    % Progressive increase
                    V_base = obj.params.VIBRATION_ACCEPTABLE + ...
                        obj.fault_duration * 0.05;
                    V_base = min(V_base, obj.params.VIBRATION_DANGER);
                    
                case obj.FAULT_OVERLOAD
                    % Moderately elevated
                    V_base = obj.params.VIBRATION_ACCEPTABLE * 0.9;
                    
                otherwise
                    V_base = obj.params.VIBRATION_GOOD * 0.8;
            end
            
            obj.vibration = V_base * (1 + 0.1 * randn());
            obj.vibration = max(0.5, obj.vibration);  % Minimum baseline
        end
        
        function addSensorNoise(obj)
            %ADDSENSORNOISE Add realistic sensor measurement noise
            
            % Already added in individual update methods
            % This is for additional global noise if needed
        end
        
        function data = getSensorData(obj)
            %GETSENSORDATA Get current sensor readings as struct
            %   Returns structured data compatible with Python receiver
            
            % Calculate derived values
            I_avg = (obj.current_a + obj.current_b + obj.current_c) / 3;
            max_dev = max([abs(obj.current_a - I_avg), ...
                          abs(obj.current_b - I_avg), ...
                          abs(obj.current_c - I_avg)]);
            imbalance_pct = (max_dev / I_avg) * 100;
            
            data = struct();
            data.timestamp = obj.simulation_time;
            data.datetime = datestr(now, 'yyyy-mm-ddTHH:MM:SS');
            
            % Amperage data
            data.amperage = struct();
            data.amperage.phase_a = round(obj.current_a, 2);
            data.amperage.phase_b = round(obj.current_b, 2);
            data.amperage.phase_c = round(obj.current_c, 2);
            data.amperage.average = round(I_avg, 2);
            data.amperage.imbalance_pct = round(imbalance_pct, 2);
            
            % Other sensors
            data.voltage = round(obj.voltage, 1);
            data.vibration = round(obj.vibration, 2);
            data.pressure = round(obj.discharge_pressure, 2);
            data.temperature = round(obj.temperature, 1);
            
            % Additional sensors
            data.flow_rate = round(obj.flow_rate, 2);
            data.rpm = round(obj.rpm);
            data.power = round(obj.power, 2);
            data.torque = round(obj.torque, 2);
            data.inlet_pressure = round(obj.inlet_pressure, 2);
            
            % Status
            data.fault_state = obj.fault_state;
            data.fault_duration = round(obj.fault_duration);
            data.running = obj.running;
        end
        
        function json = getSensorDataJSON(obj)
            %GETSENSORDATAJSON Get sensor data as JSON string
            
            data = obj.getSensorData();
            json = jsonencode(data);
        end
        
        function stop(obj)
            %STOP Stop the pump
            obj.running = false;
            fprintf('🛑 Pump stopped\n');
        end
        
        function start(obj)
            %START Start the pump
            obj.running = true;
            fprintf('▶️ Pump started\n');
        end
    end
end

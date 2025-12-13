%% =========================================================================
%  FAULT INJECTION HANDLER FOR DIGITAL TWIN
%  Receives and applies fault injection commands from Python
%  =========================================================================
%
%  This class handles bidirectional communication with Python for
%  fault injection. It receives JSON commands via TCP and applies
%  the corresponding fault effects to the simulation.
%
%  Usage:
%    handler = FaultInjectionHandler(tcp_sender);
%    handler.checkForCommands(pump_model);
%
%  Author: Digital Twin Project
%  Date: December 2025
%  =========================================================================

classdef FaultInjectionHandler < handle
    %FAULTINJECTIONHANDLER Handles fault injection commands from Python
    
    properties
        tcp_socket          % TCP connection object
        current_fault       % Current active fault
        fault_effects       % Current fault effect multipliers
        last_command        % Last received command
        command_count       % Number of commands processed
    end
    
    properties (Access = private)
        default_effects     % Default (normal) effects
    end
    
    methods
        function obj = FaultInjectionHandler(tcp_socket)
            %FAULTINJECTIONHANDLER Constructor
            %   tcp_socket: TCPSender object or tcpclient object
            
            obj.tcp_socket = tcp_socket;
            obj.current_fault = 'Normal';
            obj.command_count = 0;
            obj.last_command = '';
            
            % Initialize default effects (no modification)
            obj.default_effects = struct(...
                'vibration_mult', 1.0, ...
                'vibration_base', 0, ...
                'temp_offset', 0, ...
                'temp_base', 0, ...
                'current_mult', 1.0, ...
                'current_base', 0, ...
                'current_imbalance', 0, ...
                'pressure_mult', 1.0, ...
                'flow_mult', 1.0, ...
                'voltage_variance', 0, ...
                'pressure_variance', 0 ...
            );
            
            obj.fault_effects = obj.default_effects;
            
            fprintf('🎮 Fault Injection Handler initialized\n');
            fprintf('   Ready to receive commands from Python\n');
        end
        
        function checkForCommands(obj, pump_model)
            %CHECKFORCOMMANDS Check for and process incoming commands
            %   pump_model: GrundfosCR15_Model instance to apply faults to
            
            try
                % Check if we have a valid socket
                if isempty(obj.tcp_socket)
                    return;
                end
                
                % Get the underlying socket for reading
                if isa(obj.tcp_socket, 'TCPSender')
                    % Use the TCPSender's receive method
                    response = obj.tcp_socket.receive(0.01);
                elseif isprop(obj.tcp_socket, 'NumBytesAvailable')
                    % Direct tcpclient socket
                    if obj.tcp_socket.NumBytesAvailable > 0
                        data = read(obj.tcp_socket, obj.tcp_socket.NumBytesAvailable, 'char');
                        response = strtrim(char(data));
                    else
                        response = '';
                    end
                else
                    response = '';
                end
                
                % Process command if we received one
                if ~isempty(response)
                    obj.processCommand(response, pump_model);
                end
                
            catch ME
                % Silently ignore read errors (common when no data)
                if ~contains(ME.identifier, 'MATLAB:tcpclient')
                    fprintf('⚠️  Command check error: %s\n', ME.message);
                end
            end
        end
        
        function processCommand(obj, json_str, pump_model)
            %PROCESSCOMMAND Parse and execute a fault injection command
            %   json_str: JSON command string from Python
            %   pump_model: Pump model to apply fault to
            
            try
                % Handle multiple commands separated by newlines
                commands = strsplit(json_str, newline);
                
                for i = 1:length(commands)
                    cmd_str = strtrim(commands{i});
                    if isempty(cmd_str)
                        continue;
                    end
                    
                    % Parse JSON command
                    cmd = jsondecode(cmd_str);
                    obj.last_command = cmd_str;
                    obj.command_count = obj.command_count + 1;
                    
                    fprintf('\n');
                    fprintf('═══════════════════════════════════════════════════════\n');
                    fprintf('📥 COMMAND RECEIVED FROM PYTHON (#%d)\n', obj.command_count);
                    fprintf('═══════════════════════════════════════════════════════\n');
                    
                    % Process based on command type
                    if isfield(cmd, 'command')
                        switch cmd.command
                            case 'inject_fault'
                                obj.handleInjectFault(cmd, pump_model);
                                
                            case 'reset_fault'
                                obj.handleResetFault(pump_model);
                                
                            case 'get_status'
                                obj.sendStatus();
                                
                            otherwise
                                fprintf('⚠️  Unknown command: %s\n', cmd.command);
                        end
                    else
                        fprintf('⚠️  Invalid command format (no "command" field)\n');
                    end
                end
                
            catch ME
                fprintf('❌ Command processing error: %s\n', ME.message);
                fprintf('   Raw data: %s\n', json_str);
            end
        end
        
        function handleInjectFault(obj, cmd, pump_model)
            %HANDLEINJECTFAULT Apply a fault injection command
            
            fault_type = cmd.fault_type;
            intensity = 1.0;
            if isfield(cmd, 'intensity')
                intensity = cmd.intensity;
            end
            
            fprintf('⚠️  FAULT INJECTION: %s (intensity: %.1f)\n', fault_type, intensity);
            
            % Update internal state
            obj.current_fault = fault_type;
            
            % Extract effects from command or use defaults
            if isfield(cmd, 'effects')
                obj.applyEffects(cmd.effects, intensity);
            else
                obj.applyDefaultFaultEffects(fault_type, intensity);
            end
            
            % Apply to pump model if provided
            if nargin >= 3 && ~isempty(pump_model)
                % The pump model can use the fault_effects to modify its output
                if ismethod(pump_model, 'setFaultEffects')
                    pump_model.setFaultEffects(obj.fault_effects);
                end
                
                % Also inject the fault type directly
                if ismethod(pump_model, 'injectFault')
                    pump_model.injectFault(fault_type);
                end
            end
            
            fprintf('✅ Fault applied. Effects:\n');
            obj.printEffects();
        end
        
        function handleResetFault(obj, pump_model)
            %HANDLERESETFAULT Reset to normal operation
            
            fprintf('✅ RESET: Returning to normal operation\n');
            
            obj.current_fault = 'Normal';
            obj.fault_effects = obj.default_effects;
            
            % Reset pump model
            if nargin >= 2 && ~isempty(pump_model)
                if ismethod(pump_model, 'clearFault')
                    pump_model.clearFault();
                end
                if ismethod(pump_model, 'setFaultEffects')
                    pump_model.setFaultEffects(obj.fault_effects);
                end
            end
            
            fprintf('   All effects reset to normal\n');
        end
        
        function applyEffects(obj, effects, intensity)
            %APPLYEFFECTS Apply effect multipliers from Python command
            
            % Start with defaults
            obj.fault_effects = obj.default_effects;
            
            % Apply each effect from the command
            effect_fields = fieldnames(effects);
            for i = 1:length(effect_fields)
                field = effect_fields{i};
                value = effects.(field);
                
                % Convert field names (Python uses underscore, MATLAB uses same)
                matlab_field = strrep(field, '-', '_');
                
                if isfield(obj.fault_effects, matlab_field)
                    % Scale multipliers by intensity
                    if contains(matlab_field, 'mult')
                        % For multipliers, interpolate from 1.0
                        base_diff = value - 1.0;
                        obj.fault_effects.(matlab_field) = 1.0 + (base_diff * intensity);
                    elseif contains(matlab_field, 'base')
                        % Base values scale directly
                        obj.fault_effects.(matlab_field) = value * intensity;
                    else
                        % Offsets and others scale directly
                        obj.fault_effects.(matlab_field) = value * intensity;
                    end
                end
            end
        end
        
        function applyDefaultFaultEffects(obj, fault_type, intensity)
            %APPLYDEFAULTFAULTEFFECTS Apply predefined effects for a fault type
            
            obj.fault_effects = obj.default_effects;
            
            switch fault_type
                case 'Normal'
                    % Keep defaults
                    
                case 'Winding Defect'
                    obj.fault_effects.vibration_mult = 1.0 + (0.3 * intensity);
                    obj.fault_effects.temp_offset = 25 * intensity;
                    obj.fault_effects.current_mult = 1.0 + (0.15 * intensity);
                    obj.fault_effects.current_imbalance = 0.12 * intensity;
                    
                case 'Supply Fault'
                    obj.fault_effects.voltage_variance = 15 * intensity;
                    obj.fault_effects.current_mult = 1.0 + (0.1 * intensity);
                    obj.fault_effects.current_imbalance = 0.08 * intensity;
                    obj.fault_effects.temp_offset = 12 * intensity;
                    
                case 'Cavitation'
                    obj.fault_effects.vibration_mult = 1.0 + (1.5 * intensity);
                    obj.fault_effects.vibration_base = 5.2 * intensity;
                    obj.fault_effects.pressure_mult = 1.0 - (0.25 * intensity);
                    obj.fault_effects.flow_mult = 1.0 - (0.18 * intensity);
                    obj.fault_effects.pressure_variance = 0.5 * intensity;
                    
                case 'Bearing Wear'
                    obj.fault_effects.vibration_mult = 1.0 + (2.0 * intensity);
                    obj.fault_effects.vibration_base = 7.2 * intensity;
                    obj.fault_effects.temp_offset = 18 * intensity;
                    obj.fault_effects.current_mult = 1.0 + (0.12 * intensity);
                    
                case 'Overload'
                    obj.fault_effects.current_mult = 1.0 + (0.35 * intensity);
                    obj.fault_effects.current_base = 32 * intensity;
                    obj.fault_effects.temp_offset = 30 * intensity;
                    obj.fault_effects.temp_base = 92;
                    obj.fault_effects.vibration_mult = 1.0 + (1.8 * intensity);
                    obj.fault_effects.flow_mult = 1.0 - (0.6 * intensity);
                    
                otherwise
                    fprintf('   Using default effects for unknown fault: %s\n', fault_type);
            end
        end
        
        function printEffects(obj)
            %PRINTEFFECTS Display current fault effects
            
            fprintf('   Vibration: x%.2f (base: %.1f mm/s)\n', ...
                obj.fault_effects.vibration_mult, obj.fault_effects.vibration_base);
            fprintf('   Temperature: +%.1f°C (base: %.1f°C)\n', ...
                obj.fault_effects.temp_offset, obj.fault_effects.temp_base);
            fprintf('   Current: x%.2f (imbalance: %.1f%%)\n', ...
                obj.fault_effects.current_mult, obj.fault_effects.current_imbalance * 100);
            fprintf('   Pressure: x%.2f | Flow: x%.2f\n', ...
                obj.fault_effects.pressure_mult, obj.fault_effects.flow_mult);
        end
        
        function data = applySensorEffects(obj, data)
            %APPLYSENSOREFFECTS Apply fault effects to sensor data
            %   data: Sensor data struct from pump model
            %   Returns: Modified sensor data with fault effects applied
            
            effects = obj.fault_effects;
            
            % Apply vibration effects
            if effects.vibration_base > 0
                data.vibration = effects.vibration_base + (rand() * 0.5);
            else
                data.vibration = data.vibration * effects.vibration_mult;
            end
            
            % Apply temperature effects
            if effects.temp_base > 0
                data.temperature = effects.temp_base + (rand() * 5);
            else
                data.temperature = data.temperature + effects.temp_offset;
            end
            
            % Apply current effects
            if effects.current_base > 0
                base_current = effects.current_base;
            else
                base_current = data.amperage.average * effects.current_mult;
            end
            
            % Apply imbalance
            imbalance = effects.current_imbalance;
            if imbalance > 0
                data.amperage.phase_a = base_current * (1 + imbalance + rand()*0.02);
                data.amperage.phase_b = base_current * (1 - imbalance/2 + rand()*0.02);
                data.amperage.phase_c = base_current * (1 - imbalance/2 + rand()*0.02);
            else
                data.amperage.phase_a = base_current * (1 + rand()*0.02);
                data.amperage.phase_b = base_current * (1 + rand()*0.02);
                data.amperage.phase_c = base_current * (1 + rand()*0.02);
            end
            
            % Recalculate average and imbalance
            data.amperage.average = (data.amperage.phase_a + data.amperage.phase_b + data.amperage.phase_c) / 3;
            max_dev = max([abs(data.amperage.phase_a - data.amperage.average), ...
                          abs(data.amperage.phase_b - data.amperage.average), ...
                          abs(data.amperage.phase_c - data.amperage.average)]);
            data.amperage.imbalance_pct = (max_dev / data.amperage.average) * 100;
            
            % Apply voltage variance
            if effects.voltage_variance > 0
                data.voltage = data.voltage + (rand() - 0.5) * 2 * effects.voltage_variance;
            end
            
            % Apply pressure effects
            data.pressure = data.pressure * effects.pressure_mult;
            if effects.pressure_variance > 0
                data.pressure = data.pressure + (rand() - 0.5) * effects.pressure_variance;
            end
            
            % Apply flow effects
            data.flow_rate = data.flow_rate * effects.flow_mult;
            
            % Update fault state in data
            data.fault_state = obj.current_fault;
        end
        
        function status = getStatus(obj)
            %GETSTATUS Get current handler status
            
            status = struct(...
                'current_fault', obj.current_fault, ...
                'command_count', obj.command_count, ...
                'effects', obj.fault_effects ...
            );
        end
    end
end

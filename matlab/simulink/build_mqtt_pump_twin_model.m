function modelName = build_mqtt_pump_twin_model(varargin)
%BUILD_MQTT_PUMP_TWIN_MODEL Programmatically creates a Simulink model
% containing a MATLAB System block running the MQTTPumpTwin System object.
%
% Usage:
%   build_mqtt_pump_twin_model
%   build_mqtt_pump_twin_model('ModelName','mqtt_pump_twin')
%
% Then open/run the model:
%   open_system('mqtt_pump_twin');
%   set_param('mqtt_pump_twin','SimulationCommand','start');

p = inputParser;
addParameter(p,'ModelName','mqtt_pump_twin');
parse(p,varargin{:});
modelName = p.Results.ModelName;

% Ensure class is on path
thisDir = fileparts(mfilename('fullpath'));
addpath(thisDir);

if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

new_system(modelName);
open_system(modelName);

% Model configuration: discrete fixed-step
set_param(modelName, 'SolverType', 'Fixed-step');
set_param(modelName, 'Solver', 'FixedStepDiscrete');
set_param(modelName, 'FixedStep', '0.1');
set_param(modelName, 'StopTime', 'inf');

% Add MATLAB System block
blk = [modelName '/MQTT Pump Twin'];
add_block('simulink/User-Defined Functions/MATLAB System', blk, 'Position',[220 140 420 220]);

% Point it at our System object
set_param(blk, 'System', 'MQTTPumpTwin');

% MQTT I/O is not code-generation compatible. Run this block in interpreted mode.
% This avoids codegen-phase errors (e.g., try/catch not supported).
try
    set_param(blk, 'SimulateUsing', 'Interpreted execution');
catch
    % Some MATLAB releases use a different parameter name. If this fails,
    % set it manually in the block mask: "Simulate using" -> "Interpreted execution".
end

% (Optional) Tune properties here. Most users will configure via block mask.
% Example:
% set_param(blk, 'Host', 'localhost');
% set_param(blk, 'Port', '1883');

% Add annotation with topic info
annotation(modelName, 'textbox', [0.05 0.72 0.9 0.2], ...
    'String', sprintf(['MQTT Digital Twin (Simulink)\n' ...
    'Publishes:  digital_twin/{pump_id}/telemetry\n' ...
    'Subscribes: digital_twin/{pump_id}/command\n' ...
    'Commands: INJECT_FAULT, RESET, EMERGENCY_STOP']), ...
    'FitBoxToText','on');

save_system(modelName);
end

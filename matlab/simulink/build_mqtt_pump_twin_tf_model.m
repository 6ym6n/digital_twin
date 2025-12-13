function modelName = build_mqtt_pump_twin_tf_model(varargin)
%BUILD_MQTT_PUMP_TWIN_TF_MODEL Create a simple transfer-function-based plant
% and wire it into the MQTTPumpTwin MATLAB System block.
%
% This is intentionally simple: each signal is a first-order discrete lag
% driven by a step input, scaled and biased to nominal operating values.
% Fault effects are applied inside the MQTT block when commands arrive.
%
% Usage:
%   addpath('matlab/simulink');
%   build_mqtt_pump_twin_tf_model('ModelName','mqtt_pump_twin_tf');
%   open_system('mqtt_pump_twin_tf');

p = inputParser;
addParameter(p,'ModelName','mqtt_pump_twin_tf');
addParameter(p,'SampleTime',0.1);
addParameter(p,'StepTime',1.0);
parse(p,varargin{:});

modelName = p.Results.ModelName;
Ts = p.Results.SampleTime;
stepTime = p.Results.StepTime;

thisDir = fileparts(mfilename('fullpath'));
addpath(thisDir);

if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

new_system(modelName);
open_system(modelName);

set_param(modelName, 'SolverType', 'Fixed-step');
set_param(modelName, 'Solver', 'FixedStepDiscrete');
set_param(modelName, 'FixedStep', num2str(Ts));
set_param(modelName, 'StopTime', 'inf');

% Source step (0 -> 1)
stepBlk = [modelName '/u'];
add_block('simulink/Sources/Step', stepBlk, 'Position',[60 80 100 110]);
set_param(stepBlk, 'Time', num2str(stepTime));
set_param(stepBlk, 'Before', '0');
set_param(stepBlk, 'After', '1');

% MATLAB System (MQTT publisher/subscriber)
mqttBlk = [modelName '/MQTT Pump Twin'];
add_block('simulink/User-Defined Functions/MATLAB System', mqttBlk, 'Position',[610 140 820 290]);
set_param(mqttBlk, 'System', 'MQTTPumpTwin');

% Build signals: voltage, vibration, pressure, temperature, amps_A, amps_B, amps_C
signals = {
    struct('name','voltage',    'bias',230.0,'amp',  5.0,'tau', 1.5),
    struct('name','vibration',  'bias',  1.5,'amp',  0.2,'tau', 0.8),
    struct('name','pressure',   'bias',  5.0,'amp',  0.5,'tau', 2.0),
    struct('name','temperature','bias', 65.0,'amp',  2.0,'tau', 8.0),
    struct('name','amps_A',     'bias', 10.0,'amp',  0.4,'tau', 0.6),
    struct('name','amps_B',     'bias', 10.0,'amp',  0.4,'tau', 0.6),
    struct('name','amps_C',     'bias', 10.0,'amp',  0.4,'tau', 0.6)
};

x0 = 170;
y0 = 40;
dy = 70;

for i = 1:numel(signals)
    s = signals{i};

    tfBlk = sprintf('%s/%s_tf', modelName, s.name);
    gainBlk = sprintf('%s/%s_gain', modelName, s.name);
    biasBlk = sprintf('%s/%s_bias', modelName, s.name);
    sumBlk = sprintf('%s/%s_sum', modelName, s.name);

    y = y0 + (i-1) * dy;

    % Discrete first-order lag: y[k] = alpha*y[k-1] + (1-alpha)*u[k]
    alpha = exp(-Ts / max(s.tau, 1e-6));
    num = (1 - alpha);   % unit DC gain
    den = [1, -alpha];

    add_block('simulink/Discrete/Discrete Transfer Fcn', tfBlk, 'Position',[170 y 260 y+30]);
    set_param(tfBlk, 'Numerator', mat2str(num));
    set_param(tfBlk, 'Denominator', mat2str(den));
    set_param(tfBlk, 'SampleTime', num2str(Ts));

    add_block('simulink/Math Operations/Gain', gainBlk, 'Position',[295 y 355 y+30]);
    set_param(gainBlk, 'Gain', num2str(s.amp));

    add_block('simulink/Sources/Constant', biasBlk, 'Position',[295 y+40 355 y+70]);
    set_param(biasBlk, 'Value', num2str(s.bias));

    add_block('simulink/Math Operations/Sum', sumBlk, 'Position',[400 y 430 y+40]);
    set_param(sumBlk, 'Inputs', '++');

    % Wiring: step -> TF -> Gain -> Sum(+)
    add_line(modelName, 'u/1', sprintf('%s_tf/1', s.name), 'autorouting','on');
    add_line(modelName, sprintf('%s_tf/1', s.name), sprintf('%s_gain/1', s.name), 'autorouting','on');
    add_line(modelName, sprintf('%s_gain/1', s.name), sprintf('%s_sum/1', s.name), 'autorouting','on');

    % Bias -> Sum(+)
    add_line(modelName, sprintf('%s_bias/1', s.name), sprintf('%s_sum/2', s.name), 'autorouting','on');

    % Sum -> MQTT block input port i
    add_line(modelName, sprintf('%s_sum/1', s.name), sprintf('MQTT Pump Twin/%d', i), 'autorouting','on');
end

annotation(modelName, 'textbox', [0.05 0.78 0.9 0.18], ...
    'String', sprintf(['Simple TF plant -> MQTT publisher (Simulink)\n' ...
    'Publishes:  digital_twin/{pump_id}/telemetry\n' ...
    'Subscribes: digital_twin/{pump_id}/command\n' ...
    'Faults via commands: INJECT_FAULT, RESET, EMERGENCY_STOP']), ...
    'FitBoxToText','on');

save_system(modelName);
end

function mqtt_digital_twin(varargin)
%MQTT_DIGITAL_TWIN MATLAB-based pump digital twin over MQTT.
%
% Publishes telemetry at ~1 Hz to:
%   {MQTT_BASE_TOPIC}/{MQTT_PUMP_ID}/telemetry
% Subscribes for commands on:
%   {MQTT_BASE_TOPIC}/{MQTT_PUMP_ID}/command
%
% Commands (JSON):
%   {"command":"INJECT_FAULT","fault_type":"WINDING_DEFECT"}
%   {"command":"RESET"}
%   {"command":"EMERGENCY_STOP"}
%
% Telemetry (JSON) matches the backend expectations (flat fields):
%   pump_id, timestamp, seq, fault_state, fault_duration_s,
%   amps_A, amps_B, amps_C, imbalance_pct, voltage, vibration, pressure, temperature
%
% Requirements:
% - MATLAB with MQTT support (mqttclient). If your release doesn't include it,
%   you can still use this file as a template (swap the MQTT transport layer).
%
% Usage examples:
%   mqtt_digital_twin
%   mqtt_digital_twin('Host','localhost','Port',1883,'PumpId','pump01','BaseTopic','digital_twin')

p = inputParser;
addParameter(p,'Host', getenvOrDefault('MQTT_HOST','localhost'));
addParameter(p,'Port', str2double(getenvOrDefault('MQTT_PORT','1883')));
addParameter(p,'PumpId', getenvOrDefault('MQTT_PUMP_ID','pump01'));
addParameter(p,'BaseTopic', getenvOrDefault('MQTT_BASE_TOPIC','digital_twin'));
addParameter(p,'RateHz', 1);
addParameter(p,'NominalVoltage', 230.0);
addParameter(p,'NominalCurrent', 10.0);
addParameter(p,'NominalVibration', 1.5);
addParameter(p,'NominalPressure', 5.0);
addParameter(p,'NominalTemperature', 65.0);
parse(p, varargin{:});

cfg = p.Results;

telemetryTopic = sprintf('%s/%s/telemetry', cfg.BaseTopic, cfg.PumpId);
commandTopic = sprintf('%s/%s/command', cfg.BaseTopic, cfg.PumpId);

rng('shuffle');

state = struct();
state.fault_state = 'NORMAL';
state.fault_start = NaN;
state.seq = uint64(0);

fprintf('MATLAB Digital Twin (MQTT)\n');
fprintf('  Broker: %s:%d\n', cfg.Host, cfg.Port);
fprintf('  Publish: %s\n', telemetryTopic);
fprintf('  Subscribe: %s\n', commandTopic);

% Create MQTT client
client = createMqttClient(cfg.Host, cfg.Port);

% Subscribe to command topic
try
    subscribe(client, commandTopic);
catch subscribeErr
    error('Failed to subscribe to command topic (%s): %s', commandTopic, subscribeErr.message);
end

% Prefer async callback if supported; fall back to polling.
useCallback = false;
try
    if isprop(client,'MessageReceivedFcn')
        client.MessageReceivedFcn = @(~,evt)onMessage(evt);
        useCallback = true;
    end
catch
    useCallback = false;
end

if ~useCallback
    fprintf('Note: MessageReceivedFcn not available; using polling read loop.\n');
end

period = 1 / max(cfg.RateHz, 0.1);

while true
    if ~useCallback
        pollCommands(client);
    end

    state.seq = state.seq + 1;
    dur = faultDurationSeconds(state);

    % Base signals
    voltage = cfg.NominalVoltage * randUniform(0.98, 1.02);
    vibration = cfg.NominalVibration * randUniform(0.8, 1.1);
    pressure = cfg.NominalPressure * randUniform(0.95, 1.05);
    temperature = cfg.NominalTemperature + randUniform(-3, 3);

    a = cfg.NominalCurrent * randUniform(0.98, 1.02);
    b = cfg.NominalCurrent * randUniform(0.98, 1.02);
    c = cfg.NominalCurrent * randUniform(0.98, 1.02);

    % Fault behavior (mirrors the Python simulator logic)
    switch upper(string(state.fault_state))
        case 'WINDING_DEFECT'
            c = c * (1.0 + min(0.05 + double(dur) * 0.01, 0.25));
            temperature = cfg.NominalTemperature + 15 + double(dur) * 2;
        case 'SUPPLY_FAULT'
            voltage = randUniform(190, 207);
        case 'CAVITATION'
            vibration = 5.0 + randUniform(0, 3.0);
            if rand() < 0.3
                vibration = vibration + randUniform(2, 5);
            end
            pressure = max(0.0, cfg.NominalPressure + randUniform(-1.5, 0.5));
        case 'BEARING_WEAR'
            vibration = cfg.NominalVibration + 1.5 + double(dur) * 0.1 + randUniform(-0.3, 0.5);
            temperature = cfg.NominalTemperature + 5 + randUniform(0, 3);
        case 'OVERLOAD'
            a = a * randUniform(1.15, 1.30);
            b = b * randUniform(1.15, 1.30);
            c = c * randUniform(1.15, 1.30);
            voltage = cfg.NominalVoltage * randUniform(0.95, 0.98);
            pressure = cfg.NominalPressure * randUniform(1.1, 1.3);
            temperature = cfg.NominalTemperature + 10 + randUniform(0, 5);
        otherwise
            % NORMAL
    end

    imbalance_pct = computeImbalancePct(a, b, c);

    telemetry = struct();
    telemetry.pump_id = cfg.PumpId;
    telemetry.timestamp = utcNowIso();
    telemetry.seq = double(state.seq);
    telemetry.fault_state = char(upper(string(state.fault_state)));
    telemetry.fault_duration_s = double(dur);
    telemetry.amps_A = a;
    telemetry.amps_B = b;
    telemetry.amps_C = c;
    telemetry.imbalance_pct = imbalance_pct;
    telemetry.voltage = voltage;
    telemetry.vibration = vibration;
    telemetry.pressure = pressure;
    telemetry.temperature = temperature;

    payload = jsonencode(telemetry);

    try
        publish(client, telemetryTopic, payload);
    catch pubErr
        warning('Failed to publish telemetry: %s', pubErr.message);
    end

    pause(period);
end

    function onMessage(evt)
        % Callback handler for received MQTT messages
        try
            % evt might expose Data as string/char/uint8 depending on release
            msg = evt.Data;
            if isnumeric(msg)
                msg = char(msg);
            elseif isstring(msg)
                msg = char(msg);
            end
            applyCommand(msg);
        catch
            % ignore malformed messages
        end
    end

    function pollCommands(cli)
        % Poll any pending messages if callback isn't supported
        try
            % Some releases return a timetable/table, others a struct.
            % Try to read up to 10 messages without blocking.
            data = read(cli, 10, 'Topic', commandTopic, 'Timeout', 0);
            if isempty(data)
                return;
            end

            % If table/timetable, expect a Data variable
            if istable(data) || istimetable(data)
                if any(strcmp('Data', data.Properties.VariableNames))
                    for i = 1:height(data)
                        applyCommand(data.Data{i});
                    end
                end
                return;
            end

            % If struct array, try Data field
            if isstruct(data)
                for i = 1:numel(data)
                    if isfield(data(i),'Data')
                        applyCommand(data(i).Data);
                    end
                end
            end
        catch
            % If polling API differs, it's still fine: callback mode will handle most cases.
        end
    end

    function applyCommand(raw)
        % Normalize raw message
        if isnumeric(raw)
            raw = char(raw);
        end
        if isstring(raw)
            raw = char(raw);
        end
        if ~ischar(raw)
            return;
        end

        s = strtrim(raw);
        if isempty(s)
            return;
        end

        cmdObj = jsondecode(s);
        if ~isstruct(cmdObj) || ~isfield(cmdObj,'command')
            return;
        end

        cmd = upper(string(cmdObj.command));
        switch cmd
            case 'INJECT_FAULT'
                if isfield(cmdObj,'fault_type')
                    f = upper(string(cmdObj.fault_type));
                    fprintf('[CMD] INJECT_FAULT %s\n', f);
                    state.fault_state = char(f);
                    state.fault_start = ticNowSeconds();
                end
            case 'RESET'
                fprintf('[CMD] RESET\n');
                state.fault_state = 'NORMAL';
                state.fault_start = NaN;
            case 'EMERGENCY_STOP'
                fprintf('[CMD] EMERGENCY_STOP\n');
                state.fault_state = 'NORMAL';
                state.fault_start = NaN;
        end
    end
end

% ---- Helpers ----

function client = createMqttClient(host, port)
% Create MQTT client. Prefer tcp:// URL if required by your MATLAB release.

% Some releases accept mqttclient(host,Port=port)
try
    client = mqttclient(host, Port=port);
    return;
catch
end

% Others accept mqttclient("tcp://host:port")
try
    url = sprintf('tcp://%s:%d', host, port);
    client = mqttclient(url);
    return;
catch mqttErr
    error('Unable to create mqttclient. MATLAB error: %s', mqttErr.message);
end
end

function v = randUniform(a, b)
v = a + (b - a) * rand();
end

function pct = computeImbalancePct(a, b, c)
avg = (a + b + c) / 3.0;
if avg == 0
    pct = 0.0;
    return;
end
maxDev = max([abs(a-avg), abs(b-avg), abs(c-avg)]);
pct = (maxDev / avg) * 100.0;
end

function s = utcNowIso()
d = datetime('now','TimeZone','UTC');
s = char(d, 'yyyy-MM-dd''T''HH:mm:ss.SSS''Z''');
end

function t = ticNowSeconds()
% Store an epoch-ish seconds value for duration computations.
% We use posixtime for a stable reference.
t = posixtime(datetime('now','TimeZone','UTC'));
end

function d = faultDurationSeconds(state)
if isnan(state.fault_start)
    d = 0;
    return;
end
nowSec = posixtime(datetime('now','TimeZone','UTC'));
d = max(0, floor(nowSec - state.fault_start));
end

function v = getenvOrDefault(name, defaultValue)
v = getenv(name);
if isempty(v)
    v = defaultValue;
end
end

function mqtt_digital_twin(varargin)
%MQTT_DIGITAL_TWIN MATLAB-based pump digital twin over MQTT.
%#ok<*DEFNU>
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
% Safety/realism: cap temperature so faults don't grow unbounded
addParameter(p,'MaxTemperature', 120.0);
% Realism: first-order dynamics toward targets + small noise (oscillation)
addParameter(p,'DynamicsAlpha', 0.35); % 0..1 (higher = faster convergence)
addParameter(p,'NoiseScale', 1.0);     % scales per-signal noise amplitudes
% Value bounds (used after dynamics)
addParameter(p,'MinVoltage', 0.0);
addParameter(p,'MaxVoltage', 260.0);
addParameter(p,'MinCurrent', 0.0);
addParameter(p,'MaxCurrent', 20.0);
addParameter(p,'MinVibration', 0.0);
addParameter(p,'MaxVibration', 12.0);
addParameter(p,'MinPressure', 0.0);
addParameter(p,'MaxPressure', 12.0);
addParameter(p,'MinTemperature', -20.0);
parse(p, varargin{:});

cfg = p.Results;

telemetryTopic = sprintf('%s/%s/telemetry', cfg.BaseTopic, cfg.PumpId);
commandTopic = sprintf('%s/%s/command', cfg.BaseTopic, cfg.PumpId);

rng('shuffle');

state = struct();
state.fault_state = 'NORMAL';
state.fault_start = NaN;
state.seq = uint64(0);
state.signals = struct();
state.signals.voltage = cfg.NominalVoltage * randUniform(0.98, 1.02);
state.signals.vibration = cfg.NominalVibration * randUniform(0.8, 1.1);
state.signals.pressure = cfg.NominalPressure * randUniform(0.95, 1.05);
state.signals.temperature = cfg.NominalTemperature + randUniform(-3, 3);
state.signals.amps_A = cfg.NominalCurrent * randUniform(0.98, 1.02);
state.signals.amps_B = cfg.NominalCurrent * randUniform(0.98, 1.02);
state.signals.amps_C = cfg.NominalCurrent * randUniform(0.98, 1.02);

% Emergency stop state (true = publish zeros)
state.is_stopped = false;

% Optional setpoints (NaN = inactive)
state.setpoints = struct();
state.setpoints.temperature = NaN;
state.bands = struct();
state.bands.temperature = 2.0;

fprintf('MATLAB Digital Twin (MQTT)\n');
fprintf('  Broker: %s:%d\n', cfg.Host, cfg.Port);
fprintf('  Publish: %s\n', telemetryTopic);
fprintf('  Subscribe: %s\n', commandTopic);

% Create MQTT client
client = createMqttClient(cfg.Host, cfg.Port);

% Subscribe to command topic
try
    mqttSubscribe(client, commandTopic);
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

    % Emergency stop: publish exact zeros (no noise / no oscillation)
    if state.is_stopped
        voltage = 0;
        vibration = 0;
        pressure = 0;
        temperature = 0;
        a = 0;
        b = 0;
        c = 0;
        imbalance_pct = 0;

        telemetry = struct();
        telemetry.pump_id = cfg.PumpId;
        telemetry.timestamp = utcNowIso();
        telemetry.seq = double(state.seq);
        telemetry.fault_state = 'NORMAL';
        telemetry.fault_duration_s = 0;
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
            mqttPublish(client, telemetryTopic, payload);
        catch pubErr
            warning('mqtt_digital_twin:PublishFailed', 'Failed to publish telemetry: %s', pubErr.message);
        end

        pause(period);
        continue;
    end

    alpha = min(max(cfg.DynamicsAlpha, 0.0), 1.0);

    % Base targets (nominal with small jitter)
    voltageT = cfg.NominalVoltage * randUniform(0.98, 1.02);
    vibrationT = cfg.NominalVibration * randUniform(0.8, 1.1);
    pressureT = cfg.NominalPressure * randUniform(0.95, 1.05);
    temperatureT = cfg.NominalTemperature + randUniform(-3, 3);

    aT = cfg.NominalCurrent * randUniform(0.98, 1.02);
    bT = cfg.NominalCurrent * randUniform(0.98, 1.02);
    cT = cfg.NominalCurrent * randUniform(0.98, 1.02);

    % Fault behavior (mirrors the Python simulator logic)
    switch upper(string(state.fault_state))
        case 'WINDING_DEFECT'
            cT = cT * (1.0 + min(0.05 + double(dur) * 0.01, 0.25));
            temperatureT = cfg.NominalTemperature + 15 + double(dur) * 2;
        case 'SUPPLY_FAULT'
            voltageT = randUniform(190, 207);
        case 'CAVITATION'
            vibrationT = 5.0 + randUniform(0, 3.0);
            if rand() < 0.3
                vibrationT = vibrationT + randUniform(2, 5);
            end
            pressureT = max(0.0, cfg.NominalPressure + randUniform(-1.5, 0.5));
        case 'BEARING_WEAR'
            vibrationT = cfg.NominalVibration + 1.5 + double(dur) * 0.1 + randUniform(-0.3, 0.5);
            temperatureT = cfg.NominalTemperature + 5 + randUniform(0, 3);
        case 'OVERLOAD'
            % Overload: sustained high current + heating, mild voltage sag, slight vib increase.
            overFactor = 1.15 + min(double(dur) * 0.01, 0.25); % up to ~1.40
            aT = aT * randUniform(overFactor - 0.03, overFactor + 0.05);
            bT = bT * randUniform(overFactor - 0.03, overFactor + 0.05);
            cT = cT * randUniform(overFactor - 0.03, overFactor + 0.05);

            sag = 0.98 - min(double(dur) * 0.0005, 0.04); % down to ~0.94
            voltageT = cfg.NominalVoltage * randUniform(max(0.92, sag - 0.02), min(0.98, sag + 0.01));

            pressureT = cfg.NominalPressure * randUniform(1.05, 1.20);
            vibrationT = cfg.NominalVibration + 0.3 + min(double(dur) * 0.03, 2.0) + randUniform(-0.2, 0.3);
            temperatureT = cfg.NominalTemperature + 10 + min(double(dur) * 0.5, 35) + randUniform(-1.0, 2.0);
        otherwise
            % NORMAL
    end

    % Fault thresholds / bounds (targets are capped, then signal converges + oscillates)
    % If a temperature setpoint is active, lock temperature into a band around it.
    tempMin = cfg.MinTemperature;
    tempMax = cfg.MaxTemperature;
    if isfinite(state.setpoints.temperature)
        band = state.bands.temperature;
        if ~isfinite(band) || band <= 0
            band = 2.0;
        end
        sp = state.setpoints.temperature;
        temperatureT = sp;
        tempMin = max(cfg.MinTemperature, sp - band);
        tempMax = min(cfg.MaxTemperature, sp + band);
    end

    temperatureT = min(max(temperatureT, tempMin), tempMax);
    voltageT = min(max(voltageT, cfg.MinVoltage), cfg.MaxVoltage);
    vibrationT = min(max(vibrationT, cfg.MinVibration), cfg.MaxVibration);
    pressureT = min(max(pressureT, cfg.MinPressure), cfg.MaxPressure);
    aT = min(max(aT, cfg.MinCurrent), cfg.MaxCurrent);
    bT = min(max(bT, cfg.MinCurrent), cfg.MaxCurrent);
    cT = min(max(cT, cfg.MinCurrent), cfg.MaxCurrent);

    % Noise amplitudes (absolute units) - scaled by NoiseScale
    vNoise = max(0.5, cfg.NominalVoltage * 0.005) * cfg.NoiseScale;
    pNoise = max(0.02, cfg.NominalPressure * 0.01) * cfg.NoiseScale;
    vibNoise = max(0.03, cfg.NominalVibration * 0.05) * cfg.NoiseScale;
    % If we have a setpoint band, set noise relative to that band so we stay inside it.
    if isfinite(state.setpoints.temperature)
        band = state.bands.temperature;
        if ~isfinite(band) || band <= 0
            band = 2.0;
        end
        tNoise = max(0.05, band / 3.0) * cfg.NoiseScale;
    else
        tNoise = max(0.2, 0.5) * cfg.NoiseScale;
    end
    iNoise = max(0.05, cfg.NominalCurrent * 0.01) * cfg.NoiseScale;

    % First-order convergence + oscillation around target
    state.signals.voltage = approachToTarget(state.signals.voltage, voltageT, alpha, vNoise, cfg.MinVoltage, cfg.MaxVoltage);
    state.signals.pressure = approachToTarget(state.signals.pressure, pressureT, alpha, pNoise, cfg.MinPressure, cfg.MaxPressure);
    state.signals.vibration = approachToTarget(state.signals.vibration, vibrationT, alpha, vibNoise, cfg.MinVibration, cfg.MaxVibration);
    state.signals.temperature = approachToTarget(state.signals.temperature, temperatureT, alpha, tNoise, tempMin, tempMax);
    state.signals.amps_A = approachToTarget(state.signals.amps_A, aT, alpha, iNoise, cfg.MinCurrent, cfg.MaxCurrent);
    state.signals.amps_B = approachToTarget(state.signals.amps_B, bT, alpha, iNoise, cfg.MinCurrent, cfg.MaxCurrent);
    state.signals.amps_C = approachToTarget(state.signals.amps_C, cT, alpha, iNoise, cfg.MinCurrent, cfg.MaxCurrent);

    a = state.signals.amps_A;
    b = state.signals.amps_B;
    c = state.signals.amps_C;
    voltage = state.signals.voltage;
    vibration = state.signals.vibration;
    pressure = state.signals.pressure;
    temperature = state.signals.temperature;

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
        mqttPublish(client, telemetryTopic, payload);
    catch pubErr
        warning('mqtt_digital_twin:PublishFailed', 'Failed to publish telemetry: %s', pubErr.message);
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
            % Note: older/newer MQTT client variants differ in supported arguments.
            data = [];
            try
                data = mqttRead(cli, 10, 'Topic', commandTopic, 'Timeout', 0);
            catch
                % ignore and fall back
            end

            if isempty(data)
                try
                    data = mqttRead(cli, 10);
                catch
                end
            end

            if isempty(data)
                try
                    data = mqttRead(cli);
                catch
                end
            end

            if isempty(data)
                return;
            end

            % If table/timetable, expect a Data variable
            if istable(data) || istimetable(data)
                varNames = data.Properties.VariableNames;
                hasData = any(strcmp('Data', varNames));
                hasTopic = any(strcmp('Topic', varNames));
                if hasData
                    for i = 1:height(data)
                        if hasTopic
                            try
                                t = data.Topic(i);
                                if iscell(t)
                                    t = t{1};
                                end
                                if isstring(t)
                                    t = char(t);
                                end
                                if ischar(t) && ~strcmp(t, commandTopic)
                                    continue;
                                end
                            catch
                                % If topic parsing fails, still attempt to apply.
                            end
                        end

                        try
                            msg = data.Data(i);
                            if iscell(msg)
                                msg = msg{1};
                            end
                            applyCommand(msg);
                        catch
                            % ignore per-row failures
                        end
                    end
                end
                return;
            end

            % If struct array, try Data field
            if isstruct(data)
                for i = 1:numel(data)
                    if isfield(data(i),'Topic')
                        try
                            t = data(i).Topic;
                            if isstring(t)
                                t = char(t);
                            end
                            if ischar(t) && ~strcmp(t, commandTopic)
                                continue;
                            end
                        catch
                        end
                    end
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
                state.is_stopped = false;
                if isfield(cmdObj,'fault_type')
                    f = upper(string(cmdObj.fault_type));
                    fprintf('[CMD] INJECT_FAULT %s\n', f);
                    state.fault_state = char(f);
                    state.fault_start = ticNowSeconds();
                end

                % Clear previous setpoints unless explicitly provided in this command.
                state.setpoints.temperature = NaN;
                state.bands.temperature = 2.0;

                % Optional setpoint controls (e.g. temperature_target=90, temperature_band=2)
                if isfield(cmdObj, 'temperature_target')
                    try
                        state.setpoints.temperature = double(cmdObj.temperature_target);
                    catch
                    end
                end
                if isfield(cmdObj, 'temperature_band')
                    try
                        state.bands.temperature = double(cmdObj.temperature_band);
                    catch
                    end
                end
            case 'RESET'
                fprintf('[CMD] RESET\n');
                state.fault_state = 'NORMAL';
                state.fault_start = NaN;
                state.setpoints.temperature = NaN;
                state.is_stopped = false;
            case 'EMERGENCY_STOP'
                fprintf('[CMD] EMERGENCY_STOP\n');
                state.fault_state = 'NORMAL';
                state.fault_start = NaN;
                state.setpoints.temperature = NaN;
                state.is_stopped = true;
        end
    end

    function mqttSubscribe(cli, topic)
        if isempty(cli)
            return;
        end

        if ismethod(cli, 'subscribe')
            cli.subscribe(topic);
            return;
        end

        % Function-based API (package-qualified)
        try
            icomm.mqtt.subscribe(cli, topic);
            return;
        catch
        end

        % Fallback to plain function call
        subscribe(cli, topic);
    end

    function mqttPublish(cli, topic, payload)
        if isempty(cli)
            return;
        end

        % Method-based APIs
        if ismethod(cli, 'publish')
            cli.publish(topic, payload);
            return;
        end
        if ismethod(cli, 'write')
            cli.write(topic, payload);
            return;
        end
        if ismethod(cli, 'send')
            cli.send(topic, payload);
            return;
        end

        % Function-based APIs (try fully qualified first)
        try
            icomm.mqtt.publish(cli, topic, payload);
            return;
        catch
        end

        try
            mqtt.publish(cli, topic, payload);
            return;
        catch
        end

        % Last resort: only call publish(...) if it's not MATLAB codetools publish.
        pubPath = which('publish');
        if ~isempty(pubPath) && contains(lower(pubPath), [filesep 'codetools' filesep])
            error('mqtt_digital_twin:PublishNameClash', 'MATLAB codetools publish is shadowing MQTT publish.');
        end

        publish(cli, topic, payload);
    end

    function data = mqttRead(cli, varargin)
        if isempty(cli)
            data = [];
            return;
        end

        % Prefer method-based read if present
        if ismethod(cli, 'read')
            data = cli.read(varargin{:});
            return;
        end

        % Function-based read (package-qualified)
        try
            data = icomm.mqtt.read(cli, varargin{:});
            return;
        catch
        end

        % Fallback to plain read(...) (some releases expose it as a function)
        data = read(cli, varargin{:});
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

function y = approachToTarget(x, target, alpha, noiseStd, minVal, maxVal)
% First-order lag toward target + gaussian noise; then clamp.
if isempty(x) || ~isfinite(x)
    x = target;
end
if ~isfinite(target)
    target = x;
end
y = x + alpha * (target - x) + noiseStd * randn();
y = min(max(y, minVal), maxVal);
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

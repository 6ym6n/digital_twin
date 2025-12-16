classdef MQTTPumpTwin < matlab.System
    %MQTTPumpTwin Simulink-friendly MQTT pump digital twin.
    %
    % Drop this System object into a Simulink "MATLAB System" block.
    % It will:
    % - Subscribe to: {BaseTopic}/{PumpId}/command
    % - Publish to:   {BaseTopic}/{PumpId}/telemetry
    %
    % Telemetry JSON matches the backend bridge expectations (flat fields):
    %   pump_id, timestamp, seq, fault_state, fault_duration_s,
    %   amps_A, amps_B, amps_C, imbalance_pct,
    %   voltage, vibration, pressure, temperature
    %
    % Commands (JSON):
    %   {"command":"INJECT_FAULT","fault_type":"WINDING_DEFECT"}
    %   {"command":"RESET"}
    %   {"command":"EMERGENCY_STOP"}

    properties(Nontunable)
        % Simulink does not allow char/string parameters to be tunable.
        Host (1,:) char = 'localhost'
        PumpId (1,:) char = 'pump01'
        BaseTopic (1,:) char = 'digital_twin'
    end

    properties(Nontunable)
        Port (1,1) double = 1883
    end

    properties
        RateHz (1,1) double = 1

        NominalVoltage (1,1) double = 230.0
        NominalCurrent (1,1) double = 10.0
        NominalVibration (1,1) double = 1.5
        NominalPressure (1,1) double = 5.0
        NominalTemperature (1,1) double = 65.0

        % Safety/realism: cap temperature so faults don't grow unbounded
        MaxTemperature (1,1) double = 120.0

        % Realism: first-order dynamics toward targets + small noise
        DynamicsAlpha (1,1) double = 0.35
        NoiseScale (1,1) double = 1.0

        % Value bounds
        MinVoltage (1,1) double = 0.0
        MaxVoltage (1,1) double = 260.0
        MinCurrent (1,1) double = 0.0
        MaxCurrent (1,1) double = 20.0
        MinVibration (1,1) double = 0.0
        MaxVibration (1,1) double = 12.0
        MinPressure (1,1) double = 0.0
        MaxPressure (1,1) double = 12.0
        MinTemperature (1,1) double = -20.0
    end

    properties(Access=private)
        Client
        TelemetryTopic (1,:) char
        CommandTopic (1,:) char

        Seq (1,1) uint64 = uint64(0)
        FaultState (1,:) char = 'NORMAL'
        FaultStartEpoch (1,1) double = NaN

        LastPublishEpoch (1,1) double = 0
        PendingMessages cell = {}
        UseCallback (1,1) logical = false

        % Internal signal states (for smooth convergence + oscillation)
        LastVoltage (1,1) double = NaN
        LastVibration (1,1) double = NaN
        LastPressure (1,1) double = NaN
        LastTemperature (1,1) double = NaN
        LastA (1,1) double = NaN
        LastB (1,1) double = NaN
        LastC (1,1) double = NaN

        TemperatureSetpoint (1,1) double = NaN
        TemperatureBand (1,1) double = 2.0

        IsStopped (1,1) logical = false
    end

    methods(Access=protected)
        function setupImpl(obj)
            obj.TelemetryTopic = sprintf('%s/%s/telemetry', obj.BaseTopic, obj.PumpId);
            obj.CommandTopic   = sprintf('%s/%s/command',   obj.BaseTopic, obj.PumpId);

            obj.Client = MQTTPumpTwin.createClient(obj.Host, obj.Port);
            % Use method-call syntax to avoid function name clashes (e.g. MATLAB codetools publish).
            obj.Client.subscribe(obj.CommandTopic);

            % Prefer callback if available; fall back to polling.
            obj.UseCallback = false;
            try
                if isprop(obj.Client, 'MessageReceivedFcn')
                    obj.Client.MessageReceivedFcn = @(~,evt)obj.onMessage(evt);
                    obj.UseCallback = true;
                end
            catch
                obj.UseCallback = false;
            end

            obj.LastPublishEpoch = MQTTPumpTwin.epochSeconds();

            % Initialize internal states near nominal
            obj.LastVoltage = obj.NominalVoltage;
            obj.LastVibration = obj.NominalVibration;
            obj.LastPressure = obj.NominalPressure;
            obj.LastTemperature = obj.NominalTemperature;
            obj.LastA = obj.NominalCurrent;
            obj.LastB = obj.NominalCurrent;
            obj.LastC = obj.NominalCurrent;
        end

        function stepImpl(obj, voltageIn, vibrationIn, pressureIn, temperatureIn, ampsAIn, ampsBIn, ampsCIn)
            % Process commands
            if ~obj.UseCallback
                obj.pollCommands();
            end
            obj.drainPending();

            % Publish telemetry at RateHz
            period = 1 / max(obj.RateHz, 0.1);
            nowEpoch = MQTTPumpTwin.epochSeconds();
            if (nowEpoch - obj.LastPublishEpoch) < period
                return;
            end
            obj.LastPublishEpoch = nowEpoch;

            obj.Seq = obj.Seq + 1;
            dur = obj.faultDurationSeconds(nowEpoch);

            % Emergency stop: publish exact zeros (no noise / no oscillation)
            if obj.IsStopped
                obj.LastVoltage = 0;
                obj.LastVibration = 0;
                obj.LastPressure = 0;
                obj.LastTemperature = 0;
                obj.LastA = 0;
                obj.LastB = 0;
                obj.LastC = 0;

                telemetry = struct();
                telemetry.pump_id = obj.PumpId;
                telemetry.timestamp = MQTTPumpTwin.utcNowIso();
                telemetry.seq = double(obj.Seq);
                telemetry.fault_state = 'NORMAL';
                telemetry.fault_duration_s = 0;
                telemetry.amps_A = 0;
                telemetry.amps_B = 0;
                telemetry.amps_C = 0;
                telemetry.imbalance_pct = 0;
                telemetry.voltage = 0;
                telemetry.vibration = 0;
                telemetry.pressure = 0;
                telemetry.temperature = 0;

                payload = jsonencode(telemetry);
                try
                    obj.Client.publish(obj.TelemetryTopic, payload);
                catch
                end
                return;
            end

            % Base signals come from Simulink inputs (transfer functions / plant model).
            % If inputs are unconnected/invalid, fall back to nominal values.
            voltageT     = obj.sanitize(voltageIn, obj.NominalVoltage);
            vibrationT   = obj.sanitize(vibrationIn, obj.NominalVibration);
            pressureT    = obj.sanitize(pressureIn, obj.NominalPressure);
            temperatureT = obj.sanitize(temperatureIn, obj.NominalTemperature);

            aT = obj.sanitize(ampsAIn, obj.NominalCurrent);
            bT = obj.sanitize(ampsBIn, obj.NominalCurrent);
            cT = obj.sanitize(ampsCIn, obj.NominalCurrent);

            % Fault behavior (mirrors existing Python simulator)
            switch upper(string(obj.FaultState))
                case 'WINDING_DEFECT'
                    cT = cT * (1.0 + min(0.05 + double(dur) * 0.01, 0.25));
                    temperatureT = obj.NominalTemperature + 15 + double(dur) * 2;
                case 'SUPPLY_FAULT'
                    voltageT = MQTTPumpTwin.randUniform(190, 207);
                case 'CAVITATION'
                    vibrationT = 5.0 + MQTTPumpTwin.randUniform(0, 3.0);
                    if rand() < 0.3
                        vibrationT = vibrationT + MQTTPumpTwin.randUniform(2, 5);
                    end
                    pressureT = max(0.0, obj.NominalPressure + MQTTPumpTwin.randUniform(-1.5, 0.5));
                case 'BEARING_WEAR'
                    vibrationT = obj.NominalVibration + 1.5 + double(dur) * 0.1 + MQTTPumpTwin.randUniform(-0.3, 0.5);
                    temperatureT = obj.NominalTemperature + 5 + MQTTPumpTwin.randUniform(0, 3);
                case 'OVERLOAD'
                    % Overload: sustained high current + heating, mild voltage sag, slight vib increase.
                    overFactor = 1.15 + min(double(dur) * 0.01, 0.25); % up to ~1.40
                    aT = aT * MQTTPumpTwin.randUniform(overFactor - 0.03, overFactor + 0.05);
                    bT = bT * MQTTPumpTwin.randUniform(overFactor - 0.03, overFactor + 0.05);
                    cT = cT * MQTTPumpTwin.randUniform(overFactor - 0.03, overFactor + 0.05);

                    sag = 0.98 - min(double(dur) * 0.0005, 0.04); % down to ~0.94
                    voltageT = obj.NominalVoltage * MQTTPumpTwin.randUniform(max(0.92, sag - 0.02), min(0.98, sag + 0.01));

                    pressureT = obj.NominalPressure * MQTTPumpTwin.randUniform(1.05, 1.20);
                    vibrationT = obj.NominalVibration + 0.3 + min(double(dur) * 0.03, 2.0) + MQTTPumpTwin.randUniform(-0.2, 0.3);
                    temperatureT = obj.NominalTemperature + 10 + min(double(dur) * 0.5, 35) + MQTTPumpTwin.randUniform(-1.0, 2.0);
                otherwise
                    % NORMAL
            end

            alpha = min(max(obj.DynamicsAlpha, 0.0), 1.0);

            % Cap targets to bounds
            tempMin = obj.MinTemperature;
            tempMax = obj.MaxTemperature;
            if isfinite(obj.TemperatureSetpoint)
                band = obj.TemperatureBand;
                if ~isfinite(band) || band <= 0
                    band = 2.0;
                end
                temperatureT = obj.TemperatureSetpoint;
                tempMin = max(obj.MinTemperature, temperatureT - band);
                tempMax = min(obj.MaxTemperature, temperatureT + band);
            end

            temperatureT = min(max(temperatureT, tempMin), tempMax);
            voltageT = min(max(voltageT, obj.MinVoltage), obj.MaxVoltage);
            vibrationT = min(max(vibrationT, obj.MinVibration), obj.MaxVibration);
            pressureT = min(max(pressureT, obj.MinPressure), obj.MaxPressure);
            aT = min(max(aT, obj.MinCurrent), obj.MaxCurrent);
            bT = min(max(bT, obj.MinCurrent), obj.MaxCurrent);
            cT = min(max(cT, obj.MinCurrent), obj.MaxCurrent);

            % Per-signal noise amplitudes (absolute units)
            vNoise = max(0.5, obj.NominalVoltage * 0.005) * obj.NoiseScale;
            pNoise = max(0.02, obj.NominalPressure * 0.01) * obj.NoiseScale;
            vibNoise = max(0.03, obj.NominalVibration * 0.05) * obj.NoiseScale;
            if isfinite(obj.TemperatureSetpoint)
                band = obj.TemperatureBand;
                if ~isfinite(band) || band <= 0
                    band = 2.0;
                end
                tNoise = max(0.05, band / 3.0) * obj.NoiseScale;
            else
                tNoise = max(0.2, 0.5) * obj.NoiseScale;
            end
            iNoise = max(0.05, obj.NominalCurrent * 0.01) * obj.NoiseScale;

            % Smooth convergence + oscillation
            obj.LastVoltage = MQTTPumpTwin.approachToTarget(obj.LastVoltage, voltageT, alpha, vNoise, obj.MinVoltage, obj.MaxVoltage);
            obj.LastPressure = MQTTPumpTwin.approachToTarget(obj.LastPressure, pressureT, alpha, pNoise, obj.MinPressure, obj.MaxPressure);
            obj.LastVibration = MQTTPumpTwin.approachToTarget(obj.LastVibration, vibrationT, alpha, vibNoise, obj.MinVibration, obj.MaxVibration);
            obj.LastTemperature = MQTTPumpTwin.approachToTarget(obj.LastTemperature, temperatureT, alpha, tNoise, tempMin, tempMax);
            obj.LastA = MQTTPumpTwin.approachToTarget(obj.LastA, aT, alpha, iNoise, obj.MinCurrent, obj.MaxCurrent);
            obj.LastB = MQTTPumpTwin.approachToTarget(obj.LastB, bT, alpha, iNoise, obj.MinCurrent, obj.MaxCurrent);
            obj.LastC = MQTTPumpTwin.approachToTarget(obj.LastC, cT, alpha, iNoise, obj.MinCurrent, obj.MaxCurrent);

            voltage = obj.LastVoltage;
            pressure = obj.LastPressure;
            vibration = obj.LastVibration;
            temperature = obj.LastTemperature;
            a = obj.LastA;
            b = obj.LastB;
            c = obj.LastC;

            imbalance_pct = MQTTPumpTwin.computeImbalancePct(a, b, c);

            telemetry = struct();
            telemetry.pump_id = obj.PumpId;
            telemetry.timestamp = MQTTPumpTwin.utcNowIso();
            telemetry.seq = double(obj.Seq);
            telemetry.fault_state = obj.FaultState;
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
            obj.publishMessage(obj.TelemetryTopic, payload);
        end

        function releaseImpl(obj)
            try
                if ~isempty(obj.Client)
                    % best-effort cleanup
                    try
                        if ismethod(obj.Client, 'disconnect')
                            obj.Client.disconnect();
                        end
                    catch
                    end
                    obj.Client = [];
                end
            catch
            end
        end

        function resetImpl(obj)
            % Reset simulation state (not broker state)
            obj.Seq = uint64(0);
            obj.FaultState = 'NORMAL';
            obj.FaultStartEpoch = NaN;
            obj.PendingMessages = {};
            obj.LastPublishEpoch = MQTTPumpTwin.epochSeconds();
        end

        function icon = getIconImpl(~)
            icon = "MQTT Pump Twin";
        end

        function num = getNumInputsImpl(~)
            % voltage, vibration, pressure, temperature, amps_A, amps_B, amps_C
            num = 7;
        end

        function num = getNumOutputsImpl(~)
            num = 0;
        end

        function varargout = getInputSizeImpl(~)
            % All scalar signals
            varargout = repmat({[1 1]}, 1, 7);
        end

        function varargout = getInputDataTypeImpl(~)
            varargout = repmat({'double'}, 1, 7);
        end

        function varargout = isInputComplexImpl(~)
            varargout = repmat({false}, 1, 7);
        end

        function varargout = isInputFixedSizeImpl(~)
            varargout = repmat({true}, 1, 7);
        end

        function [name1,name2,name3,name4,name5,name6,name7] = getInputNamesImpl(~)
            name1 = 'voltage';
            name2 = 'vibration';
            name3 = 'pressure';
            name4 = 'temperature';
            name5 = 'amps_A';
            name6 = 'amps_B';
            name7 = 'amps_C';
        end
    end

    methods(Access=private)
        function publishMessage(obj, topic, payload)
            % Publish wrapper to handle different MQTT client APIs and avoid
            % name clashes with MATLAB codetools `publish`.
            client = obj.Client;
            if isempty(client)
                return;
            end

            % Method-based APIs
            if ismethod(client, 'publish')
                client.publish(topic, payload);
                return;
            end

            % Some toolboxes use write/send-style methods.
            if ismethod(client, 'write')
                try
                    client.write(topic, payload);
                    return;
                catch
                end
                try
                    client.write(payload, 'Topic', topic);
                    return;
                catch
                end
            end

            if ismethod(client, 'send')
                try
                    client.send(topic, payload);
                    return;
                catch
                end
                try
                    client.send(payload, 'Topic', topic);
                    return;
                catch
                end
            end

            % Function-based APIs (try fully-qualified first)
            try
                if exist('icomm.mqtt.publish', 'file') == 2
                    icomm.mqtt.publish(client, topic, payload);
                    return;
                end
            catch
            end

            % Last resort: call `publish(client,topic,payload)` only if it is
            % NOT MATLAB's codetools publish (which treats strings as field names).
            pubPath = which('publish');
            if ~isempty(pubPath) && contains(lower(pubPath), [filesep 'codetools' filesep])
                error('MQTTPumpTwin:PublishNotSupported', ...
                    'MQTT publish API not found for client class %s (and publish() resolves to codetools).', class(client));
            end

            publish(client, topic, payload);
        end

        function v = sanitize(~, x, defaultValue)
            try
                if isempty(x)
                    v = defaultValue;
                    return;
                end
                if ~isfinite(double(x))
                    v = defaultValue;
                    return;
                end
                v = double(x);
            catch
                v = defaultValue;
            end
        end

        function onMessage(obj, evt)
            try
                msg = evt.Data;
                if isnumeric(msg)
                    msg = char(msg);
                elseif isstring(msg)
                    msg = char(msg);
                end
                obj.PendingMessages{end+1} = msg; %#ok<AGROW>
            catch
            end
        end

        function pollCommands(obj)
            % Read up to 10 queued command messages without blocking
            try
                data = obj.Client.read(10, 'Topic', obj.CommandTopic, 'Timeout', 0);
                if isempty(data)
                    return;
                end

                if istable(data) || istimetable(data)
                    if any(strcmp('Data', data.Properties.VariableNames))
                        for i = 1:height(data)
                            obj.PendingMessages{end+1} = data.Data{i}; %#ok<AGROW>
                        end
                    end
                    return;
                end

                if isstruct(data)
                    for i = 1:numel(data)
                        if isfield(data(i), 'Data')
                            obj.PendingMessages{end+1} = data(i).Data; %#ok<AGROW>
                        end
                    end
                end
            catch
                % If API differs, callback mode is preferred.
            end
        end

        function drainPending(obj)
            if isempty(obj.PendingMessages)
                return;
            end
            msgs = obj.PendingMessages;
            obj.PendingMessages = {};

            for i = 1:numel(msgs)
                obj.applyCommand(msgs{i});
            end
        end

        function applyCommand(obj, raw)
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
            if ~isstruct(cmdObj) || ~isfield(cmdObj, 'command')
                return;
            end

            cmd = upper(string(cmdObj.command));
            switch cmd
                case 'INJECT_FAULT'
                    obj.IsStopped = false;
                    if isfield(cmdObj, 'fault_type')
                        f = upper(string(cmdObj.fault_type));
                        obj.FaultState = char(f);
                        obj.FaultStartEpoch = MQTTPumpTwin.epochSeconds();
                    end

                    % Clear previous setpoints unless explicitly provided in this command.
                    obj.TemperatureSetpoint = NaN;
                    obj.TemperatureBand = 2.0;

                    if isfield(cmdObj, 'temperature_target')
                        try
                            obj.TemperatureSetpoint = double(cmdObj.temperature_target);
                        catch
                        end
                    end
                    if isfield(cmdObj, 'temperature_band')
                        try
                            obj.TemperatureBand = double(cmdObj.temperature_band);
                        catch
                        end
                    end
                case 'RESET'
                    obj.FaultState = 'NORMAL';
                    obj.FaultStartEpoch = NaN;
                    obj.TemperatureSetpoint = NaN;
                    obj.IsStopped = false;
                case 'EMERGENCY_STOP'
                    obj.FaultState = 'NORMAL';
                    obj.FaultStartEpoch = NaN;
                    obj.TemperatureSetpoint = NaN;
                    obj.IsStopped = true;
            end
        end

        function dur = faultDurationSeconds(obj, nowEpoch)
            if isnan(obj.FaultStartEpoch)
                dur = 0;
                return;
            end
            dur = max(0, floor(nowEpoch - obj.FaultStartEpoch));
        end
    end

    methods(Static, Access=private)
        function client = createClient(host, port)
            % Support both mqttclient(host,Port=port) and mqttclient("tcp://host:port")
            try
                client = mqttclient(host, Port=port);
                return;
            catch
            end
            url = sprintf('tcp://%s:%d', host, port);
            client = mqttclient(url);
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
            d = datetime('now', 'TimeZone', 'UTC');
            s = char(d, 'yyyy-MM-dd''T''HH:mm:ss.SSS''Z''');
        end

        function t = epochSeconds()
            t = posixtime(datetime('now', 'TimeZone', 'UTC'));
        end

        function y = approachToTarget(x, target, alpha, noiseStd, minVal, maxVal)
            if isempty(x) || ~isfinite(x)
                x = target;
            end
            if ~isfinite(target)
                target = x;
            end
            y = x + alpha * (target - x) + noiseStd * randn();
            y = min(max(y, minVal), maxVal);
        end
    end
end

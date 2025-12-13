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

    properties
        Host (1,:) char = 'localhost'
        Port (1,1) double = 1883
        PumpId (1,:) char = 'pump01'
        BaseTopic (1,:) char = 'digital_twin'

        RateHz (1,1) double = 1

        NominalVoltage (1,1) double = 230.0
        NominalCurrent (1,1) double = 10.0
        NominalVibration (1,1) double = 1.5
        NominalPressure (1,1) double = 5.0
        NominalTemperature (1,1) double = 65.0
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
    end

    methods(Access=protected)
        function setupImpl(obj)
            obj.TelemetryTopic = sprintf('%s/%s/telemetry', obj.BaseTopic, obj.PumpId);
            obj.CommandTopic   = sprintf('%s/%s/command',   obj.BaseTopic, obj.PumpId);

            obj.Client = MQTTPumpTwin.createClient(obj.Host, obj.Port);
            subscribe(obj.Client, obj.CommandTopic);

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
        end

        function stepImpl(obj)
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

            % Base signals
            voltage     = obj.NominalVoltage * MQTTPumpTwin.randUniform(0.98, 1.02);
            vibration   = obj.NominalVibration * MQTTPumpTwin.randUniform(0.8, 1.1);
            pressure    = obj.NominalPressure * MQTTPumpTwin.randUniform(0.95, 1.05);
            temperature = obj.NominalTemperature + MQTTPumpTwin.randUniform(-3, 3);

            a = obj.NominalCurrent * MQTTPumpTwin.randUniform(0.98, 1.02);
            b = obj.NominalCurrent * MQTTPumpTwin.randUniform(0.98, 1.02);
            c = obj.NominalCurrent * MQTTPumpTwin.randUniform(0.98, 1.02);

            % Fault behavior (mirrors existing Python simulator)
            switch upper(string(obj.FaultState))
                case 'WINDING_DEFECT'
                    c = c * (1.0 + min(0.05 + double(dur) * 0.01, 0.25));
                    temperature = obj.NominalTemperature + 15 + double(dur) * 2;
                case 'SUPPLY_FAULT'
                    voltage = MQTTPumpTwin.randUniform(190, 207);
                case 'CAVITATION'
                    vibration = 5.0 + MQTTPumpTwin.randUniform(0, 3.0);
                    if rand() < 0.3
                        vibration = vibration + MQTTPumpTwin.randUniform(2, 5);
                    end
                    pressure = max(0.0, obj.NominalPressure + MQTTPumpTwin.randUniform(-1.5, 0.5));
                case 'BEARING_WEAR'
                    vibration = obj.NominalVibration + 1.5 + double(dur) * 0.1 + MQTTPumpTwin.randUniform(-0.3, 0.5);
                    temperature = obj.NominalTemperature + 5 + MQTTPumpTwin.randUniform(0, 3);
                case 'OVERLOAD'
                    a = a * MQTTPumpTwin.randUniform(1.15, 1.30);
                    b = b * MQTTPumpTwin.randUniform(1.15, 1.30);
                    c = c * MQTTPumpTwin.randUniform(1.15, 1.30);
                    voltage = obj.NominalVoltage * MQTTPumpTwin.randUniform(0.95, 0.98);
                    pressure = obj.NominalPressure * MQTTPumpTwin.randUniform(1.1, 1.3);
                    temperature = obj.NominalTemperature + 10 + MQTTPumpTwin.randUniform(0, 5);
                otherwise
                    % NORMAL
            end

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
            publish(obj.Client, obj.TelemetryTopic, payload);
        end

        function releaseImpl(obj)
            try
                if ~isempty(obj.Client)
                    % best-effort cleanup
                    clear obj.Client
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
            num = 0;
        end

        function num = getNumOutputsImpl(~)
            num = 0;
        end
    end

    methods(Access=private)
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
                data = read(obj.Client, 10, 'Topic', obj.CommandTopic, 'Timeout', 0);
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
                    if isfield(cmdObj, 'fault_type')
                        f = upper(string(cmdObj.fault_type));
                        obj.FaultState = char(f);
                        obj.FaultStartEpoch = MQTTPumpTwin.epochSeconds();
                    end
                case 'RESET'
                    obj.FaultState = 'NORMAL';
                    obj.FaultStartEpoch = NaN;
                case 'EMERGENCY_STOP'
                    obj.FaultState = 'NORMAL';
                    obj.FaultStartEpoch = NaN;
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
    end
end

%% =========================================================================
%  TCP SENDER CLASS FOR DIGITAL TWIN
%  Sends sensor data from MATLAB to Python via TCP/IP
%  =========================================================================

classdef TCPSender < handle
    %TCPSENDER TCP client for sending sensor data to Python
    
    properties
        host            % Server hostname
        port            % Server port
        socket          % TCP socket object
        connected       % Connection status
        send_interval   % Interval between sends (seconds)
        bytes_sent      % Total bytes sent
        packets_sent    % Total packets sent
    end
    
    methods
        function obj = TCPSender(host, port)
            %TCPSENDER Constructor
            %   host: Python server hostname (default: 'localhost')
            %   port: Python server port (default: 5555)
            
            if nargin < 1
                host = 'localhost';
            end
            if nargin < 2
                port = 5555;
            end
            
            obj.host = host;
            obj.port = port;
            obj.socket = [];
            obj.connected = false;
            obj.send_interval = 1.0;
            obj.bytes_sent = 0;
            obj.packets_sent = 0;
            
            fprintf('📡 TCP Sender initialized\n');
            fprintf('   Target: %s:%d\n', host, port);
        end
        
        function success = connect(obj)
            %CONNECT Establish TCP connection to Python server
            
            fprintf('🔌 Connecting to %s:%d...\n', obj.host, obj.port);
            
            try
                obj.socket = tcpclient(obj.host, obj.port, ...
                    'Timeout', 10, ...
                    'ConnectTimeout', 10);
                
                obj.connected = true;
                fprintf('✅ Connected to Python server!\n');
                success = true;
                
            catch ME
                fprintf('❌ Connection failed: %s\n', ME.message);
                fprintf('   Make sure Python TCP server is running.\n');
                obj.connected = false;
                success = false;
            end
        end
        
        function disconnect(obj)
            %DISCONNECT Close TCP connection
            
            if ~isempty(obj.socket)
                clear obj.socket;
                obj.socket = [];
            end
            
            obj.connected = false;
            fprintf('📴 Disconnected from Python server\n');
            fprintf('   Total packets sent: %d\n', obj.packets_sent);
            fprintf('   Total bytes sent: %d\n', obj.bytes_sent);
        end
        
        function success = send(obj, data)
            %SEND Send data packet to Python
            %   data: Struct or JSON string to send
            
            if ~obj.connected || isempty(obj.socket)
                fprintf('⚠️  Not connected. Call connect() first.\n');
                success = false;
                return;
            end
            
            try
                % Convert struct to JSON if needed
                if isstruct(data)
                    json_data = jsonencode(data);
                else
                    json_data = data;
                end
                
                % Add delimiter for message framing
                message = [json_data, newline];
                
                % Send data
                write(obj.socket, uint8(message));
                
                obj.bytes_sent = obj.bytes_sent + length(message);
                obj.packets_sent = obj.packets_sent + 1;
                
                success = true;
                
            catch ME
                fprintf('❌ Send failed: %s\n', ME.message);
                obj.connected = false;
                success = false;
            end
        end
        
        function response = receive(obj, timeout)
            %RECEIVE Receive data from Python (if any)
            %   timeout: Max wait time in seconds
            
            if nargin < 2
                timeout = 1.0;
            end
            
            response = '';
            
            if ~obj.connected || isempty(obj.socket)
                return;
            end
            
            try
                if obj.socket.NumBytesAvailable > 0
                    data = read(obj.socket, obj.socket.NumBytesAvailable, 'char');
                    response = strtrim(char(data));
                end
            catch
                % No data available or error
            end
        end
        
        function status = isConnected(obj)
            %ISCONNECTED Check connection status
            
            if isempty(obj.socket)
                status = false;
                return;
            end
            
            try
                % Try to check socket status
                status = obj.connected;
            catch
                status = false;
                obj.connected = false;
            end
        end
        
        function setInterval(obj, interval)
            %SETINTERVAL Set send interval
            %   interval: Time between sends in seconds
            
            obj.send_interval = max(0.1, interval);
            fprintf('📊 Send interval set to %.2f seconds\n', obj.send_interval);
        end
    end
end

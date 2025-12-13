%% =========================================================================
%  GRUNDFOS CR 15 PUMP PARAMETERS
%  Based on official Grundfos CR 15 specifications
%  For Digital Twin Physical Simulation
%  =========================================================================
%
%  Reference: Grundfos CR 15 Data Sheet
%  Pump Type: Vertical Multistage Centrifugal Pump
%
%  Author: Digital Twin Project
%  Date: December 2025
%  =========================================================================

classdef GrundfosCR15_Parameters
    %GRUNDFOSCR15_PARAMETERS Physical parameters for Grundfos CR 15 pump
    %   Contains all physical constants and specifications for the pump model
    
    properties (Constant)
        %% ==== PUMP IDENTIFICATION ====
        MODEL = 'Grundfos CR 15';
        PUMP_TYPE = 'Vertical Multistage Centrifugal';
        
        %% ==== HYDRAULIC PARAMETERS ====
        % Flow rate specifications
        NOMINAL_FLOW_RATE = 15;          % m³/h (nominal)
        MIN_FLOW_RATE = 2;               % m³/h (minimum)
        MAX_FLOW_RATE = 25;              % m³/h (maximum)
        
        % Pressure/Head specifications
        NOMINAL_HEAD = 50;               % m (nominal head per stage)
        MAX_HEAD = 70;                   % m (maximum head)
        STAGES = 5;                      % Number of impeller stages
        
        % Pressure conversion: Head (m) to Pressure (bar)
        % P = ρ * g * H / 100000
        NOMINAL_DISCHARGE_PRESSURE = 5.0;  % bar (at nominal conditions)
        INLET_PRESSURE_MIN = 0.5;        % bar (minimum NPSH)
        
        %% ==== IMPELLER PARAMETERS ====
        IMPELLER_DIAMETER = 0.127;       % m (127 mm)
        IMPELLER_WIDTH = 0.012;          % m (12 mm)
        BLADE_COUNT = 6;                 % Number of blades
        BLADE_ANGLE_INLET = 25;          % degrees
        BLADE_ANGLE_OUTLET = 30;         % degrees
        
        %% ==== MOTOR PARAMETERS ====
        MOTOR_POWER = 5.5;               % kW (rated power)
        MOTOR_VOLTAGE = 400;             % V (3-phase, can also be 230V delta)
        MOTOR_CURRENT = 10.5;            % A (rated current per phase)
        MOTOR_FREQUENCY = 50;            % Hz
        MOTOR_POLES = 2;                 % Number of poles
        SYNCHRONOUS_SPEED = 3000;        % RPM (50Hz, 2-pole)
        NOMINAL_SPEED = 2900;            % RPM (with slip)
        MOTOR_EFFICIENCY = 0.88;         % 88% efficiency
        POWER_FACTOR = 0.85;             % cos(φ)
        
        %% ==== ELECTRICAL PARAMETERS ====
        WINDING_RESISTANCE = 2.5;        % Ohms per phase
        WINDING_INDUCTANCE = 0.015;      % H per phase
        ROTOR_INERTIA = 0.025;           % kg.m² (motor + impeller)
        SLIP = 0.033;                    % 3.3% slip at rated load
        
        %% ==== THERMAL PARAMETERS ====
        AMBIENT_TEMPERATURE = 25;        % °C
        MAX_FLUID_TEMPERATURE = 120;     % °C
        THERMAL_MASS_MOTOR = 15;         % kg
        SPECIFIC_HEAT_MOTOR = 450;       % J/(kg·K) (steel)
        THERMAL_RESISTANCE = 0.5;        % K/W (motor to ambient)
        NOMINAL_OPERATING_TEMP = 65;     % °C (motor winding)
        
        %% ==== MECHANICAL PARAMETERS ====
        SHAFT_DIAMETER = 0.022;          % m (22 mm)
        BEARING_TYPE = 'Angular Contact Ball';
        BEARING_LIFE_HOURS = 20000;      % hours (L10 life)
        SEAL_TYPE = 'Mechanical Shaft Seal';
        
        %% ==== FLUID PARAMETERS (Water at 20°C) ====
        FLUID_DENSITY = 998;             % kg/m³
        FLUID_VISCOSITY = 0.001;         % Pa.s (dynamic viscosity)
        FLUID_BULK_MODULUS = 2.2e9;      % Pa
        
        %% ==== PUMP CURVE COEFFICIENTS ====
        % H = A - B*Q² (simplified parabolic head curve)
        % Fitted for CR 15 at 2900 RPM
        CURVE_COEFF_A = 55;              % m (shutoff head)
        CURVE_COEFF_B = 0.12;            % m/(m³/h)²
        
        % Efficiency curve: η = C*Q - D*Q² (simplified)
        EFF_COEFF_C = 0.08;
        EFF_COEFF_D = 0.002;
        
        %% ==== VIBRATION PARAMETERS ====
        % ISO 10816 vibration limits for rotating machinery
        VIBRATION_GOOD = 1.8;            % mm/s RMS (good condition)
        VIBRATION_ACCEPTABLE = 4.5;      % mm/s RMS (acceptable)
        VIBRATION_ALARM = 7.1;           % mm/s RMS (alarm)
        VIBRATION_DANGER = 11.2;         % mm/s RMS (danger/shutdown)
        
        %% ==== SENSOR NOISE PARAMETERS ====
        % Realistic sensor noise for simulation
        PRESSURE_NOISE_STD = 0.02;       % bar
        FLOW_NOISE_STD = 0.1;            % m³/h
        TEMP_NOISE_STD = 0.3;            % °C
        CURRENT_NOISE_STD = 0.05;        % A
        VIBRATION_NOISE_STD = 0.1;       % mm/s
        
        %% ==== SIMULATION PARAMETERS ====
        SIMULATION_TIMESTEP = 0.1;       % s (10 Hz sampling)
        TCP_SEND_INTERVAL = 1.0;         % s (1 Hz to Python)
    end
    
    methods (Static)
        function H = calculateHead(Q, rpm)
            %CALCULATEHEAD Calculate pump head using affinity laws
            %   Q: Flow rate in m³/h
            %   rpm: Rotational speed
            %   Returns: Head in meters
            
            % Speed ratio from nominal
            n_ratio = rpm / GrundfosCR15_Parameters.NOMINAL_SPEED;
            
            % Adjusted coefficients using affinity laws
            A_adj = GrundfosCR15_Parameters.CURVE_COEFF_A * n_ratio^2;
            B_adj = GrundfosCR15_Parameters.CURVE_COEFF_B;
            
            % Head calculation
            H = A_adj - B_adj * (Q / n_ratio)^2;
            H = max(0, H);  % Head cannot be negative
        end
        
        function P = calculatePressure(H)
            %CALCULATEPRESSURE Convert head to pressure
            %   H: Head in meters
            %   Returns: Pressure in bar
            
            rho = GrundfosCR15_Parameters.FLUID_DENSITY;
            g = 9.81;
            P = rho * g * H / 100000;  % Convert Pa to bar
        end
        
        function eta = calculateEfficiency(Q)
            %CALCULATEEFFICIENCY Calculate pump efficiency
            %   Q: Flow rate in m³/h
            %   Returns: Efficiency (0-1)
            
            C = GrundfosCR15_Parameters.EFF_COEFF_C;
            D = GrundfosCR15_Parameters.EFF_COEFF_D;
            
            eta = C * Q - D * Q^2;
            eta = min(max(eta, 0), 0.85);  % Clamp to realistic range
        end
        
        function P_shaft = calculateShaftPower(Q, H, eta)
            %CALCULATESHAFTPOWER Calculate required shaft power
            %   Q: Flow rate in m³/h
            %   H: Head in meters
            %   eta: Efficiency
            %   Returns: Power in kW
            
            rho = GrundfosCR15_Parameters.FLUID_DENSITY;
            g = 9.81;
            Q_m3s = Q / 3600;  % Convert to m³/s
            
            P_hydraulic = rho * g * Q_m3s * H;  % Watts
            P_shaft = P_hydraulic / max(eta, 0.1) / 1000;  % kW
        end
        
        function I = calculateCurrent(P_shaft, V, pf, eta_motor)
            %CALCULATECURRENT Calculate motor current
            %   P_shaft: Shaft power in kW
            %   V: Voltage
            %   pf: Power factor
            %   eta_motor: Motor efficiency
            %   Returns: Current per phase in A
            
            P_elec = P_shaft * 1000 / eta_motor;  % Electrical power in W
            I = P_elec / (sqrt(3) * V * pf);
        end
        
        function T = calculateTemperature(I, T_ambient, R_thermal, t)
            %CALCULATETEMPERATURE Calculate motor temperature rise
            %   I: Current in A
            %   T_ambient: Ambient temperature in °C
            %   R_thermal: Thermal resistance K/W
            %   t: Time constant factor
            %   Returns: Motor temperature in °C
            
            R_winding = GrundfosCR15_Parameters.WINDING_RESISTANCE;
            P_loss = 3 * I^2 * R_winding;  % 3-phase losses
            
            T_rise = P_loss * R_thermal * (1 - exp(-t));
            T = T_ambient + T_rise;
        end
    end
end

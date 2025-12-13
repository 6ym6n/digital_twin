# MATLAB Digital Twin Integration Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DIGITAL TWIN SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 MATLAB / Simulink (Physical Twin)                │   │
│  │                                                                   │   │
│  │   ┌───────────────┐     ┌──────────────┐     ┌───────────────┐   │   │
│  │   │ GrundfosCR15  │     │   Sensors    │     │  TCP Sender   │   │   │
│  │   │    Model      │────▶│  (P,Q,T,I)   │────▶│  (JSON)       │   │   │
│  │   └───────────────┘     └──────────────┘     └───────┬───────┘   │   │
│  │                                                       │           │   │
│  └───────────────────────────────────────────────────────│───────────┘   │
│                                                          │               │
│                                    TCP/IP (Port 5555)    ▼               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  Python (Intelligence Layer)                     │    │
│  │                                                                   │    │
│  │   ┌───────────────┐     ┌──────────────┐     ┌───────────────┐   │    │
│  │   │ MATLAB Bridge │     │  AI Agent    │     │   FastAPI     │   │    │
│  │   │ (TCP Server)  │────▶│  (Gemini)    │────▶│   Backend     │   │    │
│  │   └───────────────┘     └──────────────┘     └───────────────┘   │    │
│  │                                                       │           │    │
│  └───────────────────────────────────────────────────────│───────────┘    │
│                                                          │                │
│                                   WebSocket              ▼                │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                    Frontend (React Dashboard)                    │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Python Simulation (Default)
```bash
# Start backend with Python simulation
cd digital_twin
python backend/api.py
```

### Option 2: MATLAB Simulation
```bash
# Terminal 1: Start Python backend in MATLAB mode
set DT_DATA_SOURCE=matlab
python backend/api.py

# Terminal 2: In MATLAB
cd matlab
startup_digital_twin
```

## File Structure

```
digital_twin/
├── matlab/                           # MATLAB simulation files
│   ├── GrundfosCR15_Parameters.m    # Pump specifications
│   ├── GrundfosCR15_Model.m         # Physical model class
│   ├── TCPCommunication.m           # TCP sender/server classes
│   ├── run_simulation.m             # Main simulation script
│   ├── create_simulink_model.m      # Simulink model builder
│   └── startup_digital_twin.m       # Quick start script
│
├── src/                              # Python source code
│   ├── simulator.py                 # Python simulation (original)
│   ├── matlab_bridge.py             # MATLAB-Python TCP bridge
│   ├── ai_agent.py                  # AI diagnostic agent
│   ├── rag_engine.py                # RAG knowledge retrieval
│   └── config.py                    # Configuration management
│
├── backend/
│   └── api.py                       # FastAPI server
│
├── frontend/                         # React dashboard
│
└── config.json                       # Global configuration
```

## MATLAB Components

### 1. GrundfosCR15_Parameters.m
Contains all physical specifications for the Grundfos CR 15 pump:
- Hydraulic parameters (flow rate, pressure, head)
- Motor specifications (power, voltage, current, speed)
- Thermal parameters
- Vibration thresholds (ISO 10816)

```matlab
% Access parameters
params = GrundfosCR15_Parameters;
disp(params.NOMINAL_FLOW_RATE);  % 15 m³/h
disp(params.MOTOR_POWER);         % 5.5 kW
```

### 2. GrundfosCR15_Model.m
Physics-based pump model with:
- Pump curve (H-Q characteristic)
- Motor electrical model (3-phase)
- Thermal model
- Vibration model
- Fault injection capability

```matlab
% Create and use model
pump = GrundfosCR15_Model();
pump.step(0.1);  % Advance by 0.1 seconds
data = pump.getSensorData();  % Get sensor readings

% Inject faults
pump.injectFault('Cavitation');
pump.clearFault();
```

### 3. TCPCommunication.m
TCP client for streaming data to Python:

```matlab
tcp = TCPSender('localhost', 5555);
tcp.connect();
tcp.send(pump.getSensorData());
tcp.disconnect();
```

### 4. run_simulation.m
Main entry point with various options:

```matlab
% Normal operation
run_simulation()

% Demo with automatic fault injection
run_simulation('scenario', 'demo')

% Custom configuration
run_simulation('host', '192.168.1.100', 'port', 5556, 'duration', 300)
```

## Python Components

### 1. matlab_bridge.py
TCP server that receives MATLAB data:

```python
from src.matlab_bridge import MATLABBridge

# Start TCP server
bridge = MATLABBridge()
bridge.start_server()

# Get readings (same interface as PumpSimulator)
reading = bridge.get_sensor_reading()
```

### 2. HybridSimulator
Unified interface for both data sources:

```python
from src.matlab_bridge import HybridSimulator

# Use MATLAB source
simulator = HybridSimulator(source='matlab')
simulator.start()

# Switch sources at runtime
simulator.switch_source('python')
```

## Data Format

### JSON Payload (MATLAB → Python)
```json
{
  "timestamp": 123.45,
  "datetime": "2025-12-13T10:30:00",
  "amperage": {
    "phase_a": 10.25,
    "phase_b": 10.18,
    "phase_c": 10.21,
    "average": 10.21,
    "imbalance_pct": 0.35
  },
  "voltage": 398.5,
  "vibration": 1.65,
  "pressure": 5.12,
  "temperature": 67.3,
  "flow_rate": 14.8,
  "rpm": 2895,
  "power": 5.42,
  "fault_state": "Normal",
  "fault_duration": 0
}
```

## Configuration

### Environment Variables
```bash
# Data source ('python' or 'matlab')
DT_DATA_SOURCE=matlab

# TCP settings
DT_TCP_HOST=0.0.0.0
DT_TCP_PORT=5555

# API settings
DT_API_HOST=0.0.0.0
DT_API_PORT=8000
```

### config.json
```json
{
  "data_source": "matlab",
  "tcp": {
    "host": "0.0.0.0",
    "port": 5555
  }
}
```

## API Endpoints

### Switch Data Source
```bash
# Switch to MATLAB
curl -X POST http://localhost:8000/api/switch-source \
  -H "Content-Type: application/json" \
  -d '{"source": "matlab"}'

# Switch to Python
curl -X POST http://localhost:8000/api/switch-source \
  -H "Content-Type: application/json" \
  -d '{"source": "python"}'
```

### Get Status
```bash
curl http://localhost:8000/api/status
```

## Fault Injection

### From MATLAB
```matlab
pump = GrundfosCR15_Model();

% Available faults
pump.injectFault('Winding Defect');
pump.injectFault('Supply Fault');
pump.injectFault('Cavitation');
pump.injectFault('Bearing Wear');
pump.injectFault('Overload');

% Clear fault
pump.clearFault();
```

### From Python API (when using Python source)
```bash
curl -X POST http://localhost:8000/api/inject-fault \
  -H "Content-Type: application/json" \
  -d '{"fault_type": "CAVITATION"}'
```

## Simulink Integration (Optional)

For Simscape Fluids integration:

```matlab
% Create Simulink model (requires Simscape toolboxes)
create_simulink_model('GrundfosCR15_Simulink')
```

This creates a model with:
- Centrifugal pump block
- Pressure sensors (inlet/outlet)
- Flow sensor
- Motor model
- Data logging to workspace

## Troubleshooting

### Connection Issues
1. Ensure Python server is started first
2. Check firewall settings for port 5555
3. Verify IP address if not localhost

### No Data Received
1. Check MATLAB TCP connection status
2. Verify JSON format in MATLAB output
3. Check Python bridge status: `GET /api/status`

### Performance Issues
1. Reduce send rate: `run_simulation('sendrate', 1)`
2. Increase simulation timestep
3. Check network latency

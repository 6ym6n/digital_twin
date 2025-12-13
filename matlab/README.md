# MATLAB Digital Twin (MQTT)

This folder contains a MATLAB-based pump “digital twin” that publishes telemetry over MQTT and listens for control commands.

It is designed to work with the existing backend MQTT bridge:
- Telemetry topic: `digital_twin/{pump_id}/telemetry`
- Command topic: `digital_twin/{pump_id}/command`

## Requirements

- MATLAB release with `mqttclient` support (in MATLAB, run `which mqttclient`).
- A running MQTT broker (e.g., Mosquitto on `localhost:1883`).

## Run

In MATLAB (from this repo root):

```matlab
addpath('matlab');
mqtt_digital_twin;
```

Or configure explicitly:

```matlab
mqtt_digital_twin('Host','localhost','Port',1883,'PumpId','pump01','BaseTopic','digital_twin');
```

## Run (Simulink, MATLAB R2025b)

This repo includes a Simulink-friendly implementation using a **MATLAB System** block.

In MATLAB:

```matlab
addpath('matlab/simulink');
build_mqtt_pump_twin_model('ModelName','mqtt_pump_twin');
open_system('mqtt_pump_twin');
```

Then press **Run**. The model publishes telemetry and reacts to commands using the same topics as the backend.

### If Simulink shows a code generation / compile error

If you see an error like:
"Try and catch are not supported for code generation" (or any codegen-related error), set the MATLAB System block to interpreted execution:

- Open the block: `mqtt_pump_twin_tf/MQTT Pump Twin`
- In Block Parameters, set **Simulate using** → **Interpreted execution**

(The provided model builder scripts try to set this automatically.)

### Simple transfer-function plant (recommended)

If you want a minimal "plant" (first-order transfer functions) feeding the MQTT publisher, use:

```matlab
addpath('matlab/simulink');
build_mqtt_pump_twin_tf_model('ModelName','mqtt_pump_twin_tf');
open_system('mqtt_pump_twin_tf');
```

## Environment variables (optional)

The script reads these if present:
- `MQTT_HOST` (default `localhost`)
- `MQTT_PORT` (default `1883`)
- `MQTT_PUMP_ID` (default `pump01`)
- `MQTT_BASE_TOPIC` (default `digital_twin`)

## Command payloads

The backend (or any MQTT client) can publish commands as JSON:

- Inject fault
  ```json
  {"command":"INJECT_FAULT","fault_type":"WINDING_DEFECT"}
  ```

- Reset
  ```json
  {"command":"RESET"}
  ```

- Emergency stop
  ```json
  {"command":"EMERGENCY_STOP"}
  ```

Supported `fault_type` values:
- `WINDING_DEFECT`, `SUPPLY_FAULT`, `CAVITATION`, `BEARING_WEAR`, `OVERLOAD`

## Telemetry schema

Published telemetry matches what the backend expects (flat fields):
- `pump_id`, `timestamp`, `seq`, `fault_state`, `fault_duration_s`
- `amps_A`, `amps_B`, `amps_C`, `imbalance_pct`
- `voltage`, `vibration`, `pressure`, `temperature`

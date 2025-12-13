# Simulation (MQTT + Digital Twin)

This repo supports two ways to produce sensor telemetry:

1) **Local Python simulator** (`src/simulator.py`) → backend reads it directly
2) **External simulator via MQTT** (MATLAB script or Simulink model) → backend uses the MQTT bridge to consume telemetry

This document explains the **MQTT simulation setup**, how **fault injection** works, and how the **manual Diagnose (RAG)** workflow is triggered.

---

## 1) Architecture (MQTT mode)

In MQTT mode, telemetry and commands flow like this:

- **MATLAB/Simulink Digital Twin** publishes sensor telemetry to MQTT
- **Backend MQTT bridge** subscribes to telemetry, normalizes it, and exposes it to the frontend via WebSocket/REST
- **Frontend** displays the live telemetry
- **Fault injection** sends an MQTT command back to the simulator
- **Diagnose** (RAG) is **manual**: it runs only when you click the **Diagnose** button

### MQTT topics

Default topics (configurable via env vars):

- Telemetry: `digital_twin/{pump_id}/telemetry`
- Commands: `digital_twin/{pump_id}/command`

Example for `pump01`:

- `digital_twin/pump01/telemetry`
- `digital_twin/pump01/command`

---

## 2) Run the full system (Windows)

### 2.1 Start an MQTT broker

You need a broker (e.g., Mosquitto) running locally:

- Host: `localhost`
- Port: `1883`

### 2.2 Start the backend in MQTT mode

From repo root (PowerShell):

```powershell
$env:SENSOR_SOURCE='mqtt'
$env:MQTT_HOST='localhost'
$env:MQTT_PORT='1883'
$env:MQTT_PUMP_ID='pump01'
$env:MQTT_BASE_TOPIC='digital_twin'

python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

### 2.3 Start the frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

### 2.4 Start the simulator (choose one)

#### Option A — MATLAB script publisher

In MATLAB (repo root):

```matlab
addpath('matlab');
mqtt_digital_twin;
```

#### Option B — Simulink model (MATLAB System)

In MATLAB:

```matlab
addpath('matlab/simulink');
build_mqtt_pump_twin_tf_model('ModelName','mqtt_pump_twin_tf');
open_system('mqtt_pump_twin_tf');
```

Then press **Run**.

---

## 3) Telemetry schema

The external simulator publishes a flat JSON payload matching what the backend expects:

- `pump_id`, `timestamp`, `seq`
- `fault_state`, `fault_duration_s`
- `amps_A`, `amps_B`, `amps_C`, `imbalance_pct`
- `voltage`, `vibration`, `pressure`, `temperature`

The backend normalizes it and exposes it under:

- `amperage.phase_a/phase_b/phase_c/average/imbalance_pct`
- `voltage`, `vibration`, `pressure`, `temperature`

---

## 4) Fault injection (commands)

Fault injection is done by publishing a JSON command to the command topic.

### 4.1 Basic fault injection

```json
{"command":"INJECT_FAULT","fault_type":"WINDING_DEFECT"}
```

Supported `fault_type` values:

- `WINDING_DEFECT`
- `SUPPLY_FAULT`
- `CAVITATION`
- `BEARING_WEAR`
- `OVERLOAD`

### 4.2 Temperature setpoint + band (lock into a range)

If you want temperature to stabilize around a target value (example: **90 ± 2** ⇒ **88..92**), add:

```json
{
  "command":"INJECT_FAULT",
  "fault_type":"WINDING_DEFECT",
  "temperature_target":90,
  "temperature_band":2
}
```

The MATLAB/Simulink publishers will then clamp temperature into `[target-band, target+band]`.

### 4.3 Reset

```json
{"command":"RESET"}
```

- Clears the active fault
- Clears the optional setpoints
- Exits emergency-stop mode

### 4.4 Emergency stop

```json
{"command":"EMERGENCY_STOP"}
```

Behavior:

- Simulator enters **stopped mode** and publishes **exact zeros** for all sensors (no oscillation)
- Frontend immediately shows all sensors as **0**
- Stopped mode remains active until `RESET` (or a new `INJECT_FAULT`)

---

## 5) Manual Diagnose (RAG)

Important: **Diagnosis is manual**.

- When a fault is active, the UI shows a message like “Fault detected → click Diagnose”.
- Only when you click **Diagnose** does the frontend call:
  - `POST /api/diagnose` with the latest sensor snapshot

The backend then:

1) Builds a RAG query based on anomalies
2) Retrieves relevant chunks from the knowledge base
3) Calls the LLM to generate:
   - diagnosis
   - root cause
   - recommended actions

Note: Clicking **Diagnose** does **not** automatically trigger emergency stop.

---

## 6) Quick command-line testing (Mosquitto)

Inject fault:

```powershell
mosquitto_pub -h localhost -p 1883 -t digital_twin/pump01/command -m "{\"command\":\"INJECT_FAULT\",\"fault_type\":\"CAVITATION\"}"
```

Inject fault + temperature lock (90 ± 2):

```powershell
mosquitto_pub -h localhost -p 1883 -t digital_twin/pump01/command -m "{\"command\":\"INJECT_FAULT\",\"fault_type\":\"WINDING_DEFECT\",\"temperature_target\":90,\"temperature_band\":2}"
```

Emergency stop:

```powershell
mosquitto_pub -h localhost -p 1883 -t digital_twin/pump01/command -m "{\"command\":\"EMERGENCY_STOP\"}"
```

Reset:

```powershell
mosquitto_pub -h localhost -p 1883 -t digital_twin/pump01/command -m "{\"command\":\"RESET\"}"
```

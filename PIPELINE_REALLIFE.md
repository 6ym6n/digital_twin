# 🏭 Real‑Life Pipeline (Production) — Digital Twin for Predictive Maintenance

This document describes how the pipeline typically looks **in a real industrial deployment**, and how it maps to this repository’s architecture (Simulink/MATLAB twin → MQTT → FastAPI analytics → React dashboard).

---

## 1) What “real life” changes vs. a demo

In production, you usually have:
- **Real sensors** (or PLC signals), not a Python simulator.
- A **controls layer** (PLC/DCS/SCADA) that must remain authoritative for safety.
- **OT/IT separation** with a DMZ, gateways, and strict firewall rules.
- **Historian + CMMS/EAM** integrations (PI, Historian, Maximo, SAP PM).
- **Reliability + observability** requirements (buffering, replay, monitoring).

The “digital twin” can be:
- **A plant model** (Simulink/Simscape) generating expected behavior.
- **A state estimator** that fuses measured signals + model.
- **A what‑if simulator** for faults and maintenance actions.

---

## 2) End‑to‑end flow (conceptual)

```
Physical Pump + Motor + VFD
   │
   │  (pressure, vibration, temperature, current, voltage, flow, etc.)
   ▼
Sensors / Transmitters
   │
   ▼
PLC / VFD / DCS (controls + interlocks)
   │
   ├─► SCADA/HMI (operators)
   ├─► Historian (long-term storage)
   │
   ▼
Edge Gateway / OPC UA / MQTT Publisher (OT → IT bridge)
   │
   ▼
MQTT Broker (often in OT DMZ or edge)
   │
   ├─► Analytics Backend (FastAPI in this repo)
   │       ├─ anomaly detection + rules
   │       ├─ diagnosis + RAG
   │       └─ publishes recommendations/commands
   │
   └─► Digital Twin Model (MATLAB/Simulink) (can be:
           a) publishing simulated telemetry, or
           b) subscribing to real telemetry & publishing residuals)

Commands / Actions
   │
   ├─► Operator workflows (recommended)
   └─► Automated actions (carefully gated)
        ▼
      PLC/VFD interlock inputs / safe stop
```

Key rule: **Safety actions must be enforced by PLC/VFD logic**, not by the dashboard.

---

## 3) Data ingestion layer (OT → MQTT)

### Typical sources
- **PLC tags** (Modbus, Profinet, EtherNet/IP) surfaced via OPC UA.
- **VFD telemetry** (current/voltage/torque/speed).
- **Condition monitoring** (vibration sensors, accelerometers).

### Edge gateway responsibilities
- Normalize signals (units, scaling, timestamps).
- Add metadata (asset ID, location, firmware, quality flags).
- Buffer if network drops.
- Publish MQTT telemetry to a broker.

### MQTT in production
- Broker placement: often **edge/DMZ**.
- Security:
  - **TLS** (MQTTS), per-device client certs if possible.
  - Username/password at minimum.
  - ACLs so each asset can only publish/subscribe to allowed topics.
- Reliability:
  - QoS 0 for high-rate telemetry, QoS 1 for commands/alarms.
  - Retained messages for “last known config” or status.
  - Last Will and Testament (LWT) for device online/offline.

---

## 4) Digital twin (Simulink) role in real life

There are two common patterns:

### A) Twin publishes telemetry (demo / lab / HIL)
- Simulink is the “plant” producing synthetic telemetry.
- Backend treats it like real sensors.

**This repo supports this directly**: the Simulink model publishes telemetry over MQTT, and the backend consumes it.

### B) Twin consumes real telemetry + publishes residuals (more realistic)
- Twin subscribes to real telemetry.
- Simulink generates expected signals and computes residuals:
  - $r(t) = y_{measured}(t) - y_{expected}(t)$
- Backend ingests both measured data and residuals for diagnostics.

This pattern makes the “twin” a true estimator/comparator rather than just a signal generator.

---

## 5) Backend (analytics + AI + APIs)

In production, the backend typically provides:
- **Real-time streaming** (WebSockets) for dashboards.
- **Rule-based safety heuristics** (fast, deterministic):
  - e.g., temperature > threshold, vibration spikes, undervoltage.
- **Anomaly detection** (statistical / ML):
  - baselines by operating regime (speed, load, process conditions).
- **Diagnostics** (LLM/RAG as decision support):
  - “What does this symptom usually mean?”
  - “What checks do technicians do next?”
- **Integrations**:
  - Historian for long-term data.
  - CMMS/EAM for work orders.

### Mapping to this repo
- MQTT telemetry → `backend/mqtt_bridge.py`
- API + WebSocket → `backend/api.py`
- RAG/LLM diagnosis → `src/ai_agent.py` + `src/rag_engine.py`
- Dashboard → `frontend/`

---

## 6) Command and control (how to do it safely)

There are three maturity levels:

### Level 1 — Advisory only (recommended starting point)
- Backend publishes **recommendations** and **alerts**.
- Humans execute actions in SCADA/PLC/HMI.

### Level 2 — Assisted control (guarded)
- Backend can publish a **command request**.
- A controller (or operator approval) must confirm.

### Level 3 — Automatic protective action (rare, highly controlled)
- Backend publishes an emergency stop request.
- PLC/VFD still implements the actual safe stop and interlocks.

In MQTT terms:
- Telemetry: `digital_twin/{pump_id}/telemetry`
- Commands: `digital_twin/{pump_id}/command`
- (Recommended) Events/alerts: `digital_twin/{pump_id}/events`

---

## 7) Storage, replay, and auditability

In real deployments you usually add:
- **Short-term time-series store** for recent high-resolution data.
- **Long-term historian** for months/years.
- **Event log** for commands, alarms, and operator actions.

Why:
- You need to answer: “What did the system see when it decided X?”
- You need traceability for safety and maintenance audits.

---

## 8) Observability and operations

Minimum operational signals to monitor:
- MQTT broker health, client connections, dropped messages.
- “Seconds since last telemetry message” per asset.
- Backend latency (ingestion → dashboard).
- AI request rate, error rate, timeouts.

---

## 9) Practical deployment checklist

- OT/IT network design approved (DMZ, firewall rules).
- TLS + broker ACLs configured.
- Topic naming and payload schema versioned.
- Time sync (NTP/PTP) across PLC/edge/backend.
- Safety policy defined:
  - what the backend is allowed to automate (if anything)
  - how emergency stop is validated and latched
- Run HIL/SIL tests before going live.

---

## 10) How this repo fits into “real life”

This repository is a useful stepping stone:
- **Simulink model** can act as the twin/plant.
- **MQTT** decouples simulation/control from analytics/UI.
- **FastAPI** provides a clean boundary for dashboards and external tools.
- **RAG/LLM** improves technician guidance, but should remain decision support unless you implement a formally verified safety layer.

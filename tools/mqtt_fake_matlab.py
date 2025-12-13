"""Fake MATLAB/Simulink publisher for local MQTT testing.

Publishes telemetry to:  digital_twin/{pump_id}/telemetry
Listens for commands on: digital_twin/{pump_id}/command

Run a local broker first (Mosquitto), then:
  C:/.../venv/Scripts/python.exe tools/mqtt_fake_matlab.py

Environment variables:
  MQTT_HOST (default: localhost)
  MQTT_PORT (default: 1883)
  MQTT_PUMP_ID (default: pump01)
  MQTT_BASE_TOPIC (default: digital_twin)
"""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict

import paho.mqtt.client as mqtt


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_imbalance_pct(a: float, b: float, c: float) -> float:
    avg = (a + b + c) / 3.0
    if avg == 0:
        return 0.0
    max_dev = max(abs(a - avg), abs(b - avg), abs(c - avg))
    return (max_dev / avg) * 100.0


class FakePump:
    def __init__(self):
        self.fault_state = "NORMAL"
        self.fault_start = None
        self.seq = 0

        self.nom_voltage = 230.0
        self.nom_current = 10.0
        self.nom_vibration = 1.5
        self.nom_pressure = 5.0
        self.nom_temp = 65.0

    def set_fault(self, fault: str):
        fault = fault.upper().strip()
        if fault == "NORMAL" or fault == "RESET":
            self.fault_state = "NORMAL"
            self.fault_start = None
            return
        self.fault_state = fault
        self.fault_start = time.time()

    def emergency_stop(self):
        # For demo: reset fault + return to nominal
        self.fault_state = "NORMAL"
        self.fault_start = None

    def reading(self) -> Dict[str, Any]:
        self.seq += 1
        dur = 0
        if self.fault_start is not None:
            dur = int(time.time() - self.fault_start)

        # Base signals
        voltage = self.nom_voltage * random.uniform(0.98, 1.02)
        vib = self.nom_vibration * random.uniform(0.8, 1.1)
        pressure = self.nom_pressure * random.uniform(0.95, 1.05)
        temp = self.nom_temp + random.uniform(-3, 3)

        a = self.nom_current * random.uniform(0.98, 1.02)
        b = self.nom_current * random.uniform(0.98, 1.02)
        c = self.nom_current * random.uniform(0.98, 1.02)

        # Fault behavior
        if self.fault_state == "WINDING_DEFECT":
            c *= 1.0 + min(0.05 + dur * 0.01, 0.25)
            temp = self.nom_temp + 15 + dur * 2
        elif self.fault_state == "SUPPLY_FAULT":
            voltage = random.uniform(190, 207)
        elif self.fault_state == "CAVITATION":
            vib = 5.0 + random.uniform(0, 3.0)
            if random.random() < 0.3:
                vib += random.uniform(2, 5)
            pressure = max(0.0, self.nom_pressure + random.uniform(-1.5, 0.5))
        elif self.fault_state == "BEARING_WEAR":
            vib = self.nom_vibration + 1.5 + dur * 0.1 + random.uniform(-0.3, 0.5)
            temp = self.nom_temp + 5 + random.uniform(0, 3)
        elif self.fault_state == "OVERLOAD":
            a *= random.uniform(1.15, 1.30)
            b *= random.uniform(1.15, 1.30)
            c *= random.uniform(1.15, 1.30)
            voltage = self.nom_voltage * random.uniform(0.95, 0.98)
            pressure = self.nom_pressure * random.uniform(1.1, 1.3)
            temp = self.nom_temp + 10 + random.uniform(0, 5)

        return {
            "pump_id": os.getenv("MQTT_PUMP_ID", "pump01"),
            "timestamp": utc_now_iso(),
            "seq": self.seq,
            "fault_state": self.fault_state,
            "fault_duration_s": dur,
            "amps_A": a,
            "amps_B": b,
            "amps_C": c,
            "imbalance_pct": compute_imbalance_pct(a, b, c),
            "voltage": voltage,
            "vibration": vib,
            "pressure": pressure,
            "temperature": temp,
        }


def main():
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    pump_id = os.getenv("MQTT_PUMP_ID", "pump01")
    base = os.getenv("MQTT_BASE_TOPIC", "digital_twin")

    telemetry_topic = f"{base}/{pump_id}/telemetry"
    command_topic = f"{base}/{pump_id}/command"

    pump = FakePump()

    def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            cmd = str(payload.get("command", "")).upper().strip()
            fault = str(payload.get("fault_type", "")).upper().strip()

            if cmd == "INJECT_FAULT" and fault:
                print(f"[CMD] INJECT_FAULT {fault}")
                pump.set_fault(fault)
            elif cmd == "RESET":
                print("[CMD] RESET")
                pump.set_fault("NORMAL")
            elif cmd == "EMERGENCY_STOP":
                print("[CMD] EMERGENCY_STOP")
                pump.emergency_stop()
        except Exception:
            return

    client = mqtt.Client(client_id=f"fake-matlab-{int(time.time())}")
    client.on_message = on_message

    client.connect(host, port, keepalive=30)
    client.subscribe(command_topic, qos=1)
    client.loop_start()

    print(f"Publishing telemetry to {telemetry_topic} @ 1 Hz")
    print(f"Listening for commands on {command_topic}")

    try:
        while True:
            payload = pump.reading()
            client.publish(telemetry_topic, json.dumps(payload), qos=0, retain=False)
            time.sleep(1.0)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

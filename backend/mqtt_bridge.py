"""MQTT bridge for separating the Digital Twin (simulation) from the backend.

- Subscribes to telemetry published by an external simulator (e.g., MATLAB/Simulink).
- Publishes command messages (fault injection, reset, emergency stop) back to the simulator.

This keeps the existing FastAPI/WebSocket contract unchanged while swapping the sensor source.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

import paho.mqtt.client as mqtt


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _compute_imbalance_pct(phase_a: float, phase_b: float, phase_c: float) -> float:
    avg = (phase_a + phase_b + phase_c) / 3.0
    if avg == 0:
        return 0.0
    max_dev = max(abs(phase_a - avg), abs(phase_b - avg), abs(phase_c - avg))
    return (max_dev / avg) * 100.0


def _normalize_fault_state(raw: Any) -> str:
    if not raw:
        return "Normal"
    text = str(raw).strip()
    # Accept both NORMAL and "Normal" and the simulator's human labels
    if text.upper() == "NORMAL":
        return "Normal"
    return text


def _normalize_telemetry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map external telemetry schema(s) into the backend's existing sensor schema."""

    # Accept both nested and flat schemas
    amps_obj = payload.get("amperage")
    if isinstance(amps_obj, dict):
        phase_a = _safe_float(amps_obj.get("phase_a"), 0.0)
        phase_b = _safe_float(amps_obj.get("phase_b"), 0.0)
        phase_c = _safe_float(amps_obj.get("phase_c"), 0.0)
        imbalance_pct = _safe_float(amps_obj.get("imbalance_pct"), None)
    else:
        phase_a = _safe_float(payload.get("amps_A", payload.get("phase_a")), 0.0)
        phase_b = _safe_float(payload.get("amps_B", payload.get("phase_b")), 0.0)
        phase_c = _safe_float(payload.get("amps_C", payload.get("phase_c")), 0.0)
        imbalance_pct = _safe_float(payload.get("imbalance_pct"), None)

    avg = (phase_a + phase_b + phase_c) / 3.0
    if imbalance_pct is None:
        imbalance_pct = _compute_imbalance_pct(phase_a, phase_b, phase_c)

    fault_state = _normalize_fault_state(payload.get("fault_state", payload.get("error_state")))

    normalized = {
        "timestamp": payload.get("timestamp") or _utc_now_iso(),
        "fault_state": fault_state,
        "fault_duration": payload.get("fault_duration", payload.get("fault_duration_s", 0)),
        "amperage": {
            "phase_a": phase_a,
            "phase_b": phase_b,
            "phase_c": phase_c,
            "average": avg,
            "imbalance_pct": imbalance_pct,
        },
        "voltage": _safe_float(payload.get("voltage"), 0.0),
        "vibration": _safe_float(payload.get("vibration"), 0.0),
        "pressure": _safe_float(payload.get("pressure"), 0.0),
        "temperature": _safe_float(payload.get("temperature"), 0.0),
    }

    # Preserve optional metadata if present
    if "pump_id" in payload:
        normalized["pump_id"] = payload["pump_id"]
    if "seq" in payload:
        normalized["seq"] = payload["seq"]

    return normalized


@dataclass
class MQTTConfig:
    host: str = "localhost"
    port: int = 1883
    pump_id: str = "pump01"
    base_topic: str = "digital_twin"
    username: Optional[str] = None
    password: Optional[str] = None
    telemetry_qos: int = 0
    command_qos: int = 1

    @property
    def telemetry_topic(self) -> str:
        return f"{self.base_topic}/{self.pump_id}/telemetry"

    @property
    def command_topic(self) -> str:
        return f"{self.base_topic}/{self.pump_id}/command"

    @property
    def status_topic(self) -> str:
        return f"{self.base_topic}/{self.pump_id}/status"


class MQTTBridge:
    """Background MQTT client that maintains the latest telemetry and a rolling history."""

    def __init__(self, config: MQTTConfig, max_history: int = 60):
        self.config = config
        self._lock = threading.Lock()
        self._latest: Optional[Dict[str, Any]] = None
        self._history: Deque[Dict[str, Any]] = deque(maxlen=max_history)
        self._connected = False
        self._last_message_ts: float = 0.0

        client_id = f"dt-backend-{int(time.time())}"
        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        if config.username:
            self._client.username_pw_set(config.username, config.password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def start(self) -> None:
        """Connect and start MQTT loop in a background thread."""
        # Non-blocking: connect_async + loop_start
        self._client.connect_async(self.config.host, self.config.port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        try:
            self._client.loop_stop()
        finally:
            try:
                self._client.disconnect()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return self._connected

    def seconds_since_last_message(self) -> Optional[float]:
        if self._last_message_ts <= 0:
            return None
        return time.time() - self._last_message_ts

    def latest(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return dict(self._latest) if self._latest else None

    def history(self) -> list[Dict[str, Any]]:
        with self._lock:
            return list(self._history)

    # ---- Publishing commands ----

    def publish_command(
        self,
        command: str,
        fault_type: Optional[str] = None,
        request_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "pump_id": self.config.pump_id,
            "request_id": request_id or f"req-{int(time.time()*1000)}",
            "timestamp": _utc_now_iso(),
            "command": command,
        }
        if fault_type is not None:
            payload["fault_type"] = fault_type

        if params:
            # Pass-through for simulator-specific knobs (e.g. temperature_target)
            payload.update(params)

        self._client.publish(
            self.config.command_topic,
            json.dumps(payload),
            qos=self.config.command_qos,
            retain=False,
        )

    # ---- MQTT callbacks ----

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int):
        self._connected = (rc == 0)
        if self._connected:
            client.subscribe(self.config.telemetry_topic, qos=self.config.telemetry_qos)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int):
        self._connected = False

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                return

            normalized = _normalize_telemetry(payload)
            with self._lock:
                self._latest = normalized
                self._history.append(normalized)
                self._last_message_ts = time.time()
        except Exception:
            # Keep bridge resilient: ignore malformed messages
            return


def load_mqtt_config_from_env() -> MQTTConfig:
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    pump_id = os.getenv("MQTT_PUMP_ID", "pump01")
    base_topic = os.getenv("MQTT_BASE_TOPIC", "digital_twin")
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")

    telemetry_qos = int(os.getenv("MQTT_TELEMETRY_QOS", "0"))
    command_qos = int(os.getenv("MQTT_COMMAND_QOS", "1"))

    return MQTTConfig(
        host=host,
        port=port,
        pump_id=pump_id,
        base_topic=base_topic,
        username=username,
        password=password,
        telemetry_qos=telemetry_qos,
        command_qos=command_qos,
    )

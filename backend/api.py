"""
FastAPI Backend for Digital Twin Dashboard
Real-time WebSocket API for sensor data streaming and AI diagnostics
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator import PumpSimulator, FaultType
from src.ai_agent import MaintenanceAIAgent
from backend.mqtt_bridge import MQTTBridge, load_mqtt_config_from_env

# Global instances
pump_simulator: Optional[PumpSimulator] = None
ai_agent: Optional[MaintenanceAIAgent] = None
mq_bridge: Optional[MQTTBridge] = None
active_connections: List[WebSocket] = []
sensor_history: List[Dict] = []
MAX_HISTORY = 60  # Keep last 60 seconds

# Session-only chat memory (in-memory). This keeps context within a single chat session
# without persisting anything to disk.
CHAT_MAX_TURNS = 20  # user+assistant messages (rolling window)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

# Basic guardrail: keep chat focused on pump maintenance topics.
# (A rules-based filter is simple, fast, and reliable for demos.)
MAINTENANCE_KEYWORDS = (
    # FR
    "pompe",
    "moteur",
    "maintenance",
    "diagnostic",
    "défaut",
    "defaut",
    "capteur",
    "tension",
    "courant",
    "déséquilibre",
    "desequilibre",
    "vibration",
    "température",
    "temperature",
    "pression",
    "cavitation",
    "roulement",
    "bobinage",
    "surcharge",
    "joint",
    "hélice",
    "helice",
    "turbine",
    "impeller",
    # EN
    "pump",
    "motor",
    "fault",
    "sensor",
    "voltage",
    "current",
    "imbalance",
    "bearing",
    "overload",
    "seal",
    # Project terms
    "mqtt",
    "simulink",
    "matlab",
)


def _is_maintenance_question(text: str) -> bool:
    msg = (text or "").strip().lower()
    if not msg:
        return False
    return any(k in msg for k in MAINTENANCE_KEYWORDS)


def _maintenance_refusal_message(text: str) -> str:
    msg = (text or "").strip().lower()
    english_markers = ("what", "how", "why", "please", "can you", "could you")
    is_english = any(m in msg for m in english_markers)
    if is_english:
        return (
            "I can only help with pump maintenance/diagnostics (sensors, faults, tests, actions). "
            "Please rephrase your question in that context."
        )
    return (
        "Je peux répondre uniquement aux questions liées à la maintenance/diagnostic de la pompe "
        "(capteurs, défauts, tests, actions). Reformule ta question dans ce cadre."
    )

# Fault start snapshot tracking (for questions like: "what were sensors at the beginning?")
MAX_FAULT_EVENTS = 20
_last_fault_state_seen: Optional[str] = None
fault_active_context: Optional[Dict[str, Any]] = None
fault_event_history: List[Dict[str, Any]] = []


def _normalize_fault_state(value: Any) -> str:
    s = str(value or "Normal").strip()
    # Some sources may use NORMAL; simulator uses "Normal"
    if s.upper() == "NORMAL":
        return "Normal"
    return s


def _parse_iso_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        s = str(value).strip()
        # Support trailing 'Z'
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _extract_fault_duration_seconds(reading: Dict[str, Any]) -> Optional[float]:
    for key in ("fault_duration", "fault_duration_s", "fault_duration_sec"):
        if key in reading:
            try:
                v = reading.get(key)
                if v is None:
                    continue
                return float(v)
            except Exception:
                continue
    return None


def _track_fault_context(reading: Dict[str, Any]) -> None:
    """Track fault transitions and store the first snapshot when a fault starts."""
    global _last_fault_state_seen, fault_active_context, fault_event_history

    current_fault = _normalize_fault_state(reading.get("fault_state", "Normal"))
    prev_fault = _normalize_fault_state(_last_fault_state_seen)

    # Initialize baseline
    if _last_fault_state_seen is None:
        _last_fault_state_seen = current_fault
        if current_fault == "Normal":
            fault_active_context = None
        else:
            # First observation is already a fault
            prev_fault = "Normal"

    # Only act on transitions
    if current_fault != prev_fault:
        now_iso = datetime.now().astimezone().isoformat()

        if current_fault == "Normal":
            fault_active_context = None
        else:
            ts = reading.get("timestamp")
            ts_dt = _parse_iso_timestamp(ts)
            dur_s = _extract_fault_duration_seconds(reading)
            estimated_start_iso = None
            if ts_dt and dur_s is not None:
                try:
                    estimated_start_iso = (ts_dt - timedelta(seconds=dur_s)).isoformat()
                except Exception:
                    estimated_start_iso = None

            event = {
                "fault_state": current_fault,
                "fault_start_seen_at": now_iso,
                "fault_start_estimated_at": estimated_start_iso,
                "fault_start_snapshot": reading,
            }
            fault_active_context = event
            fault_event_history.append(event)
            if len(fault_event_history) > MAX_FAULT_EVENTS:
                fault_event_history = fault_event_history[-MAX_FAULT_EVENTS:]

    _last_fault_state_seen = current_fault


def _get_fault_context_for_prompt() -> Optional[Dict[str, Any]]:
    # Only send the active fault context to the LLM (keeps prompt small)
    if not fault_active_context:
        return None
    return {
        "fault_state": fault_active_context.get("fault_state"),
        "fault_start_seen_at": fault_active_context.get("fault_start_seen_at"),
        "fault_start_estimated_at": fault_active_context.get("fault_start_estimated_at"),
        "fault_start_snapshot": fault_active_context.get("fault_start_snapshot"),
    }


def _get_sensor_source() -> str:
    """Select sensor source: 'simulator' (default) or 'mqtt'."""
    return os.getenv("SENSOR_SOURCE", "simulator").strip().lower()


def _get_latest_sensor_reading() -> Optional[Dict]:
    source = _get_sensor_source()
    if source == "mqtt" and mq_bridge:
        reading = mq_bridge.latest()
        if reading:
            _track_fault_context(reading)
        return reading
    if pump_simulator:
        reading = pump_simulator.get_sensor_reading()
        if reading:
            _track_fault_context(reading)
        return reading
    return None


# Pydantic models for API
class FaultRequest(BaseModel):
    fault_type: str
    # Optional: allow UI/API to request a specific target band for the external simulator
    temperature_target: Optional[float] = None
    temperature_band: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    include_sensor_context: bool = True
    # Session identifier generated by the frontend (stored in localStorage).
    # Used to keep a short rolling chat history for context.
    session_id: Optional[str] = None

class MemoryAddRequest(BaseModel):
    text: str
    tag: Optional[str] = None
    source: Optional[str] = None

class MemorySearchResponse(BaseModel):
    results: List[Dict[str, Any]]

class DiagnosticRequest(BaseModel):
    sensor_data: Dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    global pump_simulator, ai_agent, mq_bridge
    
    print("\n" + "="*60)
    print("🚀 Starting Digital Twin Backend Server")
    print("="*60 + "\n")
    
    # Initialize simulator (kept for fallback and local-only mode)
    pump_simulator = PumpSimulator()

    # Initialize MQTT bridge if enabled
    if _get_sensor_source() == "mqtt":
        try:
            mq_bridge = MQTTBridge(load_mqtt_config_from_env(), max_history=MAX_HISTORY)
            mq_bridge.start()
            print("📡 MQTT sensor source enabled")
        except Exception as e:
            mq_bridge = None
            print(f"⚠️ MQTT bridge initialization failed: {e}")
            print("   Falling back to simulator sensor source")
    
    # Initialize AI agent (may take a few seconds for embeddings)
    try:
        ai_agent = MaintenanceAIAgent()
    except Exception as e:
        print(f"⚠️ AI Agent initialization failed: {e}")
        print("   Chat and diagnostics will be unavailable")
        ai_agent = None
    
    print("\n✅ Backend ready! Waiting for connections...\n")
    
    yield
    
    # Cleanup
    print("\n🛑 Shutting down Digital Twin Backend...")
    if mq_bridge:
        try:
            mq_bridge.stop()
        except Exception:
            pass


# Create FastAPI app
app = FastAPI(
    title="Digital Twin API",
    description="Real-time IoT Digital Twin for Grundfos CR Pump Predictive Maintenance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REST API Endpoints
# =====================================================

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "service": "Digital Twin API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/sensor-data")
async def get_sensor_data():
    """Get current sensor readings"""
    reading = _get_latest_sensor_reading()
    if reading is None:
        raise HTTPException(status_code=503, detail="Sensor source not available")
    return reading


@app.get("/api/sensor-history")
async def get_sensor_history():
    """Get historical sensor data (last 60 readings)"""
    if _get_sensor_source() == "mqtt" and mq_bridge:
        return {"history": mq_bridge.history()}
    return {"history": sensor_history}


@app.post("/api/inject-fault")
async def inject_fault(request: FaultRequest):
    """Inject a fault condition into the simulator"""
    # In MQTT mode, publish a command to the external simulator.
    if _get_sensor_source() == "mqtt":
        if mq_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT bridge not initialized")
        fault_id = request.fault_type.upper().strip()
        if fault_id == "NORMAL":
            mq_bridge.publish_command("RESET")
        else:
            params: Dict[str, Any] = {}
            if request.temperature_target is not None:
                params["temperature_target"] = float(request.temperature_target)
            if request.temperature_band is not None:
                params["temperature_band"] = float(request.temperature_band)
            mq_bridge.publish_command("INJECT_FAULT", fault_type=fault_id, params=params or None)
        return {"status": "success", "message": f"Command sent via MQTT: {fault_id}"}

    # Simulator mode
    if pump_simulator is None:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    fault_mapping = {
        "NORMAL": FaultType.NORMAL,
        "WINDING_DEFECT": FaultType.WINDING_DEFECT,
        "SUPPLY_FAULT": FaultType.SUPPLY_FAULT,
        "CAVITATION": FaultType.CAVITATION,
        "BEARING_WEAR": FaultType.BEARING_WEAR,
        "OVERLOAD": FaultType.OVERLOAD,
    }
    
    fault_type = fault_mapping.get(request.fault_type.upper())
    if fault_type is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid fault type. Valid options: {list(fault_mapping.keys())}"
        )
    
    if fault_type == FaultType.NORMAL:
        pump_simulator.reset_fault()
        return {"status": "success", "message": "System reset to normal operation"}
    else:
        pump_simulator.inject_fault(fault_type)
        return {"status": "success", "message": f"Fault injected: {fault_type.value}"}


@app.post("/api/emergency-stop")
async def emergency_stop():
    """
    Emergency stop - immediately reset pump to normal operation.
    Called automatically when critical conditions are detected.
    """
    if _get_sensor_source() == "mqtt" and mq_bridge:
        mq_bridge.publish_command("EMERGENCY_STOP")

    if pump_simulator is None:
        raise HTTPException(status_code=503, detail="Pump simulator not initialized")

    # Keep local simulator safe as well
    pump_simulator.reset_fault()
    return {
        "status": "success",
        "message": "🛑 EMERGENCY STOP EXECUTED - Pump reset to safe state",
        "action": "PUMP_STOPPED"
    }


@app.post("/api/diagnose")
async def get_diagnosis(request: DiagnosticRequest):
    """Get AI diagnostic for current sensor data including shutdown decision"""
    if ai_agent is None:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    try:
        result = ai_agent.get_diagnostic(request.sensor_data)
        
        # Extract shutdown decision
        shutdown = result.get("shutdown_decision", {})
        
        return {
            "diagnosis": result["diagnosis"],
            "fault_detected": result["fault_detected"],
            "shutdown_decision": {
                "action": shutdown.get("action", "NORMAL_OPERATION"),
                "urgency": shutdown.get("urgency", "OK"),
                "icon": shutdown.get("icon", "✅"),
                "message": shutdown.get("message", ""),
                "message_en": shutdown.get("message_en", ""),
                "recommendation": shutdown.get("recommendation", ""),
                "recommendation_en": shutdown.get("recommendation_en", ""),
                "critical_conditions": shutdown.get("critical_conditions", []),
                "warning_conditions": shutdown.get("warning_conditions", [])
            },
            "references": [
                {"page": c["page"], "score": c["score"]} 
                for c in result["context_used"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with AI maintenance assistant"""
    if ai_agent is None:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    try:
        sensor_data = None
        if request.include_sensor_context:
            sensor_data = _get_latest_sensor_reading()

        fault_context = _get_fault_context_for_prompt() if request.include_sensor_context else None

        msg = (request.message or "").strip()

        # Guardrail: refuse non-maintenance questions before calling the LLM.
        if not _is_maintenance_question(msg):
            return {
                "response": _maintenance_refusal_message(msg),
                "timestamp": datetime.now().isoformat(),
            }

        # Session-only memory: keep a rolling window of chat messages.
        sid = (request.session_id or "default").strip() or "default"
        history = chat_sessions.get(sid, [])
        history.append({"role": "user", "content": msg})
        # Trim to last N messages
        if len(history) > CHAT_MAX_TURNS:
            history = history[-CHAT_MAX_TURNS:]

        response = ai_agent.ask_question(msg, sensor_data, fault_context=fault_context, chat_history=history)

        history.append({"role": "assistant", "content": response})
        if len(history) > CHAT_MAX_TURNS:
            history = history[-CHAT_MAX_TURNS:]
        chat_sessions[sid] = history

        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fault-types")
async def get_fault_types():
    """Get list of available fault types"""
    return {
        "fault_types": [
            {"id": "NORMAL", "name": "Normal Operation", "icon": "✅"},
            {"id": "WINDING_DEFECT", "name": "Winding Defect", "icon": "⚡"},
            {"id": "SUPPLY_FAULT", "name": "Supply Fault", "icon": "🔌"},
            {"id": "CAVITATION", "name": "Cavitation", "icon": "💧"},
            {"id": "BEARING_WEAR", "name": "Bearing Wear", "icon": "⚙️"},
            {"id": "OVERLOAD", "name": "Overload", "icon": "🔥"},
        ]
    }


@app.get("/api/fault-context")
async def get_fault_context():
    """Expose the last fault-start snapshot for debugging / UI use."""
    return {
        "active": _get_fault_context_for_prompt(),
        "history": fault_event_history[-5:],
    }


# =====================================================
# WebSocket for Real-Time Streaming
# =====================================================

@app.websocket("/ws/sensor-stream")
async def websocket_sensor_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data streaming.
    Sends sensor readings every second.
    """
    await websocket.accept()
    active_connections.append(websocket)
    print(f"📡 Client connected. Total connections: {len(active_connections)}")
    
    try:
        while True:
            reading = _get_latest_sensor_reading()
            if reading:
                # Add to history (simulator mode only; MQTT keeps its own)
                if _get_sensor_source() != "mqtt":
                    sensor_history.append(reading)
                    if len(sensor_history) > MAX_HISTORY:
                        sensor_history.pop(0)

                await websocket.send_json({
                    "type": "sensor_update",
                    "data": reading,
                    "history_length": len(sensor_history) if _get_sensor_source() != "mqtt" else (len(mq_bridge.history()) if mq_bridge else 0)
                })
            
            await asyncio.sleep(1)  # 1 Hz update rate
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"📴 Client disconnected. Total connections: {len(active_connections)}")


@app.websocket("/ws/diagnostic-stream")
async def websocket_diagnostic_stream(websocket: WebSocket):
    """
    WebSocket for auto-diagnostic updates.
    Triggers when fault state changes.
    """
    await websocket.accept()
    last_fault_state = "Normal"
    
    try:
        while True:
            reading = _get_latest_sensor_reading()
            if reading:
                current_fault = reading.get("fault_state", "Normal")
                
                # Check if fault state changed
                if current_fault != last_fault_state and current_fault != "Normal":
                    # Fault detected - trigger diagnosis
                    await websocket.send_json({
                        "type": "fault_detected",
                        "fault_state": current_fault,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Get AI diagnosis if available
                    if ai_agent:
                        try:
                            result = ai_agent.get_diagnostic(reading)
                            await websocket.send_json({
                                "type": "diagnosis_ready",
                                "diagnosis": result["diagnosis"],
                                "references": [
                                    {"page": c["page"], "score": c["score"]}
                                    for c in result["context_used"]
                                ]
                            })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "diagnosis_error",
                                "error": str(e)
                            })
                
                elif current_fault == "Normal" and last_fault_state != "Normal":
                    # Fault cleared
                    await websocket.send_json({
                        "type": "fault_cleared",
                        "timestamp": datetime.now().isoformat()
                    })
                
                last_fault_state = current_fault
            
            await asyncio.sleep(0.5)  # Check every 500ms
            
    except WebSocketDisconnect:
        print("📴 Diagnostic stream disconnected")


# =====================================================
# Serve Frontend (Production)
# =====================================================

# Check if frontend build exists
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes"""
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404)
        
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404)


# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "🏭"*30)
    print("  DIGITAL TWIN BACKEND SERVER")
    print("🏭"*30 + "\n")
    
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

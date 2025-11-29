"""
FastAPI Backend for Digital Twin Dashboard
Real-time WebSocket API for sensor data streaming and AI diagnostics
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
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

# Global instances
pump_simulator: Optional[PumpSimulator] = None
ai_agent: Optional[MaintenanceAIAgent] = None
active_connections: List[WebSocket] = []
sensor_history: List[Dict] = []
MAX_HISTORY = 60  # Keep last 60 seconds


# Pydantic models for API
class FaultRequest(BaseModel):
    fault_type: str

class ChatRequest(BaseModel):
    message: str
    include_sensor_context: bool = True

class DiagnosticRequest(BaseModel):
    sensor_data: Dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    global pump_simulator, ai_agent
    
    print("\n" + "="*60)
    print("🚀 Starting Digital Twin Backend Server")
    print("="*60 + "\n")
    
    # Initialize simulator
    pump_simulator = PumpSimulator()
    
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
    if pump_simulator is None:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    reading = pump_simulator.get_sensor_reading()
    return reading


@app.get("/api/sensor-history")
async def get_sensor_history():
    """Get historical sensor data (last 60 readings)"""
    return {"history": sensor_history}


@app.post("/api/inject-fault")
async def inject_fault(request: FaultRequest):
    """Inject a fault condition into the simulator"""
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


@app.post("/api/diagnose")
async def get_diagnosis(request: DiagnosticRequest):
    """Get AI diagnostic for current sensor data"""
    if ai_agent is None:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    try:
        result = ai_agent.get_diagnostic(request.sensor_data)
        return {
            "diagnosis": result["diagnosis"],
            "fault_detected": result["fault_detected"],
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
        if request.include_sensor_context and pump_simulator:
            sensor_data = pump_simulator.get_sensor_reading()
        
        response = ai_agent.ask_question(request.message, sensor_data)
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
            if pump_simulator:
                # Get current reading
                reading = pump_simulator.get_sensor_reading()
                
                # Add to history
                sensor_history.append(reading)
                if len(sensor_history) > MAX_HISTORY:
                    sensor_history.pop(0)
                
                # Send to client
                await websocket.send_json({
                    "type": "sensor_update",
                    "data": reading,
                    "history_length": len(sensor_history)
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
            if pump_simulator:
                reading = pump_simulator.get_sensor_reading()
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

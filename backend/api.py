"""
FastAPI Backend for Digital Twin Dashboard
Real-time WebSocket API for sensor data streaming and AI diagnostics

Supports dual data sources:
- Python simulation (PumpSimulator)
- MATLAB/Simulink via TCP (MATLABBridge)
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Union
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator import PumpSimulator, FaultType
from src.ai_agent import MaintenanceAIAgent
from src.matlab_bridge import MATLABBridge, HybridSimulator, MATLABBridgeConfig
from src.config import get_config, DataSource, DigitalTwinConfig
from backend.fault_scenarios import (
    FAULT_SCENARIOS, StateTransitionManager, 
    get_scenarios_for_ui, get_scenario_details,
    get_fault_progression, get_full_progression_chain
)

# Global instances
pump_simulator: Optional[Union[PumpSimulator, HybridSimulator]] = None
matlab_bridge: Optional[MATLABBridge] = None
ai_agent: Optional[MaintenanceAIAgent] = None
active_connections: List[WebSocket] = []
sensor_history: List[Dict] = []
MAX_HISTORY = 60  # Keep last 60 seconds
current_data_source: DataSource = DataSource.PYTHON
state_manager: StateTransitionManager = StateTransitionManager()  # New state manager


# Pydantic models for API
class FaultRequest(BaseModel):
    fault_type: str

class ChatRequest(BaseModel):
    message: str
    include_sensor_context: bool = True

class DiagnosticRequest(BaseModel):
    sensor_data: Dict

class DataSourceRequest(BaseModel):
    source: str  # 'python' or 'matlab'


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    global pump_simulator, matlab_bridge, ai_agent, current_data_source
    
    print("\n" + "="*60)
    print("🚀 Starting Digital Twin Backend Server")
    print("="*60 + "\n")
    
    # Load configuration
    config = get_config()
    current_data_source = config.data_source
    
    print(f"📊 Data Source: {current_data_source.value.upper()}")
    
    # Initialize based on data source
    if current_data_source == DataSource.MATLAB:
        # Initialize MATLAB bridge directly (not through HybridSimulator to avoid double binding)
        print("🌉 Initializing MATLAB Bridge...")
        matlab_config = MATLABBridgeConfig(
            host=config.tcp.host,
            port=config.tcp.port
        )
        matlab_bridge = MATLABBridge(matlab_config)
        
        if matlab_bridge.start_server():
            # Use bridge directly as pump_simulator (same interface)
            pump_simulator = matlab_bridge
            print("✅ MATLAB Bridge ready - waiting for MATLAB connection on port 5555")
        else:
            print("⚠️  MATLAB Bridge failed, falling back to Python simulator")
            pump_simulator = PumpSimulator()
            current_data_source = DataSource.PYTHON
    else:
        # Initialize Python simulator
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
    
    if matlab_bridge:
        matlab_bridge.stop_server()


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
        "data_source": current_data_source.value,
        "matlab_connected": matlab_bridge.is_connected() if matlab_bridge else False,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status")
async def get_status():
    """Get detailed system status"""
    status = {
        "data_source": current_data_source.value,
        "simulator_active": pump_simulator is not None,
        "ai_agent_active": ai_agent is not None,
        "active_connections": len(active_connections),
        "history_length": len(sensor_history),
    }
    
    if matlab_bridge:
        status["matlab"] = matlab_bridge.get_status()
    
    return status


@app.post("/api/switch-source")
async def switch_data_source(request: DataSourceRequest):
    """Switch between Python and MATLAB data sources"""
    global pump_simulator, matlab_bridge, current_data_source
    
    new_source = request.source.lower()
    
    if new_source not in ['python', 'matlab']:
        raise HTTPException(
            status_code=400,
            detail="Invalid source. Use 'python' or 'matlab'"
        )
    
    if new_source == current_data_source.value:
        return {"status": "unchanged", "source": current_data_source.value}
    
    try:
        if new_source == 'matlab':
            # Switch to MATLAB
            if not matlab_bridge:
                config = get_config()
                matlab_config = MATLABBridgeConfig(
                    host=config.tcp.host,
                    port=config.tcp.port
                )
                matlab_bridge = MATLABBridge(matlab_config)
            
            if matlab_bridge.start_server():
                pump_simulator = HybridSimulator(source='matlab')
                pump_simulator.start()
                current_data_source = DataSource.MATLAB
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Failed to start MATLAB bridge"
                )
        else:
            # Switch to Python
            if matlab_bridge:
                matlab_bridge.stop_server()
            
            pump_simulator = PumpSimulator()
            current_data_source = DataSource.PYTHON
        
        return {
            "status": "switched",
            "source": current_data_source.value,
            "message": f"Now using {current_data_source.value.upper()} data source"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    """
    Inject a fault condition with state transition logic.
    
    Transition rules:
    - From NORMAL: Can go to any state
    - From LOW/MEDIUM/HIGH: Can go to NORMAL (repair) or higher severity
    - From CRITICAL: Can ONLY go to NORMAL (repair required)
    """
    global state_manager
    
    if pump_simulator is None:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    
    target_state = request.fault_type.upper()
    
    # Check if transition is allowed
    can_go, reason = state_manager.can_transition_to(target_state)
    
    if not can_go:
        # Return a user-friendly error with current state info
        current = state_manager.get_current_scenario()
        return {
            "status": "blocked",
            "success": False,
            "message": reason,
            "current_state": {
                "id": current.id,
                "display_name": current.display_name,
                "severity": current.severity.value,
                "severity_name": current.severity.name,
            },
            "allowed_transitions": state_manager.get_allowed_transitions(),
            "hint": "💡 Cliquez sur 'Fonctionnement Normal' pour réparer/réinitialiser la pompe avant de simuler un autre défaut."
        }
    
    # Perform the transition
    success, message, scenario = state_manager.transition_to(target_state)
    
    if success:
        # Map to old FaultType enum for backward compatibility with simulator
        fault_mapping = {
            "NORMAL": FaultType.NORMAL,
            "WINDING_DEFECT": FaultType.WINDING_DEFECT,
            "SUPPLY_FAULT": FaultType.SUPPLY_FAULT,
            "CAVITATION": FaultType.CAVITATION,
            "BEARING_WEAR": FaultType.BEARING_WEAR,
            "OVERLOAD": FaultType.OVERLOAD,
            # New states map to closest existing FaultType
            "FILTER_CLOGGING": FaultType.CAVITATION,  # Similar hydraulic effect
            "MINOR_VIBRATION": FaultType.BEARING_WEAR,  # Mechanical
            "IMPELLER_WEAR": FaultType.CAVITATION,  # Hydraulic
            "SEAL_LEAK": FaultType.BEARING_WEAR,  # Mechanical
            "PUMP_SEIZURE": FaultType.OVERLOAD,  # Critical
        }
        
        fault_type = fault_mapping.get(target_state, FaultType.NORMAL)
        
        if fault_type == FaultType.NORMAL:
            pump_simulator.reset_fault()
        else:
            pump_simulator.inject_fault(fault_type)
        
        return {
            "status": "success",
            "success": True,
            "message": message,
            "scenario": {
                "id": scenario.id,
                "display_name": scenario.display_name,
                "icon": scenario.icon,
                "severity": scenario.severity.value,
                "severity_name": scenario.severity.name,
                "description": scenario.description,
                "symptoms": scenario.symptoms,
                "causes": scenario.causes,
                "repair_action": scenario.repair_action,
                "maintenance_time": scenario.maintenance_time,
            },
            "current_state": target_state,
            "is_repair": target_state == "NORMAL",
        }
    else:
        return {
            "status": "error",
            "success": False,
            "message": message
        }


@app.post("/api/emergency-stop")
async def emergency_stop():
    """
    Emergency stop - immediately reset pump to normal operation.
    Called automatically when critical conditions are detected.
    """
    if pump_simulator is None:
        raise HTTPException(status_code=503, detail="Pump simulator not initialized")
    
    pump_simulator.reset_fault()
    return {
        "status": "success",
        "message": "🛑 EMERGENCY STOP EXECUTED - Pump reset to safe state",
        "action": "PUMP_STOPPED"
    }


@app.get("/api/fault-progression/{scenario_id}")
async def get_progression(scenario_id: str):
    """
    Get predictive fault progression for a scenario.
    
    Returns what faults can develop from the current fault if not fixed,
    sorted by probability (highest first). Based on Grundfos manual causality chains.
    
    Example: FILTER_CLOGGING can progress to:
    - CAVITATION (65% likely) - within 2-4 hours
    - IMPELLER_WEAR (25% likely) - within 1-2 weeks
    - OVERLOAD (10% likely) - within 4-8 hours
    """
    progressions = get_fault_progression(scenario_id)
    
    if not progressions:
        return {
            "scenario_id": scenario_id,
            "progressions": [],
            "message": "No further progression - this is either a terminal state or normal operation"
        }
    
    return {
        "scenario_id": scenario_id,
        "progressions": progressions,
        "total_paths": len(progressions)
    }


@app.get("/api/fault-tree/{scenario_id}")
async def get_progression_tree(scenario_id: str, depth: int = 3):
    """
    Get the full fault progression tree from a scenario.
    
    Shows all possible paths to failure if the current fault is not addressed.
    Useful for visualizing the complete risk chain in UML-style diagram.
    
    Args:
        scenario_id: Starting fault ID
        depth: How many levels deep to explore (default 3)
    """
    from backend.fault_scenarios import FAULT_SCENARIOS, get_fault_progression
    
    scenario = FAULT_SCENARIOS.get(scenario_id)
    if not scenario:
        return {
            "error": f"Unknown scenario: {scenario_id}"
        }
    
    # Get direct progressions
    progressions = get_fault_progression(scenario_id)
    
    # Build flat paths for UML-style display
    paths = []
    for prog in progressions:
        paths.append({
            "fault": prog["target_fault"],
            "name": prog["target_name"],
            "icon": prog.get("target_icon", "⚠️"),
            "probability": prog["probability"],
            "severity": prog["target_severity"],
            "time_to_progress": prog["time_to_progress"],
            "trigger_conditions": prog["trigger_conditions"],
            "prevention_action": prog.get("prevention_action", "Monitor and address root cause")
        })
    
    return {
        "root_fault": scenario_id,
        "root_name": scenario.display_name,
        "root_icon": scenario.icon,
        "root_severity": scenario.severity.value,
        "root_description": scenario.description,
        "paths": sorted(paths, key=lambda x: x["probability"], reverse=True),
        "repair_action": scenario.repair_action,
        "maintenance_time": scenario.maintenance_time
    }


@app.get("/api/manual-guide/{scenario_id}")
async def get_manual_guide(scenario_id: str):
    """
    Get troubleshooting guide data by QUERYING the Grundfos manual via RAG.
    
    This actually searches the PDF manual and returns relevant information.
    NO pre-defined data, everything comes from the manual.
    """
    from backend.fault_scenarios import FAULT_SCENARIOS
    
    scenario = FAULT_SCENARIOS.get(scenario_id)
    if not scenario:
        return None
    
    # Use RAG to query the manual for this specific fault
    if ai_agent is None or ai_agent.rag_engine is None:
        return {
            "id": scenario.id,
            "name": scenario.display_name,
            "icon": scenario.icon,
            "severity": scenario.severity.value,
            "description": scenario.description,
            "error": "RAG engine not available",
            "symptoms": [],
            "causes": [],
            "corrective_actions": [],
            "manual_references": []
        }
    
    # Build query for RAG based on fault type
    fault_name = scenario.name.lower()
    rag_query = f"{fault_name} symptoms causes troubleshooting corrective actions"
    
    # Query the knowledge base (the actual Grundfos PDF)
    retrieved_chunks = ai_agent.rag_engine.query_knowledge_base(
        query=rag_query,
        top_k=5
    )
    
    # Extract the raw text from manual
    # Chunks are dicts with keys: 'content', 'page', 'source', 'score'
    manual_content = []
    manual_references = []
    for chunk in retrieved_chunks:
        # Handle both dict format and Document object format
        if isinstance(chunk, dict):
            content = chunk.get('content', '')
            page = chunk.get('page', '')
            source = chunk.get('source', '')
        else:
            content = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
            page = chunk.metadata.get('page', '') if hasattr(chunk, 'metadata') else ''
            source = chunk.metadata.get('source', '') if hasattr(chunk, 'metadata') else ''
        
        manual_content.append(content)
        if page or source:
            ref = f"Page {page}" if page else source
            if ref not in manual_references:
                manual_references.append(ref)
    
    # Combine all retrieved content
    combined_content = "\n\n".join(manual_content)
    
    return {
        "id": scenario.id,
        "name": scenario.display_name,
        "icon": scenario.icon,
        "severity": scenario.severity.value,
        "description": f"Information retrieved from Grundfos manual for: {scenario.name}",
        "manual_content": combined_content,
        "manual_references": manual_references,
        "query_used": rag_query
    }


@app.post("/api/diagnose")
async def get_diagnosis(request: DiagnosticRequest):
    """Get AI diagnostic for current sensor data including shutdown decision, detected scenario, and fault progressions"""
    if ai_agent is None:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    try:
        result = ai_agent.get_diagnostic(request.sensor_data)
        
        # Extract shutdown decision
        shutdown = result.get("shutdown_decision", {})
        
        # Extract detected scenario
        detected = result.get("detected_scenario", {})
        
        # Extract fault progressions (predictive analysis)
        progressions = result.get("fault_progressions", [])
        
        return {
            "diagnosis": result["diagnosis"],
            "fault_detected": result["fault_detected"],
            "detected_scenario": {
                "id": detected.get("id", "UNKNOWN"),
                "confidence": detected.get("confidence", 0),
                "info": detected.get("info", {})
            },
            "fault_progressions": progressions,  # NEW: What can go wrong next
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
            "sensor_summary": result.get("sensor_summary", {}),
            "references": [
                {"page": c["page"], "score": c["score"]} 
                for c in result["context_used"]
            ]
        }
    except Exception as e:
        error_str = str(e)
        # Check for API quota errors (429)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            raise HTTPException(
                status_code=429, 
                detail="API quota exhausted. Please wait a few minutes before retrying."
            )
        raise HTTPException(status_code=500, detail=error_str)


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
    """Get list of available fault scenarios with state transition info"""
    current = state_manager.get_current_scenario()
    allowed = state_manager.get_allowed_transitions()
    
    return {
        "current_state": {
            "id": current.id,
            "display_name": current.display_name,
            "severity": current.severity.value,
            "severity_name": current.severity.name,
        },
        "allowed_transitions": allowed,
        "scenarios": get_scenarios_for_ui(),
        # Legacy format for backward compatibility
        "fault_types": [
            {
                "id": s.id, 
                "name": s.display_name, 
                "icon": s.icon,
                "severity": s.severity.value,
                "can_select": s.id in allowed,
            }
            for s in FAULT_SCENARIOS.values()
        ]
    }


@app.get("/api/scenario/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get detailed information about a specific fault scenario"""
    details = get_scenario_details(scenario_id.upper())
    if not details:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    
    # Add transition info
    can_go, reason = state_manager.can_transition_to(scenario_id.upper())
    details["can_activate"] = can_go
    details["transition_message"] = reason
    
    return details


@app.get("/api/current-state")
async def get_current_state():
    """Get current fault state and available transitions"""
    current = state_manager.get_current_scenario()
    return {
        "current": {
            "id": current.id,
            "display_name": current.display_name,
            "icon": current.icon,
            "severity": current.severity.value,
            "severity_name": current.severity.name,
            "description": current.description,
            "symptoms": current.symptoms,
            "repair_action": current.repair_action,
        },
        "allowed_transitions": state_manager.get_allowed_transitions(),
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
                
                # Add MATLAB connection status
                matlab_status = False
                if matlab_bridge and hasattr(matlab_bridge, 'is_connected'):
                    matlab_status = matlab_bridge.is_connected()
                elif matlab_bridge and hasattr(matlab_bridge, 'state'):
                    from src.matlab_bridge import ConnectionState
                    matlab_status = matlab_bridge.state == ConnectionState.CONNECTED
                
                # Add to history
                sensor_history.append(reading)
                if len(sensor_history) > MAX_HISTORY:
                    sensor_history.pop(0)
                
                # Get current scenario from state manager
                current_scenario = state_manager.get_current_scenario()
                
                # Send to client with connection info AND current scenario state
                await websocket.send_json({
                    "type": "sensor_update",
                    "data": reading,
                    "history_length": len(sensor_history),
                    "data_source": current_data_source.value,
                    "matlab_connected": matlab_status,
                    # Add scenario state for frontend sync
                    "scenario_state": {
                        "id": current_scenario.id,
                        "display_name": current_scenario.display_name,
                        "icon": current_scenario.icon,
                        "severity": current_scenario.severity.value,
                        "severity_name": current_scenario.severity.name,
                    }
                })
            
            await asyncio.sleep(1)  # 1 Hz update rate
            
    except WebSocketDisconnect:
        if websocket in active_connections:
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

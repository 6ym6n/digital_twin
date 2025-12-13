"""
AI Agent for Predictive Maintenance Diagnostics
Integrates Google Gemini with RAG for intelligent fault analysis

Synchronized with fault_scenarios.py for consistent fault detection
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_engine import RAGEngine

# Import fault scenarios for synchronized detection
try:
    from backend.fault_scenarios import FAULT_SCENARIOS, Severity, get_fault_progression
    SCENARIOS_AVAILABLE = True
except ImportError:
    SCENARIOS_AVAILABLE = False
    print("⚠️  fault_scenarios.py not found - using basic detection")
    def get_fault_progression(x): return []

# Load environment variables
load_dotenv()


class MaintenanceAIAgent:
    """
    AI-powered diagnostic agent for pump troubleshooting.
    Combines real-time sensor data with RAG-retrieved documentation.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 1000000
    ):
        """
        Initialize the AI agent with Gemini LLM and RAG engine.
        
        Args:
            model_name: Gemini model to use (default: gemini-2.5-flash for low latency)
            temperature: Creativity vs consistency (0.0-1.0, lower = more focused)
            max_tokens: Maximum response length
        """
        # Verify API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")
        
        # Initialize Gemini LLM
        print("🤖 Initializing Google Gemini AI Agent...")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            convert_system_message_to_human=True  # Gemini compatibility
        )
        
        # Initialize RAG engine
        print("📚 Connecting to knowledge base...")
        self.rag_engine = RAGEngine()
        
        # System prompt for maintenance engineer persona
        self.system_prompt = self._create_system_prompt()
        
        print("✅ AI Agent initialized successfully!")
        print(f"   Model: {model_name}")
        print(f"   Temperature: {temperature}")
        print(f"   Max Tokens: {max_tokens}\n")
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines AI behavior.
        
        Returns:
            System prompt string
        """
        return """You are a Senior Maintenance Engineer specialized in Grundfos CR centrifugal pumps with 15+ years of experience in industrial diagnostics.

Your responsibilities:
1. Analyze sensor data to identify root causes of pump failures
2. Provide actionable diagnostic steps based on manufacturer documentation
3. Recommend specific tools, measurements, and corrective actions
4. Prioritize safety and equipment protection
5. Keep explanations concise for real-time dashboard display

Communication style:
- Use technical terminology but remain clear
- Structure responses: DIAGNOSIS → ROOT CAUSE → ACTION ITEMS
- Reference specific manual pages when applicable
- If unsure, recommend additional measurements rather than guessing
- For emergencies (extreme values), recommend immediate shutdown

Context awareness:
- You receive real-time sensor readings (amperage, voltage, vibration, etc.)
- You have access to the Grundfos CR pump troubleshooting manual via RAG
- Historical fault patterns help identify progressive failures
"""
    
    # =========================================================================
    # SCENARIO DETECTION - Synchronized with fault_scenarios.py
    # =========================================================================
    
    # Sensor thresholds for each fault scenario
    # These MUST match the sensor_effects defined in fault_scenarios.py
    # Priority order matters: more specific/severe scenarios checked first
    SCENARIO_THRESHOLDS = {
        # Normal operation baseline (400V 3-phase system)
        "NORMAL": {
            "vibration_max": 2.5,
            "temp_max": 70,
            "current_max": 12,
            "imbalance_max": 3,
            "voltage_min": 380,
            "voltage_max": 420,
            "pressure_min": 4,
            "flow_min": 13
        },
        
        # Level 1 - LOW severity
        "FILTER_CLOGGING": {
            "vibration_range": (1.5, 3.5),
            "pressure_range": (3.5, 4.5),
            "flow_range": (12, 14),
            "temp_range": (60, 72),
            "priority": 1,
            "description": "Clogged inlet filter",
            "rag_query": "filter clogging inlet strainer flow reduction maintenance"
        },
        "MINOR_VIBRATION": {
            "vibration_range": (3.0, 4.5),
            "temp_range": (60, 72),
            "current_range": (9, 12),
            "priority": 1,
            "description": "Minor vibration - possible misalignment",
            "rag_query": "vibration alignment coupling balance impeller"
        },
        
        # Level 2 - MEDIUM severity
        "CAVITATION": {
            # From fault_scenarios: vibration_base: 5.2, inlet_pressure_factor: 0.75
            "vibration_range": (4.5, 6.5),
            "pressure_range": (1.5, 3.0),  # Low pressure is KEY indicator
            "flow_range": (10, 14),
            "temp_range": (60, 75),  # Temperature stays relatively normal
            "priority": 2,
            "description": "Cavitation - vapor bubbles in fluid",
            "rag_query": "cavitation NPSH inlet pressure vapor bubbles impeller damage"
        },
        "IMPELLER_WEAR": {
            # From fault_scenarios: vibration_base: 4.8, current_factor: 1.08, flow_rate_factor: 0.80
            "vibration_range": (4.0, 6.0),
            "flow_range": (10, 13),
            "current_range": (10, 13),
            "pressure_range": (3.5, 5.0),
            "temp_range": (60, 75),  # Normal temp
            "priority": 2,
            "description": "Impeller wear - reduced efficiency",
            "rag_query": "impeller wear efficiency hydraulic performance replacement"
        },
        "SEAL_LEAK": {
            # From fault_scenarios: motor_temp_add: 8, outlet_pressure_factor: 0.92
            "pressure_range": (3.8, 5.0),
            "temp_range": (70, 80),
            "vibration_range": (2.0, 4.0),
            "priority": 2,
            "description": "Mechanical seal leak",
            "rag_query": "mechanical seal leak shaft seal replacement inspection"
        },
        
        # Level 3 - HIGH severity (check before MEDIUM to prioritize severe cases)
        "BEARING_WEAR": {
            # From fault_scenarios: vibration_base: 7.2, motor_temp_add: 18, current_factor: 1.12
            # KEY indicators: HIGH vibration (6.5-9) + HIGH temperature (80-95)
            "vibration_range": (6.5, 9.5),
            "temp_range": (80, 95),
            "current_range": (10, 15),
            "pressure_range": (3.0, 5.5),  # Pressure stays relatively normal
            "priority": 3,
            "description": "Advanced bearing wear - urgent intervention needed",
            "rag_query": "bearing wear vibration temperature lubrication replacement"
        },
        "WINDING_DEFECT": {
            # From fault_scenarios: current_base: 28.5, motor_temp_add: 25, vibration_base: 6.5
            # KEY indicator: HIGH imbalance + high current
            "imbalance_range": (8, 25),
            "temp_range": (85, 100),
            "current_range": (25, 35),
            "vibration_range": (5.5, 8.0),
            "priority": 3,
            "description": "Motor winding defect - failure risk",
            "rag_query": "motor winding defect phase imbalance insulation resistance megger"
        },
        "SUPPLY_FAULT": {
            # KEY indicator: Voltage out of range OR high imbalance
            "voltage_range": (340, 375),
            "voltage_high_range": (425, 460),
            "imbalance_range": (5, 20),
            "temp_range": (70, 90),
            "priority": 3,
            "description": "Electrical supply problem",
            "rag_query": "voltage supply fault phase loss power quality electrical"
        },
        
        # Level 4 - CRITICAL severity (highest priority)
        "OVERLOAD": {
            # From fault_scenarios: current_factor: 1.50, motor_temp_add: 30, vibration_base: 8.5
            # KEY indicators: VERY HIGH current + VERY HIGH temp + HIGH vibration
            "current_range": (25, 45),
            "temp_range": (90, 105),
            "vibration_range": (7.5, 11.0),
            "flow_range": (3, 10),
            "priority": 4,
            "description": "MOTOR OVERLOAD - Immediate shutdown required",
            "rag_query": "motor overload overcurrent thermal protection trip emergency"
        },
        "PUMP_SEIZURE": {
            # KEY indicators: EXTREME current + EXTREME temp + EXTREME vibration + NO flow
            "current_range": (35, 60),
            "temp_range": (95, 120),
            "vibration_range": (9.0, 15.0),
            "flow_range": (0, 3),
            "pressure_range": (0, 2),
            "priority": 4,
            "description": "PUMP SEIZURE - DO NOT RESTART",
            "rag_query": "pump seizure blocked rotor mechanical failure emergency shutdown"
        }
    }
    
    def _detect_scenario_from_sensors(self, sensor_data: Dict) -> Tuple[str, Dict, float]:
        """
        Detect the most likely fault scenario based on sensor readings.
        
        This method analyzes sensor values and compares them against
        the thresholds defined for each scenario in fault_scenarios.py.
        
        Args:
            sensor_data: Current sensor readings
            
        Returns:
            Tuple of (scenario_id, scenario_info, confidence_score)
        """
        amps = sensor_data.get('amperage', {})
        voltage = sensor_data.get('voltage', 400)
        vibration = sensor_data.get('vibration', 1.5)
        temperature = sensor_data.get('temperature', 65)
        pressure = sensor_data.get('pressure', 5)
        flow = sensor_data.get('flow_rate', 15)
        current = amps.get('average', 10)
        imbalance = amps.get('imbalance_pct', 0)
        
        # Score each scenario based on how well sensor values match
        scenario_scores = {}
        
        for scenario_id, thresholds in self.SCENARIO_THRESHOLDS.items():
            if scenario_id == "NORMAL":
                continue  # Handle normal separately
                
            score = 0
            matches = 0
            total_checks = 0
            priority = thresholds.get('priority', 1)
            
            # Check vibration range (key indicator for mechanical issues)
            if 'vibration_range' in thresholds:
                total_checks += 1
                vmin, vmax = thresholds['vibration_range']
                if vmin <= vibration <= vmax:
                    score += 2.0  # High weight for vibration
                    matches += 1
                elif vibration > vmin * 0.9 and vibration < vmax * 1.1:
                    score += 0.8  # Close to range
            
            # Check temperature range (key indicator for thermal issues)
            if 'temp_range' in thresholds:
                total_checks += 1
                tmin, tmax = thresholds['temp_range']
                if tmin <= temperature <= tmax:
                    score += 2.0  # High weight for temperature
                    matches += 1
                elif temperature > tmin * 0.95 and temperature < tmax * 1.05:
                    score += 0.6
            
            # Check current range
            if 'current_range' in thresholds:
                total_checks += 1
                cmin, cmax = thresholds['current_range']
                if cmin <= current <= cmax:
                    score += 1.5
                    matches += 1
                elif current > cmin * 0.9:
                    score += 0.4
            
            # Check imbalance range
            if 'imbalance_range' in thresholds:
                total_checks += 1
                imin, imax = thresholds['imbalance_range']
                if imin <= imbalance <= imax:
                    score += 1.5  # Higher weight for imbalance
                    matches += 1
                elif imbalance > imin * 0.7:
                    score += 0.5
            
            # Check voltage range (can be low OR high)
            if 'voltage_range' in thresholds:
                total_checks += 1
                vmin, vmax = thresholds['voltage_range']
                if vmin <= voltage <= vmax:
                    score += 1.2
                    matches += 1
                # Also check high voltage range if defined
                if 'voltage_high_range' in thresholds:
                    vhmin, vhmax = thresholds['voltage_high_range']
                    if vhmin <= voltage <= vhmax:
                        score += 1.2
                        matches += 1
            
            # Check pressure range
            if 'pressure_range' in thresholds:
                total_checks += 1
                pmin, pmax = thresholds['pressure_range']
                if pmin <= pressure <= pmax:
                    score += 1.0
                    matches += 1
                elif pressure < pmin * 1.3:
                    score += 0.4
            
            # Check flow range
            if 'flow_range' in thresholds:
                total_checks += 1
                fmin, fmax = thresholds['flow_range']
                if fmin <= flow <= fmax:
                    score += 1.0
                    matches += 1
                elif flow < fmax * 1.2:
                    score += 0.3
            
            # Check pressure range (key for cavitation detection)
            if 'pressure_range' in thresholds:
                total_checks += 1
                pmin, pmax = thresholds['pressure_range']
                if pmin <= pressure <= pmax:
                    # Low pressure is KEY indicator for cavitation
                    if scenario_id == "CAVITATION" and pressure < 2.5:
                        score += 3.0  # Very high weight for low pressure in cavitation
                    else:
                        score += 1.0
                    matches += 1
                elif pressure > pmin * 0.8:
                    score += 0.4
            
            # Calculate confidence with priority boost
            if total_checks > 0:
                base_confidence = (score / (total_checks * 2)) * 100  # Normalize against max possible
                # Boost confidence for higher priority scenarios when they match well
                priority_boost = (priority - 1) * 5 if matches >= total_checks * 0.5 else 0
                confidence = min(100, base_confidence + priority_boost)
                
                scenario_scores[scenario_id] = {
                    'score': score,
                    'confidence': confidence,
                    'matches': matches,
                    'total_checks': total_checks,
                    'priority': priority,
                    'thresholds': thresholds
                }
        
        # Check if normal operation
        normal = self.SCENARIO_THRESHOLDS["NORMAL"]
        is_normal = (
            vibration <= normal["vibration_max"] and
            temperature <= normal["temp_max"] and
            current <= normal["current_max"] and
            imbalance <= normal["imbalance_max"] and
            normal["voltage_min"] <= voltage <= normal["voltage_max"] and
            pressure >= normal["pressure_min"] and
            flow >= normal["flow_min"]
        )
        
        if is_normal and not scenario_scores:
            return "NORMAL", {"description": "Normal operation"}, 100.0
        
        # FIRST: Check fault_state from sensor data (most reliable)
        fault_state = sensor_data.get('fault_state', 'Normal')
        if fault_state and fault_state != 'Normal':
            # Map fault_state to scenario ID
            fault_mapping = {
                'Winding Defect': 'WINDING_DEFECT',
                'Supply Fault': 'SUPPLY_FAULT',
                'Cavitation': 'CAVITATION',
                'Bearing Wear': 'BEARING_WEAR',
                'Overload': 'OVERLOAD',
                'Pump Seizure': 'PUMP_SEIZURE',
                'Filter Clogging': 'FILTER_CLOGGING',
                'Minor Vibration': 'MINOR_VIBRATION',
                'Impeller Wear': 'IMPELLER_WEAR',
                'Seal Leak': 'SEAL_LEAK',
            }
            mapped = fault_mapping.get(fault_state)
            if mapped and mapped in self.SCENARIO_THRESHOLDS:
                # Use fault_state with high confidence since it comes from the injection
                return mapped, self.SCENARIO_THRESHOLDS[mapped], 95.0
        
        # SECOND: Use sensor-based detection if fault_state is Normal but sensors show anomaly
        if scenario_scores:
            # Sort by priority first, then confidence
            sorted_scenarios = sorted(
                scenario_scores.items(),
                key=lambda x: (x[1].get('priority', 1), x[1]['confidence']),
                reverse=True
            )
            best_scenario = sorted_scenarios[0]
            scenario_id = best_scenario[0]
            info = best_scenario[1]
            
            # Only return if confidence is reasonable (> 35%)
            if info['confidence'] > 35:
                return scenario_id, info['thresholds'], info['confidence']
        
        return "UNKNOWN", {"description": "Undetermined state"}, 30.0
    
    def _get_scenario_context(self, scenario_id: str) -> Dict:
        """
        Get detailed scenario information from fault_scenarios.py if available.
        
        Args:
            scenario_id: The detected scenario ID
            
        Returns:
            Dictionary with scenario details (symptoms, causes, repair_action, etc.)
        """
        if SCENARIOS_AVAILABLE and scenario_id in FAULT_SCENARIOS:
            scenario = FAULT_SCENARIOS[scenario_id]
            return {
                "id": scenario.id,
                "name": scenario.display_name,
                "icon": scenario.icon,
                "severity": scenario.severity.name,
                "severity_value": scenario.severity.value,
                "description": scenario.description,
                "symptoms": scenario.symptoms,
                "causes": scenario.causes,
                "repair_action": scenario.repair_action,
                "maintenance_time": scenario.maintenance_time,
                "category": scenario.category,
                "manual_page": scenario.manual_page
            }
        
        # Fallback to basic info from thresholds
        if scenario_id in self.SCENARIO_THRESHOLDS:
            thresholds = self.SCENARIO_THRESHOLDS[scenario_id]
            return {
                "id": scenario_id,
                "description": thresholds.get('description', 'Unknown fault'),
                "rag_query": thresholds.get('rag_query', scenario_id)
            }
        
        return {"id": scenario_id, "description": "Unknown"}

    def _format_sensor_data(self, sensor_data: Dict) -> str:
        """
        Format sensor readings into human-readable text for the prompt.
        
        Args:
            sensor_data: Dictionary from PumpSimulator.get_sensor_reading()
        
        Returns:
            Formatted sensor data string
        """
        amps = sensor_data.get('amperage', {})
        
        sensor_text = f"""Current Sensor Readings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• TIMESTAMP: {sensor_data.get('timestamp', 'N/A')}
• FAULT STATE: {sensor_data.get('fault_state', 'Unknown')}
• FAULT DURATION: {sensor_data.get('fault_duration', 0)} seconds

ELECTRICAL:
  - Phase A Current: {amps.get('phase_a', 'N/A')} A
  - Phase B Current: {amps.get('phase_b', 'N/A')} A
  - Phase C Current: {amps.get('phase_c', 'N/A')} A
  - Average Current: {amps.get('average', 'N/A')} A
  - Phase Imbalance: {amps.get('imbalance_pct', 'N/A')}%
  - Supply Voltage: {sensor_data.get('voltage', 'N/A')} V

MECHANICAL:
  - Vibration: {sensor_data.get('vibration', 'N/A')} mm/s
  - Discharge Pressure: {sensor_data.get('pressure', 'N/A')} bar
  
THERMAL:
  - Motor Temperature: {sensor_data.get('temperature', 'N/A')} °C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return sensor_text
    
    def _evaluate_shutdown_decision(self, sensor_data: Dict) -> Dict[str, any]:
        """
        Evaluate whether the pump should be stopped based on sensor readings.
        
        Based on Grundfos manual recommendations:
        - Page 5: "Do NOT stop the pump immediately" for initial diagnosis
        - Critical conditions require immediate shutdown
        
        Thresholds:
        - Imbalance > 5%: From Grundfos manual Page 7
        - Voltage ±10%: From Grundfos manual Page 8
        - Vibration > 5 mm/s: ISO 10816 standard for pumps
        - Temperature > 80°C: IEC Class B motor insulation limit
        
        Args:
            sensor_data: Current sensor readings
            
        Returns:
            Dictionary with shutdown decision and reasoning
        """
        amps = sensor_data.get('amperage', {})
        imbalance = amps.get('imbalance_pct', 0)
        voltage = sensor_data.get('voltage', 230)
        vibration = sensor_data.get('vibration', 0)
        temperature = sensor_data.get('temperature', 65)
        pressure = sensor_data.get('pressure', 4)
        
        # Critical thresholds - IMMEDIATE SHUTDOWN REQUIRED
        critical_conditions = []
        
        # Temperature > 90°C: Imminent motor damage
        if temperature > 90:
            critical_conditions.append({
                "parameter": "Temperature",
                "value": f"{temperature:.1f}°C",
                "threshold": "90°C",
                "reason": "Motor insulation damage imminent - risk of fire"
            })
        
        # Extreme vibration > 10 mm/s: Mechanical destruction
        if vibration > 10:
            critical_conditions.append({
                "parameter": "Vibration",
                "value": f"{vibration:.2f} mm/s",
                "threshold": "10 mm/s",
                "reason": "Severe mechanical damage in progress - bearing/impeller destruction"
            })
        
        # Severe phase imbalance > 15%: Winding burnout risk
        if imbalance > 15:
            critical_conditions.append({
                "parameter": "Phase Imbalance",
                "value": f"{imbalance:.1f}%",
                "threshold": "15%",
                "reason": "Severe winding damage risk - motor burnout imminent"
            })
        
        # Voltage for 400V 3-phase system: < 340V or > 460V (>15% deviation): Motor damage
        # Normal range: 380-420V (±5%), Warning: 360-380V or 420-440V (±10%), Critical: <340V or >460V (>15%)
        if voltage < 340 or voltage > 460:
            critical_conditions.append({
                "parameter": "Voltage",
                "value": f"{voltage:.1f}V",
                "threshold": "340-460V (±15% de 400V)",
                "reason": "Extreme voltage - immediate motor protection required"
            })
        
        # Zero or negative pressure: Dry running
        if pressure <= 0:
            critical_conditions.append({
                "parameter": "Pressure",
                "value": f"{pressure:.2f} bar",
                "threshold": "> 0 bar",
                "reason": "Dry running detected - pump damage imminent"
            })
        
        # Warning thresholds - Continue for diagnosis, then decide
        warning_conditions = []
        
        # Temperature 80-90°C: Monitor closely
        if 80 <= temperature <= 90:
            warning_conditions.append({
                "parameter": "Temperature",
                "value": f"{temperature:.1f}°C",
                "threshold": "80°C",
                "reason": "Elevated temperature - monitor and diagnose cause"
            })
        
        # Vibration 5-10 mm/s: Needs attention
        if 5 < vibration <= 10:
            warning_conditions.append({
                "parameter": "Vibration",
                "value": f"{vibration:.2f} mm/s",
                "threshold": "5 mm/s",
                "reason": "High vibration - continue briefly for diagnosis"
            })
        
        # Phase imbalance 5-15%: Investigate
        if 5 < imbalance <= 15:
            warning_conditions.append({
                "parameter": "Phase Imbalance",
                "value": f"{imbalance:.1f}%",
                "threshold": "5%",
                "reason": "Current imbalance detected - check windings after diagnosis"
            })
        
        # Voltage deviation 10-15% for 400V system: 360-380V or 420-440V
        if (360 <= voltage < 380) or (420 < voltage <= 440):
            warning_conditions.append({
                "parameter": "Voltage",
                "value": f"{voltage:.1f}V",
                "threshold": "±5% (380-420V)",
                "reason": "Voltage out of optimal range - monitor supply"
            })
        
        # Low pressure: Possible cavitation
        if 0 < pressure < 2:
            warning_conditions.append({
                "parameter": "Pressure",
                "value": f"{pressure:.2f} bar",
                "threshold": "2 bar",
                "reason": "Low pressure - check for cavitation or blockage"
            })
        
        # Determine shutdown decision
        if critical_conditions:
            return {
                "action": "IMMEDIATE_SHUTDOWN",
                "urgency": "CRITICAL",
                "icon": "⛔",
                "message": "ARRÊT IMMÉDIAT REQUIS - Conditions critiques détectées",
                "message_en": "IMMEDIATE SHUTDOWN REQUIRED - Critical conditions detected",
                "critical_conditions": critical_conditions,
                "warning_conditions": warning_conditions,
                "recommendation": "Couper l'alimentation immédiatement. Ne pas redémarrer avant inspection complète.",
                "recommendation_en": "Cut power immediately. Do not restart before complete inspection."
            }
        elif warning_conditions:
            return {
                "action": "CONTINUE_THEN_STOP",
                "urgency": "WARNING",
                "icon": "⚠️",
                "message": "Continuer pour diagnostic, puis arrêter pour inspection",
                "message_en": "Continue for diagnosis, then stop for inspection",
                "critical_conditions": [],
                "warning_conditions": warning_conditions,
                "recommendation": "Comme recommandé par Grundfos (Page 5): Ne pas arrêter immédiatement. Effectuer les mesures pendant le fonctionnement, puis arrêter pour correction.",
                "recommendation_en": "As recommended by Grundfos (Page 5): Do NOT stop immediately. Take measurements while running, then stop for correction."
            }
        else:
            return {
                "action": "NORMAL_OPERATION",
                "urgency": "OK",
                "icon": "✅",
                "message": "Fonctionnement normal - Aucune action requise",
                "message_en": "Normal operation - No action required",
                "critical_conditions": [],
                "warning_conditions": [],
                "recommendation": "Continuer la surveillance normale.",
                "recommendation_en": "Continue normal monitoring."
            }
    
    def _build_diagnostic_query(self, sensor_data: Dict, detected_scenario: str = None) -> str:
        """
        Construct a RAG query based on detected scenario and sensor anomalies.
        
        This method now uses the scenario detection system to build more
        targeted queries for the RAG knowledge base.
        
        Args:
            sensor_data: Sensor readings dictionary
            detected_scenario: Pre-detected scenario ID (optional)
        
        Returns:
            Optimized query string for RAG retrieval
        """
        # If we have a detected scenario, use its specific RAG query
        if detected_scenario and detected_scenario in self.SCENARIO_THRESHOLDS:
            scenario_info = self.SCENARIO_THRESHOLDS[detected_scenario]
            if 'rag_query' in scenario_info:
                base_query = scenario_info['rag_query']
                
                # Add severity-specific terms
                if detected_scenario in ['OVERLOAD', 'PUMP_SEIZURE']:
                    base_query += " emergency shutdown protection"
                elif detected_scenario in ['BEARING_WEAR', 'WINDING_DEFECT', 'SUPPLY_FAULT']:
                    base_query += " urgent repair maintenance"
                
                return base_query
        
        # Fallback: Build query based on individual sensor anomalies
        fault_state = sensor_data.get('fault_state', 'Normal')
        amps = sensor_data.get('amperage', {})
        imbalance = amps.get('imbalance_pct', 0)
        voltage = sensor_data.get('voltage', 400)
        vibration = sensor_data.get('vibration', 0)
        temperature = sensor_data.get('temperature', 65)
        pressure = sensor_data.get('pressure', 5)
        current = amps.get('average', 10)
        
        query_parts = []
        
        # CRITICAL CONDITIONS - highest priority
        if current > 28:
            query_parts.append("motor overload overcurrent protection thermal trip")
        if temperature > 88:
            query_parts.append("motor overheating insulation damage emergency")
        if vibration > 8:
            query_parts.append("severe vibration mechanical failure bearing")
        
        # HIGH SEVERITY CONDITIONS
        if imbalance > 8:
            query_parts.append("motor winding defect phase imbalance insulation")
        if voltage < 360 or voltage > 440:
            query_parts.append("voltage supply fault power quality electrical")
        if vibration > 6:
            query_parts.append("bearing wear vibration analysis replacement")
        
        # MEDIUM SEVERITY CONDITIONS  
        if vibration > 4.5:
            query_parts.append("cavitation NPSH inlet pressure impeller")
        if pressure < 3:
            query_parts.append("low pressure cavitation blockage valve")
        if temperature > 75:
            query_parts.append("elevated temperature cooling lubrication")
        
        # LOW SEVERITY CONDITIONS
        if 3 < vibration <= 4.5:
            query_parts.append("alignment balance coupling vibration")
        if 5 < imbalance <= 8:
            query_parts.append("current imbalance supply winding check")
        
        # Default fallback
        if not query_parts:
            if fault_state and fault_state != 'Normal':
                query_parts.append(f"{fault_state} troubleshooting diagnosis repair")
            else:
                query_parts.append("pump maintenance inspection checklist")
        
        return " ".join(query_parts)
    
    def get_diagnostic(
        self,
        sensor_data: Dict,
        user_question: Optional[str] = None,
        include_context: bool = True
    ) -> Dict[str, any]:
        """
        Generate AI diagnostic response based on sensor data.
        
        This method now uses scenario detection to provide more accurate
        and targeted diagnostics based on the fault_scenarios.py definitions.
        
        Args:
            sensor_data: Current sensor readings from PumpSimulator
            user_question: Optional user query (for chat mode)
            include_context: Whether to retrieve RAG context
        
        Returns:
            Dictionary containing:
                - diagnosis: AI response text
                - context_used: Retrieved documentation chunks
                - query: RAG query that was used
                - fault_detected: Boolean
                - detected_scenario: The identified fault scenario
        """
        print(f"\n🔍 Analyzing fault: {sensor_data.get('fault_state', 'Unknown')}")
        
        # STEP 1: Detect scenario from sensor values
        detected_scenario, scenario_match_info, confidence = self._detect_scenario_from_sensors(sensor_data)
        print(f"🎯 Detected Scenario: {detected_scenario} (confidence: {confidence:.1f}%)")
        
        # STEP 2: Get detailed scenario information
        scenario_context = self._get_scenario_context(detected_scenario)
        
        # STEP 2.5: Get fault progression predictions
        fault_progressions = get_fault_progression(detected_scenario)
        print(f"📈 Possible progressions: {len(fault_progressions)}")
        
        # Format sensor data
        sensor_text = self._format_sensor_data(sensor_data)
        
        # Build progression warning text with prevention actions
        progression_text = ""
        if fault_progressions:
            progression_lines = ["📈 PREDICTIVE ANALYSIS - If not fixed, this can lead to:"]
            for i, prog in enumerate(fault_progressions, 1):
                progression_lines.append(
                    f"   {i}. {prog['target_name']} ({prog['probability']}% likely) - "
                    f"within {prog['time_to_progress']}"
                )
                progression_lines.append(f"      ⚡ Trigger: {prog['trigger_conditions']}")
                if prog.get('prevention_action'):
                    progression_lines.append(f"      ✅ Prevention: {prog['prevention_action']}")
            progression_text = chr(10).join(progression_lines)
        
        # Add detected scenario info to sensor text
        scenario_info_text = ""
        if detected_scenario != "NORMAL" and detected_scenario != "UNKNOWN":
            scenario_info_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 DETECTED SCENARIO: {scenario_context.get('name', detected_scenario)}
   Confidence: {confidence:.0f}%
   Severity: {scenario_context.get('severity', 'N/A')}
   Category: {scenario_context.get('category', 'N/A')}
   
📋 DESCRIPTION:
   {scenario_context.get('description', 'N/A')}

⚠️ EXPECTED SYMPTOMS:
   {chr(10).join(['   • ' + s for s in scenario_context.get('symptoms', ['N/A'])])}

🔧 POSSIBLE CAUSES:
   {chr(10).join(['   • ' + c for c in scenario_context.get('causes', ['N/A'])])}

{progression_text}

🛠️ RECOMMENDED ACTION:
   {scenario_context.get('repair_action', 'N/A')}
   
⏱️ ESTIMATED TIME: {scenario_context.get('maintenance_time', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # STEP 3: Build RAG query based on detected scenario
        context = ""
        retrieved_chunks = []
        rag_query = ""
        
        if include_context:
            rag_query = self._build_diagnostic_query(sensor_data, detected_scenario)
            print(f"📚 RAG Query: '{rag_query}'")
            
            retrieved_chunks = self.rag_engine.query_knowledge_base(
                query=rag_query,
                top_k=3
            )
            
            context = self._format_context(retrieved_chunks)
        
        # STEP 4: Build the prompt with scenario context
        if user_question:
            # Chat mode - user asked a specific question
            prompt = f"""{self.system_prompt}

{sensor_text}
{scenario_info_text}

DOCUMENTATION CONTEXT:
{context if context else "No specific documentation retrieved."}

USER QUESTION: {user_question}

Provide a focused answer to the user's question. Use the detected scenario information 
and documentation to give precise, actionable advice."""
        else:
            # Auto-diagnostic mode - analyze fault automatically
            severity_instruction = ""
            if scenario_context.get('severity_value', 0) >= 3:
                severity_instruction = """
⚠️ WARNING: HIGH SEVERITY scenario detected!
Prioritize safety and recommend shutdown if necessary."""
            elif scenario_context.get('severity_value', 0) == 4:
                severity_instruction = """
🚨 EMERGENCY: CRITICAL scenario detected!
Immediate shutdown may be required. Assess risks as priority."""
            
            prompt = f"""{self.system_prompt}
{severity_instruction}

{sensor_text}
{scenario_info_text}

DOCUMENTATION CONTEXT (from Grundfos manual):
{context if context else "No specific documentation retrieved."}

TASK: Based on the detected scenario "{scenario_context.get('name', detected_scenario)}" and sensor data:

1. **MAIN DIAGNOSTIC**: Confirm or refine the detected scenario
2. **ROOT CAUSE**: Explain why this problem is occurring
3. **IMMEDIATE ACTIONS**: What should the technician do now?
4. **VERIFICATION**: How to confirm the diagnosis?

Respond in ENGLISH. Be concise (max 250 words) for dashboard display."""
        
        # Get AI response
        print("🤖 Generating diagnostic response...")
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            diagnosis_text = response.content if response.content else "No response generated. The model may have filtered the content."
            
            # Debug: Check for safety ratings or other issues
            if not response.content:
                print("⚠️  Warning: Empty response from model")
                if hasattr(response, 'response_metadata'):
                    print(f"Response metadata: {response.response_metadata}")
        
        except Exception as e:
            diagnosis_text = f"Error generating diagnosis: {str(e)}"
            print(f"❌ Error: {str(e)}")
        
        # Detect if this is an actual fault
        fault_detected = sensor_data.get('fault_state', 'Normal') != 'Normal'
        
        # Evaluate shutdown decision based on Grundfos manual recommendations
        shutdown_decision = self._evaluate_shutdown_decision(sensor_data)
        
        # Log shutdown decision
        if shutdown_decision["action"] == "IMMEDIATE_SHUTDOWN":
            print(f"⛔ CRITICAL: {shutdown_decision['message_en']}")
            for cond in shutdown_decision["critical_conditions"]:
                print(f"   - {cond['parameter']}: {cond['value']} (threshold: {cond['threshold']})")
        elif shutdown_decision["action"] == "CONTINUE_THEN_STOP":
            print(f"⚠️  WARNING: {shutdown_decision['message_en']}")
        
        print("✅ Diagnostic complete!\n")
        
        return {
            "diagnosis": diagnosis_text,
            "context_used": retrieved_chunks,
            "rag_query": rag_query,
            "fault_detected": fault_detected,
            "shutdown_decision": shutdown_decision,
            "detected_scenario": {
                "id": detected_scenario,
                "confidence": confidence,
                "info": scenario_context
            },
            "fault_progressions": fault_progressions,  # NEW: predictive progression data
            "sensor_summary": {
                "fault_state": sensor_data.get('fault_state'),
                "imbalance": sensor_data.get('amperage', {}).get('imbalance_pct'),
                "voltage": sensor_data.get('voltage'),
                "vibration": sensor_data.get('vibration'),
                "temperature": sensor_data.get('temperature'),
                "pressure": sensor_data.get('pressure'),
                "flow_rate": sensor_data.get('flow_rate'),
                "current": sensor_data.get('amperage', {}).get('average')
            }
        }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved documentation chunks for the prompt.
        
        Args:
            chunks: List of retrieved document chunks from RAG
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documentation found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            page = chunk.get('page', 'Unknown')
            content = chunk.get('content', '')
            context_parts.append(
                f"[Manual Reference {i} - Page {page}]\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def ask_question(self, question: str, sensor_data: Optional[Dict] = None) -> str:
        """
        Chat mode - answer user questions about maintenance.
        
        Args:
            question: User's question
            sensor_data: Optional current sensor readings for context
        
        Returns:
            AI response text
        """
        print(f"\n💬 User Question: {question}")
        
        # Retrieve relevant documentation
        print("📚 Searching knowledge base...")
        chunks = self.rag_engine.query_knowledge_base(question, top_k=3)
        context = self._format_context(chunks)
        
        # Build prompt
        sensor_context = ""
        if sensor_data:
            sensor_context = f"\n\nCURRENT PUMP STATUS:\n{self._format_sensor_data(sensor_data)}"
        
        prompt = f"""{self.system_prompt}

{sensor_context}

DOCUMENTATION CONTEXT:
{context}

USER QUESTION: {question}

Provide a clear, actionable answer based on the manual and current pump status (if available)."""
        
        # Get response
        print("🤖 Generating response...")
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            response_text = response.content if response.content else "No response generated."
            
            if not response.content:
                print("⚠️  Warning: Empty response from model")
        except Exception as e:
            response_text = f"Error: {str(e)}"
            print(f"❌ Error: {str(e)}")
        
        print("✅ Response generated!\n")
        return response_text


# Testing and demonstration
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 AI AGENT TEST MODE")
    print("="*80 + "\n")
    
    try:
        # Initialize agent
        agent = MaintenanceAIAgent()
        
        # Import simulator for test data
        from simulator import PumpSimulator, FaultType
        pump = PumpSimulator()
        
        # Test scenarios
        test_scenarios = [
            (FaultType.WINDING_DEFECT, "Motor winding defect with phase imbalance"),
            (FaultType.CAVITATION, "Cavitation with high vibration"),
            (FaultType.SUPPLY_FAULT, "Voltage supply fault"),
        ]
        
        print("\n" + "─"*80)
        print("📋 RUNNING AUTO-DIAGNOSTIC TESTS")
        print("─"*80 + "\n")
        
        for fault_type, description in test_scenarios:
            print(f"\n{'═'*80}")
            print(f"🔧 TEST SCENARIO: {description}")
            print(f"{'═'*80}\n")
            
            # Inject fault and generate reading
            pump.inject_fault(fault_type)
            sensor_data = pump.get_sensor_reading()
            
            # Get AI diagnostic
            result = agent.get_diagnostic(sensor_data)
            
            print("🤖 AI DIAGNOSTIC:")
            print("─"*80)
            print(result['diagnosis'])
            print("─"*80)
            
            print(f"\n📚 Documentation References Used:")
            for i, chunk in enumerate(result['context_used'], 1):
                print(f"   [{i}] Page {chunk['page']} (Score: {chunk['score']:.3f})")
            
            input("\n⏸️  Press Enter to continue...\n")
        
        # Test chat mode
        print("\n" + "─"*80)
        print("💬 TESTING CHAT MODE")
        print("─"*80 + "\n")
        
        pump.reset_fault()
        sensor_data = pump.get_sensor_reading()
        
        test_questions = [
            "What tools do I need to inspect the impeller?",
            "How do I measure motor winding resistance?",
            "What causes mechanical seal failure?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            print("─"*80)
            answer = agent.ask_question(question, sensor_data)
            print(answer)
            print("─"*80)
            input("\n⏸️  Press Enter for next question...\n")
        
        print("\n" + "="*80)
        print("✅ AI AGENT TEST COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()

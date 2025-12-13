"""
Fault Scenarios Manager for Digital Twin
Based on Grundfos CR Pump Troubleshooting Manual

This module defines realistic fault scenarios with:
- Severity levels (for transition logic)
- User-friendly descriptions in French
- Repair/maintenance actions
- Sensor value modifications
"""

from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass


class Severity(Enum):
    """Severity levels - determines state transition rules"""
    NORMAL = 0      # Fonctionnement normal
    LOW = 1         # Avertissement léger
    MEDIUM = 2      # Problème modéré
    HIGH = 3        # Problème sérieux
    CRITICAL = 4    # Critique - arrêt requis


@dataclass
class FaultProgression:
    """Defines how a fault can evolve into more severe faults"""
    target_fault: str           # ID of the fault it can evolve into
    probability: float          # Probability (0-100%) of this progression
    time_to_progress: str       # Estimated time before progression if not fixed
    trigger_conditions: str     # What accelerates this progression
    prevention_action: str      # What to do to PREVENT this progression


@dataclass
class FaultScenario:
    """Complete fault scenario definition"""
    id: str
    name: str                   # Technical name
    display_name: str           # User-friendly name
    icon: str                   # Emoji icon
    severity: Severity          # Severity level
    category: str               # Category (electrical, hydraulic, mechanical)
    
    # User-friendly information
    description: str            # What's happening
    symptoms: List[str]         # Observable symptoms
    causes: List[str]           # Possible causes
    repair_action: str          # What to do to fix
    maintenance_time: str       # Estimated time
    
    # Sensor modifications (multipliers or absolute values)
    sensor_effects: Dict[str, float]
    
    # PDF reference
    manual_page: Optional[str] = None
    
    # Fault progression - what can this fault evolve into?
    can_progress_to: Optional[List[FaultProgression]] = None


# =============================================================================
# FAULT SCENARIOS BASED ON GRUNDFOS CR TROUBLESHOOTING MANUAL
# =============================================================================

FAULT_SCENARIOS: Dict[str, FaultScenario] = {
    
    # -------------------------------------------------------------------------
    # NORMAL OPERATION
    # -------------------------------------------------------------------------
    "NORMAL": FaultScenario(
        id="NORMAL",
        name="Normal Operation",
        display_name="🟢 Normal Operation",
        icon="✅",
        severity=Severity.NORMAL,
        category="normal",
        description="Pump operating within normal parameters. All sensors indicate optimal values.",
        symptoms=[
            "Stable and low vibrations",
            "Normal motor temperature (< 70°C)",
            "Flow and pressure within spec",
            "Stable electrical current"
        ],
        causes=["No anomaly detected"],
        repair_action="No action required. Continue regular monitoring.",
        maintenance_time="N/A",
        sensor_effects={},  # No modifications
        manual_page="General Operation"
    ),
    
    # -------------------------------------------------------------------------
    # LEVEL 1 - LOW SEVERITY (Can transition to any state)
    # -------------------------------------------------------------------------
    "FILTER_CLOGGING": FaultScenario(
        id="FILTER_CLOGGING",
        name="Filter Clogging",
        display_name="🔶 Filter Clogging",
        icon="🧹",
        severity=Severity.LOW,
        category="hydraulic",
        description="Inlet strainer is becoming clogged, slightly reducing flow rate.",
        symptoms=[
            "Slight flow reduction (-10%)",
            "Dropping inlet pressure",
            "Slightly modified pumping noise",
            "No notable temperature change"
        ],
        causes=[
            "Debris accumulation in filter",
            "Non-compliant water quality",
            "Maintenance interval exceeded"
        ],
        repair_action="Clean or replace inlet strainer. Check water source quality.",
        maintenance_time="15-30 minutes",
        sensor_effects={
            "flow_rate_factor": 0.90,      # -10% flow
            "inlet_pressure_factor": 0.92,  # -8% inlet pressure
            "vibration_add": 0.3,           # +0.3 mm/s vibration
        },
        manual_page="Page 5 - Filter Maintenance",
        can_progress_to=[
            FaultProgression(
                target_fault="CAVITATION",
                probability=65,
                time_to_progress="2-4 hours",
                trigger_conditions="Continued operation with clogged filter reduces NPSH",
                prevention_action="Clean filter immediately. Check inlet pressure is above 0.5 bar"
            ),
            FaultProgression(
                target_fault="IMPELLER_WEAR",
                probability=25,
                time_to_progress="1-2 weeks",
                trigger_conditions="Debris passing through damages impeller",
                prevention_action="Install finer mesh strainer. Improve water source filtration"
            ),
            FaultProgression(
                target_fault="OVERLOAD",
                probability=10,
                time_to_progress="4-8 hours",
                trigger_conditions="Severe blockage causes motor strain",
                prevention_action="Stop pump and clear blockage before motor current rises >15A"
            ),
        ]
    ),
    
    "MINOR_VIBRATION": FaultScenario(
        id="MINOR_VIBRATION",
        name="Minor Vibration Increase",
        display_name="🔶 Minor Vibration",
        icon="📳",
        severity=Severity.LOW,
        category="mechanical",
        description="Slight vibration increase detected. Monitoring recommended.",
        symptoms=[
            "Slightly elevated vibrations (3-4 mm/s)",
            "Otherwise stable operation",
            "No significant abnormal noise"
        ],
        causes=[
            "Slight impeller imbalance",
            "Slightly loose fasteners",
            "Early seal wear"
        ],
        repair_action="Check fastener torque. Schedule an inspection.",
        maintenance_time="30 minutes - 1 hour",
        sensor_effects={
            "vibration_base": 3.5,          # Vibration at 3.5 mm/s
            "vibration_variance": 0.8,      # More variance
        },
        manual_page="Page 7 - Vibration Analysis",
        can_progress_to=[
            FaultProgression(
                target_fault="BEARING_WEAR",
                probability=55,
                time_to_progress="1-4 weeks",
                trigger_conditions="Unaddressed vibration accelerates bearing degradation",
                prevention_action="Check and tighten all mounting bolts. Verify alignment with dial indicator"
            ),
            FaultProgression(
                target_fault="IMPELLER_WEAR",
                probability=30,
                time_to_progress="2-6 weeks",
                trigger_conditions="Imbalance causes uneven impeller wear",
                prevention_action="Balance impeller if vibration >4mm/s. Check for debris on impeller"
            ),
            FaultProgression(
                target_fault="SEAL_LEAK",
                probability=15,
                time_to_progress="1-3 weeks",
                trigger_conditions="Vibration damages mechanical seal faces",
                prevention_action="Reduce vibration below 3mm/s. Inspect seal for wear marks"
            ),
        ]
    ),
    
    # -------------------------------------------------------------------------
    # LEVEL 2 - MEDIUM SEVERITY
    # -------------------------------------------------------------------------
    "CAVITATION": FaultScenario(
        id="CAVITATION",
        name="Cavitation",
        display_name="🟠 Cavitation",
        icon="💧",
        severity=Severity.MEDIUM,
        category="hydraulic",
        description="Vapor bubbles forming in fluid causing progressive impeller damage.",
        symptoms=[
            "Crackling/gravel-like noise",
            "Moderate vibrations (4-6 mm/s)",
            "Flow fluctuations",
            "Reduced hydraulic performance"
        ],
        causes=[
            "Insufficient NPSH available",
            "Fluid temperature too high",
            "Inlet valve partially closed",
            "Excessive suction height"
        ],
        repair_action="Check NPSH. Fully open inlet valve. Reduce fluid temperature if possible.",
        maintenance_time="1-2 hours",
        sensor_effects={
            "vibration_base": 5.2,
            "vibration_variance": 1.5,
            "flow_rate_factor": 0.82,
            "inlet_pressure_factor": 0.75,
            "efficiency_factor": 0.85,
        },
        manual_page="Page 8 - Cavitation Troubleshooting",
        can_progress_to=[
            FaultProgression(
                target_fault="IMPELLER_WEAR",
                probability=60,
                time_to_progress="2-7 days",
                trigger_conditions="Bubble collapse erodes impeller material",
                prevention_action="Increase inlet pressure above 2 bar. Lower fluid temp below 60°C"
            ),
            FaultProgression(
                target_fault="BEARING_WEAR",
                probability=25,
                time_to_progress="1-3 weeks",
                trigger_conditions="Cavitation-induced vibration damages bearings",
                prevention_action="Eliminate cavitation noise. Keep vibration below 5mm/s"
            ),
            FaultProgression(
                target_fault="SEAL_LEAK",
                probability=15,
                time_to_progress="1-2 weeks",
                trigger_conditions="Pressure fluctuations damage seal",
                prevention_action="Stabilize inlet pressure. Check seal flush system is working"
            ),
        ]
    ),
    
    "IMPELLER_WEAR": FaultScenario(
        id="IMPELLER_WEAR",
        name="Impeller Wear",
        display_name="🟠 Impeller Wear",
        icon="⚙️",
        severity=Severity.MEDIUM,
        category="mechanical",
        description="Impeller showing wear signs, reducing pumping efficiency.",
        symptoms=[
            "Progressive flow reduction",
            "Increased vibrations",
            "Reduced efficiency",
            "Slightly increased power consumption"
        ],
        causes=[
            "Normal age-related wear",
            "Abrasive particles in fluid",
            "Prolonged uncorrected cavitation"
        ],
        repair_action="Schedule impeller replacement. Check pumped fluid condition.",
        maintenance_time="2-4 hours",
        sensor_effects={
            "flow_rate_factor": 0.80,
            "efficiency_factor": 0.82,
            "vibration_base": 4.8,
            "current_factor": 1.08,
        },
        manual_page="Page 10 - Impeller Inspection",
        can_progress_to=[
            FaultProgression(
                target_fault="OVERLOAD",
                probability=50,
                time_to_progress="1-3 days",
                trigger_conditions="Motor works harder to compensate for reduced efficiency",
                prevention_action="Monitor motor current closely. Replace impeller when current >12A continuously"
            ),
            FaultProgression(
                target_fault="BEARING_WEAR",
                probability=35,
                time_to_progress="1-2 weeks",
                trigger_conditions="Imbalanced worn impeller stresses bearings",
                prevention_action="Schedule impeller replacement within 1 week. Check bearing temperature daily"
            ),
            FaultProgression(
                target_fault="PUMP_SEIZURE",
                probability=15,
                time_to_progress="2-4 weeks",
                trigger_conditions="Severe wear causes impeller contact with casing",
                prevention_action="Stop pump if unusual noise heard. Inspect clearances before catastrophic failure"
            ),
        ]
    ),
    
    "SEAL_LEAK": FaultScenario(
        id="SEAL_LEAK",
        name="Mechanical Seal Leak",
        display_name="🟠 Seal Leak",
        icon="💦",
        severity=Severity.MEDIUM,
        category="mechanical",
        description="Mechanical seal has a leak. Short-term intervention required.",
        symptoms=[
            "Visible leak at seal location",
            "Slight pressure drop",
            "Moisture traces on motor",
            "Possible temperature increase"
        ],
        causes=[
            "Normal seal wear",
            "Dry running",
            "Particles in fluid",
            "Misalignment"
        ],
        repair_action="Replace mechanical seal. Check alignment and fluid quality.",
        maintenance_time="2-3 hours",
        sensor_effects={
            "outlet_pressure_factor": 0.92,
            "motor_temp_add": 8,
            "efficiency_factor": 0.90,
        },
        manual_page="Page 12 - Seal Replacement",
        can_progress_to=[
            FaultProgression(
                target_fault="BEARING_WEAR",
                probability=45,
                time_to_progress="3-7 days",
                trigger_conditions="Leaking fluid contaminates bearing lubricant",
                prevention_action="Replace seal immediately. Clean and re-grease bearings after seal change"
            ),
            FaultProgression(
                target_fault="WINDING_DEFECT",
                probability=35,
                time_to_progress="1-2 weeks",
                trigger_conditions="Moisture ingress damages motor insulation",
                prevention_action="Protect motor from leaking fluid. Check insulation resistance with megger"
            ),
            FaultProgression(
                target_fault="PUMP_SEIZURE",
                probability=20,
                time_to_progress="1-3 weeks",
                trigger_conditions="Total seal failure leads to dry running",
                prevention_action="Monitor seal leakage rate. Stop pump if leak becomes a stream"
            ),
        ]
    ),
    
    # -------------------------------------------------------------------------
    # LEVEL 3 - HIGH SEVERITY
    # -------------------------------------------------------------------------
    "BEARING_WEAR": FaultScenario(
        id="BEARING_WEAR",
        name="Bearing Wear",
        display_name="🔴 Bearing Wear",
        icon="🔧",
        severity=Severity.HIGH,
        category="mechanical",
        description="Bearings showing advanced wear signs. Urgent intervention recommended.",
        symptoms=[
            "High vibrations (6-8 mm/s)",
            "Rumbling or whistling noise",
            "Rising motor temperature",
            "Perceptible mechanical play"
        ],
        causes=[
            "Natural bearing wear",
            "Insufficient lubrication",
            "Excessive radial load",
            "Lubricant contamination"
        ],
        repair_action="⚠️ STOP THE PUMP as soon as possible. Replace bearings.",
        maintenance_time="3-5 hours",
        sensor_effects={
            "vibration_base": 7.2,
            "vibration_variance": 2.0,
            "motor_temp_add": 18,
            "current_factor": 1.12,
            "efficiency_factor": 0.78,
        },
        manual_page="Page 14 - Bearing Replacement",
        can_progress_to=[
            FaultProgression(
                target_fault="PUMP_SEIZURE",
                probability=70,
                time_to_progress="2-24 hours",
                trigger_conditions="Complete bearing failure causes rotor seizure",
                prevention_action="STOP PUMP NOW. Do not operate with vibration >8mm/s or temp >85°C"
            ),
            FaultProgression(
                target_fault="OVERLOAD",
                probability=30,
                time_to_progress="1-4 hours",
                trigger_conditions="Increased friction causes motor overload",
                prevention_action="Monitor current closely. Stop if current exceeds 20A for >5 minutes"
            ),
        ]
    ),
    
    "WINDING_DEFECT": FaultScenario(
        id="WINDING_DEFECT",
        name="Motor Winding Defect",
        display_name="🔴 Winding Defect",
        icon="⚡",
        severity=Severity.HIGH,
        category="electrical",
        description="Defect detected in motor winding. Imminent failure risk.",
        symptoms=[
            "Unstable motor current",
            "High motor temperature",
            "Possible burning smell",
            "Electromagnetic vibrations"
        ],
        causes=[
            "Partial short circuit in winding",
            "Deteriorated insulation",
            "Prolonged overheating",
            "Moisture in motor"
        ],
        repair_action="⚠️ STOP IMMEDIATELY. Have motor rewound or replaced.",
        maintenance_time="4-8 hours (rewinding) or replacement",
        sensor_effects={
            "current_base": 28.5,
            "current_variance": 4.0,
            "motor_temp_add": 25,
            "vibration_base": 6.5,
        },
        manual_page="Page 16 - Motor Troubleshooting",
        can_progress_to=[
            FaultProgression(
                target_fault="OVERLOAD",
                probability=80,
                time_to_progress="30 min - 2 hours",
                trigger_conditions="Short circuit increases current draw rapidly",
                prevention_action="STOP IMMEDIATELY. Test insulation resistance - must be >1MΩ"
            ),
            FaultProgression(
                target_fault="PUMP_SEIZURE",
                probability=20,
                time_to_progress="1-4 hours",
                trigger_conditions="Complete motor failure stops pump",
                prevention_action="Do not attempt restart. Motor requires professional inspection"
            ),
        ]
    ),
    
    "SUPPLY_FAULT": FaultScenario(
        id="SUPPLY_FAULT",
        name="Power Supply Fault",
        display_name="🔴 Supply Fault",
        icon="🔌",
        severity=Severity.HIGH,
        category="electrical",
        description="Electrical supply problem detected. Verification required.",
        symptoms=[
            "Unstable or incorrect voltage",
            "Unbalanced current between phases",
            "Difficult starts",
            "Reduced performance"
        ],
        causes=[
            "Incorrect supply voltage",
            "Missing or weak phase",
            "Loose connections",
            "Variable frequency drive issue"
        ],
        repair_action="⚠️ Check electrical supply. Inspect VFD. Tighten connections.",
        maintenance_time="1-3 hours",
        sensor_effects={
            "voltage_variance": 15,
            "current_variance": 3.5,
            "motor_temp_add": 12,
            "efficiency_factor": 0.85,
        },
        manual_page="Page 18 - Electrical Checks",
        can_progress_to=[
            FaultProgression(
                target_fault="WINDING_DEFECT",
                probability=50,
                time_to_progress="2-8 hours",
                trigger_conditions="Phase imbalance causes uneven heating in windings",
                prevention_action="Check phase balance - must be within 2%. Repair supply before restart"
            ),
            FaultProgression(
                target_fault="OVERLOAD",
                probability=35,
                time_to_progress="1-4 hours",
                trigger_conditions="Single phasing causes remaining phases to overload",
                prevention_action="Verify all 3 phases present. Check fuses and contactors"
            ),
            FaultProgression(
                target_fault="BEARING_WEAR",
                probability=15,
                time_to_progress="1-2 weeks",
                trigger_conditions="Voltage fluctuations cause inconsistent motor torque",
                prevention_action="Install voltage stabilizer. Monitor power quality continuously"
            ),
        ]
    ),
    
    # -------------------------------------------------------------------------
    # LEVEL 4 - CRITICAL (Cannot transition down without repair)
    # -------------------------------------------------------------------------
    "OVERLOAD": FaultScenario(
        id="OVERLOAD",
        name="Motor Overload",
        display_name="⛔ Motor Overload",
        icon="🔥",
        severity=Severity.CRITICAL,
        category="electrical",
        description="🚨 CRITICAL: Motor is overloaded. IMMEDIATE SHUTDOWN REQUIRED to avoid permanent damage.",
        symptoms=[
            "Very high current (> 120% nominal)",
            "Critical motor temperature (> 90°C)",
            "Thermal breaker activated or imminent",
            "Risk of motor destruction"
        ],
        causes=[
            "Partial mechanical blockage",
            "Impeller blocked by foreign object",
            "Discharge valve closed",
            "Fluid viscosity too high"
        ],
        repair_action="🛑 EMERGENCY STOP! Identify and remove blockage cause before restart.",
        maintenance_time="Variable depending on cause",
        sensor_effects={
            "current_base": 32.0,
            "motor_temp_base": 92,
            "vibration_base": 8.5,
            "efficiency_factor": 0.60,
            "flow_rate_factor": 0.40,
        },
        manual_page="Page 20 - Emergency Procedures",
        can_progress_to=[
            FaultProgression(
                target_fault="PUMP_SEIZURE",
                probability=85,
                time_to_progress="5-30 minutes",
                trigger_conditions="Continued operation under overload destroys motor/bearings",
                prevention_action="IMMEDIATE SHUTDOWN! Remove blockage and verify free rotation before restart"
            ),
            FaultProgression(
                target_fault="WINDING_DEFECT",
                probability=15,
                time_to_progress="10-60 minutes",
                trigger_conditions="Overcurrent burns winding insulation",
                prevention_action="Reduce load immediately. Check thermal protection settings"
            ),
        ]
    ),
    
    "PUMP_SEIZURE": FaultScenario(
        id="PUMP_SEIZURE",
        name="Pump Seizure",
        display_name="⛔ Pump Seizure",
        icon="🚫",
        severity=Severity.CRITICAL,
        category="mechanical",
        description="🚨 CRITICAL: Pump is blocked or seized. IMMEDIATE STOP to avoid destruction.",
        symptoms=[
            "Complete flow stoppage",
            "Extremely high current",
            "Very high vibrations then stop",
            "Mechanical blocking noise"
        ],
        causes=[
            "Foreign object blocking impeller",
            "Bearing seizure",
            "Fluid freezing",
            "Major mechanical failure"
        ],
        repair_action="🛑 DO NOT RESTART! Complete disassembly required for inspection and repair.",
        maintenance_time="4-8 hours minimum",
        sensor_effects={
            "current_base": 38.0,
            "motor_temp_base": 98,
            "vibration_base": 10.0,
            "flow_rate_base": 0,
            "efficiency_factor": 0.0,
        },
        manual_page="Page 22 - Major Failures"
    ),
}


# =============================================================================
# STATE TRANSITION RULES
# =============================================================================

class StateTransitionManager:
    """
    Manages valid state transitions based on severity levels.
    
    Rules:
    - From NORMAL: Can go to any state
    - From LOW: Can go to NORMAL (repair) or same/higher severity
    - From MEDIUM: Can go to NORMAL (repair) or higher severity
    - From HIGH: Can go to NORMAL (repair) or CRITICAL
    - From CRITICAL: Can ONLY go to NORMAL (full repair/replacement required)
    """
    
    def __init__(self):
        self.current_state = "NORMAL"
    
    def get_current_scenario(self) -> FaultScenario:
        """Get current fault scenario"""
        return FAULT_SCENARIOS.get(self.current_state, FAULT_SCENARIOS["NORMAL"])
    
    def can_transition_to(self, target_state: str) -> tuple[bool, str]:
        """
        Check if transition from current state to target is allowed.
        
        Returns:
            (allowed, reason_message)
        """
        if target_state not in FAULT_SCENARIOS:
            return False, f"Unknown state: {target_state}"
        
        current = FAULT_SCENARIOS[self.current_state]
        target = FAULT_SCENARIOS[target_state]
        
        # From NORMAL: can go anywhere
        if current.severity == Severity.NORMAL:
            return True, "Transition allowed from normal state"
        
        # To NORMAL: always allowed (represents repair)
        if target.severity == Severity.NORMAL:
            return True, "Repair/Reset allowed"
        
        # From CRITICAL: can only go to NORMAL (needs repair)
        if current.severity == Severity.CRITICAL:
            return False, f"⛔ Critical state! You must first repair (return to Normal) before simulating another fault."
        
        # Cannot go from higher to lower severity (except NORMAL)
        if target.severity.value < current.severity.value:
            return False, f"⚠️ Cannot transition from {current.severity.name} state ({current.display_name}) to a less severe state ({target.display_name}). First repair by clicking 'Normal Operation'."
        
        # Same or higher severity: allowed
        return True, "Transition allowed"
    
    def get_allowed_transitions(self) -> List[str]:
        """Get list of states we can transition to from current state"""
        allowed = []
        for state_id in FAULT_SCENARIOS.keys():
            can_go, _ = self.can_transition_to(state_id)
            if can_go:
                allowed.append(state_id)
        return allowed
    
    def transition_to(self, target_state: str) -> tuple[bool, str, Optional[FaultScenario]]:
        """
        Attempt to transition to a new state.
        
        Returns:
            (success, message, new_scenario or None)
        """
        can_go, reason = self.can_transition_to(target_state)
        
        if can_go:
            old_state = self.current_state
            self.current_state = target_state
            new_scenario = FAULT_SCENARIOS[target_state]
            
            if target_state == "NORMAL":
                message = f"✅ System repaired! Back to normal operation. (was: {FAULT_SCENARIOS[old_state].display_name})"
            else:
                message = f"⚠️ {new_scenario.display_name} injected. {new_scenario.description}"
            
            return True, message, new_scenario
        else:
            return False, reason, None


# =============================================================================
# API HELPERS
# =============================================================================

def get_scenarios_for_ui() -> List[Dict]:
    """
    Get all scenarios formatted for the UI.
    Groups by severity and adds transition info.
    """
    categories = {
        "normal": {"name": "Normal State", "icon": "✅", "scenarios": []},
        "low": {"name": "Warnings (Level 1)", "icon": "🔶", "description": "Monitoring recommended", "scenarios": []},
        "medium": {"name": "Moderate Issues (Level 2)", "icon": "🟠", "description": "Planned intervention", "scenarios": []},
        "high": {"name": "Serious Issues (Level 3)", "icon": "🔴", "description": "Urgent intervention", "scenarios": []},
        "critical": {"name": "Critical States (Level 4)", "icon": "⛔", "description": "IMMEDIATE STOP", "scenarios": []},
    }
    
    severity_to_category = {
        Severity.NORMAL: "normal",
        Severity.LOW: "low",
        Severity.MEDIUM: "medium",
        Severity.HIGH: "high",
        Severity.CRITICAL: "critical",
    }
    
    for scenario in FAULT_SCENARIOS.values():
        cat = severity_to_category[scenario.severity]
        categories[cat]["scenarios"].append({
            "id": scenario.id,
            "name": scenario.name,
            "display_name": scenario.display_name,
            "icon": scenario.icon,
            "severity": scenario.severity.value,
            "severity_name": scenario.severity.name,
            "category": scenario.category,
            "description": scenario.description,
            "symptoms": scenario.symptoms,
            "causes": scenario.causes,
            "repair_action": scenario.repair_action,
            "maintenance_time": scenario.maintenance_time,
        })
    
    return categories


def get_scenario_details(scenario_id: str) -> Optional[Dict]:
    """Get detailed information about a specific scenario"""
    scenario = FAULT_SCENARIOS.get(scenario_id)
    if not scenario:
        return None
    
    return {
        "id": scenario.id,
        "name": scenario.name,
        "display_name": scenario.display_name,
        "icon": scenario.icon,
        "severity": scenario.severity.value,
        "severity_name": scenario.severity.name,
        "category": scenario.category,
        "description": scenario.description,
        "symptoms": scenario.symptoms,
        "causes": scenario.causes,
        "repair_action": scenario.repair_action,
        "maintenance_time": scenario.maintenance_time,
        "manual_page": scenario.manual_page,
        "sensor_effects": scenario.sensor_effects,
    }


def get_fault_progression(scenario_id: str) -> List[Dict]:
    """
    Get possible fault progressions for a scenario, sorted by probability (highest first).
    
    This is the predictive maintenance feature - shows what could go wrong next
    and how likely it is based on Grundfos manual causality chains.
    
    Args:
        scenario_id: Current fault scenario ID
        
    Returns:
        List of possible progressions sorted by probability, each containing:
        - target_fault: ID of the fault it can progress to
        - target_name: Display name of target fault
        - target_severity: Severity level of target fault
        - probability: Likelihood (0-100%)
        - time_to_progress: Estimated time before progression
        - trigger_conditions: What accelerates this progression
        - prevention_action: Recommended action to prevent progression
    """
    scenario = FAULT_SCENARIOS.get(scenario_id)
    if not scenario or not scenario.can_progress_to:
        return []
    
    progressions = []
    for prog in scenario.can_progress_to:
        target = FAULT_SCENARIOS.get(prog.target_fault)
        if target:
            progressions.append({
                "target_fault": prog.target_fault,
                "target_name": target.display_name,
                "target_icon": target.icon,
                "target_severity": target.severity.value,
                "target_severity_name": target.severity.name,
                "probability": prog.probability,
                "time_to_progress": prog.time_to_progress,
                "trigger_conditions": prog.trigger_conditions,
                "prevention_action": prog.prevention_action or "No specific action defined",
            })
    
    # Sort by probability (highest first)
    progressions.sort(key=lambda x: x["probability"], reverse=True)
    
    return progressions


def get_full_progression_chain(scenario_id: str, max_depth: int = 3) -> Dict:
    """
    Get the full progression tree showing all possible paths to failure.
    
    This builds a tree of what can happen if the fault is not fixed,
    showing the complete causality chain from the manual.
    
    Args:
        scenario_id: Starting fault scenario ID
        max_depth: Maximum depth of the tree (to prevent infinite loops)
        
    Returns:
        Tree structure with all possible progressions
    """
    def build_tree(fault_id: str, depth: int, visited: set) -> Dict:
        if depth <= 0 or fault_id in visited:
            return None
        
        visited.add(fault_id)
        scenario = FAULT_SCENARIOS.get(fault_id)
        if not scenario:
            return None
        
        progressions = get_fault_progression(fault_id)
        children = []
        
        for prog in progressions:
            child_tree = build_tree(prog["target_fault"], depth - 1, visited.copy())
            child_node = {
                **prog,
                "children": child_tree["progressions"] if child_tree else []
            }
            children.append(child_node)
        
        return {
            "fault_id": fault_id,
            "fault_name": scenario.display_name,
            "severity": scenario.severity.value,
            "progressions": children
        }
    
    return build_tree(scenario_id, max_depth, set())

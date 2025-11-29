"""
IoT Physics Simulator for Grundfos CR Pump
Generates realistic sensor data with fault injection capabilities
Based on troubleshooting manual specifications (Pages 6, 8, 9)
"""

import time
import random
from datetime import datetime
from typing import Dict, Generator
from enum import Enum

class FaultType(Enum):
    """Enumeration of fault conditions that can be simulated"""
    NORMAL = "Normal"
    WINDING_DEFECT = "Winding Defect"
    SUPPLY_FAULT = "Supply Fault"
    CAVITATION = "Cavitation"
    BEARING_WEAR = "Bearing Wear"
    OVERLOAD = "Overload"

class PumpSimulator:
    """
    Simulates a Grundfos CR Pump with realistic sensor behavior.
    
    Sensor Parameters:
    - Amperage (3-Phase): Normal operation with balanced phases
    - Voltage: 230V nominal (3-phase supply)
    - Vibration: Normal <2mm/s, Alert >5mm/s
    - Pressure: Nominal operating pressure with fluctuations
    - Temperature: Motor winding temperature
    """
    
    def __init__(
        self,
        nominal_voltage: float = 230.0,
        nominal_current: float = 10.0,
        nominal_vibration: float = 1.5,
        nominal_pressure: float = 5.0,
        nominal_temperature: float = 65.0
    ):
        """
        Initialize the pump simulator with nominal operating values.
        
        Args:
            nominal_voltage: Target voltage in V (default: 230V)
            nominal_current: Rated current per phase in A (default: 10A)
            nominal_vibration: Normal vibration in mm/s (default: 1.5)
            nominal_pressure: Operating pressure in bar (default: 5.0)
            nominal_temperature: Motor temperature in °C (default: 65)
        """
        self.nominal_voltage = nominal_voltage
        self.nominal_current = nominal_current
        self.nominal_vibration = nominal_vibration
        self.nominal_pressure = nominal_pressure
        self.nominal_temperature = nominal_temperature
        
        # Current fault state
        self.fault_state = FaultType.NORMAL
        
        # Fault injection parameters
        self.fault_duration = 0  # How long fault has been active
        self.fault_intensity = 1.0  # Multiplier for fault severity
        
        print("🏭 Grundfos CR Pump Simulator Initialized")
        print(f"   Nominal Voltage: {nominal_voltage}V")
        print(f"   Nominal Current: {nominal_current}A per phase")
        print(f"   Normal Vibration: {nominal_vibration} mm/s")
    
    def _generate_normal_amperage(self) -> Dict[str, float]:
        """
        Generate balanced 3-phase amperage readings (Normal operation).
        
        Returns:
            Dict with phase_a, phase_b, phase_c current values
        """
        # Small random variations (±2% is normal)
        variation = 0.02
        base = self.nominal_current
        
        return {
            "phase_a": base * random.uniform(1 - variation, 1 + variation),
            "phase_b": base * random.uniform(1 - variation, 1 + variation),
            "phase_c": base * random.uniform(1 - variation, 1 + variation)
        }
    
    def _generate_winding_fault_amperage(self) -> Dict[str, float]:
        """
        Generate amperage with winding defect (Page 8 logic).
        One phase shows >5% deviation from average.
        
        Returns:
            Dict with imbalanced phase currents
        """
        base = self.nominal_current
        
        # Progressive fault - gets worse over time
        imbalance = 0.05 + (self.fault_duration * 0.01)  # Start at 5%, increase
        imbalance = min(imbalance, 0.25)  # Cap at 25% deviation
        
        # Randomly select which phase is faulty
        faulty_phase = random.choice(['a', 'b', 'c'])
        
        amps = {
            "phase_a": base * random.uniform(0.98, 1.02),
            "phase_b": base * random.uniform(0.98, 1.02),
            "phase_c": base * random.uniform(0.98, 1.02)
        }
        
        # Inject fault in selected phase (could be higher or lower)
        fault_direction = random.choice([1, -1])
        amps[f"phase_{faulty_phase}"] *= (1 + fault_direction * imbalance)
        
        return amps
    
    def _generate_voltage(self) -> float:
        """
        Generate supply voltage based on fault state.
        
        Normal: ~230V (±2%)
        Supply Fault (Page 9): <207V (10% drop)
        
        Returns:
            Voltage reading in V
        """
        if self.fault_state == FaultType.SUPPLY_FAULT:
            # Voltage drop: 190-207V range
            return random.uniform(190, 207)
        elif self.fault_state == FaultType.OVERLOAD:
            # Slight voltage sag under heavy load
            return self.nominal_voltage * random.uniform(0.95, 0.98)
        else:
            # Normal: ±2% variation
            return self.nominal_voltage * random.uniform(0.98, 1.02)
    
    def _generate_vibration(self) -> float:
        """
        Generate vibration readings based on fault state.
        
        Normal: <2 mm/s
        Cavitation: >5 mm/s with fluctuations
        Bearing Wear: 3-6 mm/s progressive increase
        
        Returns:
            Vibration in mm/s
        """
        if self.fault_state == FaultType.CAVITATION:
            # High vibration with random spikes
            base_vib = 5.0 + random.uniform(0, 3.0)
            # Add random spikes
            if random.random() < 0.3:
                base_vib += random.uniform(2, 5)
            return base_vib
        
        elif self.fault_state == FaultType.BEARING_WEAR:
            # Progressive increase
            increase = self.fault_duration * 0.1
            return self.nominal_vibration + 1.5 + increase + random.uniform(-0.3, 0.5)
        
        elif self.fault_state == FaultType.OVERLOAD:
            # Slightly elevated
            return self.nominal_vibration * random.uniform(1.2, 1.6)
        
        else:
            # Normal: small random variations
            return self.nominal_vibration * random.uniform(0.8, 1.1)
    
    def _generate_pressure(self) -> float:
        """
        Generate discharge pressure based on fault state.
        
        Returns:
            Pressure in bar
        """
        if self.fault_state == FaultType.CAVITATION:
            # Fluctuating pressure
            fluctuation = random.uniform(-1.5, 0.5)
            return max(0, self.nominal_pressure + fluctuation)
        
        elif self.fault_state == FaultType.OVERLOAD:
            # Higher pressure (pump working harder)
            return self.nominal_pressure * random.uniform(1.1, 1.3)
        
        else:
            # Normal operation: ±5% variation
            return self.nominal_pressure * random.uniform(0.95, 1.05)
    
    def _generate_temperature(self) -> float:
        """
        Generate motor winding temperature.
        
        Returns:
            Temperature in °C
        """
        if self.fault_state == FaultType.WINDING_DEFECT:
            # Overheating due to winding issue
            return self.nominal_temperature + 15 + (self.fault_duration * 2)
        
        elif self.fault_state == FaultType.OVERLOAD:
            # Elevated temperature
            return self.nominal_temperature + 10 + random.uniform(0, 5)
        
        elif self.fault_state == FaultType.BEARING_WEAR:
            # Slight temperature increase
            return self.nominal_temperature + 5 + random.uniform(0, 3)
        
        else:
            # Normal: ±3°C variation
            return self.nominal_temperature + random.uniform(-3, 3)
    
    def inject_fault(self, fault_type: FaultType, intensity: float = 1.0):
        """
        Inject a fault condition into the simulation.
        
        Args:
            fault_type: Type of fault to simulate
            intensity: Severity multiplier (0.5 to 2.0)
        """
        self.fault_state = fault_type
        self.fault_duration = 0
        self.fault_intensity = max(0.5, min(2.0, intensity))
        
        print(f"\n⚠️  FAULT INJECTED: {fault_type.value}")
        print(f"   Intensity: {self.fault_intensity:.1f}x")
    
    def reset_fault(self):
        """Reset to normal operation"""
        self.fault_state = FaultType.NORMAL
        self.fault_duration = 0
        self.fault_intensity = 1.0
        print("\n✅ System Reset: Normal Operation Restored")
    
    def get_sensor_reading(self) -> Dict:
        """
        Generate a single sensor reading snapshot.
        
        Returns:
            Dictionary containing all sensor values and fault state
        """
        # Generate amperage based on fault state
        if self.fault_state == FaultType.WINDING_DEFECT:
            amps = self._generate_winding_fault_amperage()
        elif self.fault_state == FaultType.OVERLOAD:
            # Overload: all phases elevated
            amps = {
                "phase_a": self.nominal_current * random.uniform(1.15, 1.30),
                "phase_b": self.nominal_current * random.uniform(1.15, 1.30),
                "phase_c": self.nominal_current * random.uniform(1.15, 1.30)
            }
        else:
            amps = self._generate_normal_amperage()
        
        # Calculate average amperage
        avg_amps = (amps["phase_a"] + amps["phase_b"] + amps["phase_c"]) / 3
        
        # Calculate phase imbalance percentage
        max_dev = max(
            abs(amps["phase_a"] - avg_amps),
            abs(amps["phase_b"] - avg_amps),
            abs(amps["phase_c"] - avg_amps)
        )
        imbalance_pct = (max_dev / avg_amps) * 100 if avg_amps > 0 else 0
        
        # Increment fault duration
        if self.fault_state != FaultType.NORMAL:
            self.fault_duration += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "amperage": {
                "phase_a": round(amps["phase_a"], 2),
                "phase_b": round(amps["phase_b"], 2),
                "phase_c": round(amps["phase_c"], 2),
                "average": round(avg_amps, 2),
                "imbalance_pct": round(imbalance_pct, 2)
            },
            "voltage": round(self._generate_voltage(), 1),
            "vibration": round(self._generate_vibration(), 2),
            "pressure": round(self._generate_pressure(), 2),
            "temperature": round(self._generate_temperature(), 1),
            "fault_state": self.fault_state.value,
            "fault_duration": self.fault_duration
        }
    
    def stream_sensor_data(self, interval: float = 1.0) -> Generator[Dict, None, None]:
        """
        Generate continuous stream of sensor data.
        
        Args:
            interval: Time between readings in seconds (default: 1.0)
        
        Yields:
            Sensor reading dictionaries
        """
        print(f"\n📡 Starting sensor data stream (interval: {interval}s)")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                reading = self.get_sensor_reading()
                yield reading
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  Sensor stream stopped by user")


# Testing and demonstration
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 GRUNDFOS CR PUMP SIMULATOR - TEST MODE")
    print("="*80 + "\n")
    
    # Initialize simulator
    pump = PumpSimulator()
    
    # Test scenarios
    scenarios = [
        (FaultType.NORMAL, 5, "Normal Operation"),
        (FaultType.WINDING_DEFECT, 5, "Motor Winding Defect"),
        (FaultType.SUPPLY_FAULT, 5, "Voltage Supply Fault"),
        (FaultType.CAVITATION, 5, "Cavitation Condition"),
        (FaultType.BEARING_WEAR, 5, "Bearing Wear"),
        (FaultType.OVERLOAD, 5, "Pump Overload"),
    ]
    
    for fault_type, duration, description in scenarios:
        print("\n" + "─"*80)
        print(f"📊 SCENARIO: {description}")
        print("─"*80)
        
        if fault_type != FaultType.NORMAL:
            pump.inject_fault(fault_type)
        else:
            pump.reset_fault()
        
        for i in range(duration):
            reading = pump.get_sensor_reading()
            
            print(f"\n⏱️  Reading #{i+1}")
            print(f"   Amperage: A={reading['amperage']['phase_a']}A "
                  f"B={reading['amperage']['phase_b']}A "
                  f"C={reading['amperage']['phase_c']}A "
                  f"(Imbalance: {reading['amperage']['imbalance_pct']:.1f}%)")
            print(f"   Voltage: {reading['voltage']}V")
            print(f"   Vibration: {reading['vibration']} mm/s")
            print(f"   Pressure: {reading['pressure']} bar")
            print(f"   Temperature: {reading['temperature']}°C")
            print(f"   Status: {reading['fault_state']}")
            
            time.sleep(0.5)  # Faster for testing
    
    print("\n" + "="*80)
    print("✅ SIMULATOR TEST COMPLETE!")
    print("="*80 + "\n")

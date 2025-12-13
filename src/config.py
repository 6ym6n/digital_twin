"""
Configuration for Digital Twin System
Centralized configuration for MATLAB bridge, simulation, and API settings.

Author: Digital Twin Project
Date: December 2025
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import json


class DataSource(Enum):
    """Available data sources for the digital twin"""
    PYTHON = "python"      # Python PumpSimulator
    MATLAB = "matlab"      # MATLAB Simulink via TCP


@dataclass
class TCPConfig:
    """TCP communication configuration"""
    host: str = "0.0.0.0"          # Server bind address
    port: int = 5555               # TCP port
    buffer_size: int = 4096        # Receive buffer size
    timeout: float = 30.0          # Connection timeout (seconds)
    reconnect_delay: float = 5.0   # Delay between reconnection attempts
    max_queue_size: int = 100      # Max sensor readings in queue


@dataclass
class PumpConfig:
    """Grundfos CR 15 pump configuration"""
    # Identification
    model: str = "Grundfos CR 15"
    pump_type: str = "Vertical Multistage Centrifugal"
    
    # Hydraulic parameters
    nominal_flow_rate: float = 15.0       # m³/h
    min_flow_rate: float = 2.0            # m³/h
    max_flow_rate: float = 25.0           # m³/h
    nominal_head: float = 50.0            # m per stage
    stages: int = 5
    nominal_pressure: float = 5.0         # bar
    
    # Motor parameters
    motor_power: float = 5.5              # kW
    motor_voltage: float = 400            # V (3-phase)
    motor_current: float = 10.5           # A per phase
    nominal_speed: int = 2900             # RPM
    motor_efficiency: float = 0.88
    power_factor: float = 0.85
    
    # Thermal parameters
    ambient_temperature: float = 25.0     # °C
    max_fluid_temperature: float = 120.0  # °C
    nominal_operating_temp: float = 65.0  # °C
    
    # Vibration thresholds (ISO 10816)
    vibration_good: float = 1.8           # mm/s
    vibration_acceptable: float = 4.5     # mm/s
    vibration_alarm: float = 7.1          # mm/s
    vibration_danger: float = 11.2        # mm/s


@dataclass
class ThresholdConfig:
    """Anomaly detection thresholds"""
    # Current imbalance (Grundfos manual Page 7)
    current_imbalance_warning: float = 5.0    # %
    current_imbalance_critical: float = 15.0  # %
    
    # Voltage deviation (Grundfos manual Page 8)
    voltage_low_warning: float = 207.0        # V (10% below 230V)
    voltage_low_critical: float = 180.0       # V (20% below)
    voltage_high_warning: float = 253.0       # V (10% above)
    voltage_high_critical: float = 270.0      # V (20% above)
    
    # Temperature (IEC Class B)
    temperature_warning: float = 80.0         # °C
    temperature_critical: float = 90.0        # °C
    
    # Vibration (ISO 10816)
    vibration_warning: float = 5.0            # mm/s
    vibration_critical: float = 10.0          # mm/s
    
    # Pressure
    pressure_low_warning: float = 2.0         # bar
    pressure_critical: float = 0.0            # bar (dry running)


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    websocket_interval: float = 1.0    # Sensor update rate (Hz)
    max_history: int = 60              # Sensor history length
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class DigitalTwinConfig:
    """Main configuration container"""
    # Data source selection - MATLAB par défaut
    data_source: DataSource = DataSource.MATLAB
    
    # Sub-configurations
    tcp: TCPConfig = field(default_factory=TCPConfig)
    pump: PumpConfig = field(default_factory=PumpConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Paths
    stl_model_path: Optional[str] = None
    knowledge_base_path: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'DigitalTwinConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Data source - default to MATLAB unless explicitly set to python
        source = os.getenv('DT_DATA_SOURCE', 'matlab').lower()
        config.data_source = DataSource(source)
        
        # TCP settings
        config.tcp.host = os.getenv('DT_TCP_HOST', '0.0.0.0')
        config.tcp.port = int(os.getenv('DT_TCP_PORT', '5555'))
        
        # API settings
        config.api.host = os.getenv('DT_API_HOST', '0.0.0.0')
        config.api.port = int(os.getenv('DT_API_PORT', '8000'))
        
        # Paths
        config.stl_model_path = os.getenv('DT_STL_PATH')
        config.knowledge_base_path = os.getenv('DT_KB_PATH')
        
        return config
    
    @classmethod
    def from_file(cls, filepath: str) -> 'DigitalTwinConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config = cls()
        
        if 'data_source' in data:
            config.data_source = DataSource(data['data_source'])
        
        if 'tcp' in data:
            for key, value in data['tcp'].items():
                if hasattr(config.tcp, key):
                    setattr(config.tcp, key, value)
        
        if 'pump' in data:
            for key, value in data['pump'].items():
                if hasattr(config.pump, key):
                    setattr(config.pump, key, value)
        
        if 'thresholds' in data:
            for key, value in data['thresholds'].items():
                if hasattr(config.thresholds, key):
                    setattr(config.thresholds, key, value)
        
        if 'api' in data:
            for key, value in data['api'].items():
                if hasattr(config.api, key):
                    setattr(config.api, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'data_source': self.data_source.value,
            'tcp': {
                'host': self.tcp.host,
                'port': self.tcp.port,
                'buffer_size': self.tcp.buffer_size,
                'timeout': self.tcp.timeout,
            },
            'pump': {
                'model': self.pump.model,
                'nominal_flow_rate': self.pump.nominal_flow_rate,
                'nominal_pressure': self.pump.nominal_pressure,
                'motor_power': self.pump.motor_power,
                'motor_voltage': self.pump.motor_voltage,
                'motor_current': self.pump.motor_current,
                'nominal_speed': self.pump.nominal_speed,
            },
            'thresholds': {
                'current_imbalance_warning': self.thresholds.current_imbalance_warning,
                'current_imbalance_critical': self.thresholds.current_imbalance_critical,
                'voltage_low_warning': self.thresholds.voltage_low_warning,
                'temperature_warning': self.thresholds.temperature_warning,
                'vibration_warning': self.thresholds.vibration_warning,
            },
            'api': {
                'host': self.api.host,
                'port': self.api.port,
            }
        }
    
    def save(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Global configuration instance
_config: Optional[DigitalTwinConfig] = None


def get_config() -> DigitalTwinConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = DigitalTwinConfig.from_env()
    return _config


def set_config(config: DigitalTwinConfig):
    """Set the global configuration instance."""
    global _config
    _config = config


def load_config(filepath: str):
    """Load and set configuration from file."""
    global _config
    _config = DigitalTwinConfig.from_file(filepath)
    return _config

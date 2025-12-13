"""
MATLAB Bridge for Digital Twin
TCP Server that receives sensor data from MATLAB and provides
PumpSimulator-compatible interface for the existing Python stack.

This module acts as the bridge between the MATLAB physical simulation
and the Python intelligence layer (AI agent, anomaly detection).

Architecture:
    MATLAB Simulink → TCP → MATLABBridge → AI Agent / API

Author: Digital Twin Project
Date: December 2025
"""

import socket
import json
import threading
import queue
import time
from datetime import datetime
from typing import Dict, Optional, Generator, Callable
from dataclasses import dataclass, field
from enum import Enum


class ConnectionState(Enum):
    """TCP connection state"""
    DISCONNECTED = "disconnected"
    LISTENING = "listening"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MATLABBridgeConfig:
    """Configuration for MATLAB-Python bridge"""
    host: str = "0.0.0.0"  # Listen on all interfaces
    port: int = 5555
    buffer_size: int = 4096
    timeout: float = 30.0
    reconnect_delay: float = 5.0
    max_queue_size: int = 100


class MATLABBridge:
    """
    TCP Server bridge that receives sensor data from MATLAB.
    Provides an interface compatible with PumpSimulator for seamless integration.
    
    Usage:
        bridge = MATLABBridge()
        bridge.start_server()
        
        # Get readings (same interface as PumpSimulator)
        reading = bridge.get_sensor_reading()
    """
    
    def __init__(self, config: Optional[MATLABBridgeConfig] = None):
        """
        Initialize the MATLAB bridge.
        
        Args:
            config: Bridge configuration (uses defaults if None)
        """
        self.config = config or MATLABBridgeConfig()
        
        # TCP server components
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
        
        # State
        self.state = ConnectionState.DISCONNECTED
        self.running = False
        
        # Data handling
        self.data_queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.latest_reading: Optional[Dict] = None
        self.reading_lock = threading.Lock()
        
        # Statistics
        self.packets_received = 0
        self.bytes_received = 0
        self.last_receive_time: Optional[float] = None
        
        # Thread for receiving data
        self.receive_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_data_received: Optional[Callable[[Dict], None]] = None
        self.on_connection_change: Optional[Callable[[ConnectionState], None]] = None
        
        # Fault state tracking (for compatibility with PumpSimulator)
        self._fault_state = "Normal"
        self._fault_duration = 0
        
        print("🌉 MATLAB Bridge initialized")
        print(f"   TCP Server: {self.config.host}:{self.config.port}")
    
    def start_server(self) -> bool:
        """
        Start the TCP server and begin listening for MATLAB connections.
        
        Returns:
            True if server started successfully
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config.host, self.config.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)  # Allow periodic checks
            
            self.state = ConnectionState.LISTENING
            self.running = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            print(f"✅ TCP Server started on port {self.config.port}")
            print("   Waiting for MATLAB connection...")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            self.state = ConnectionState.ERROR
            return False
    
    def stop_server(self):
        """Stop the TCP server and close all connections."""
        print("🛑 Stopping MATLAB Bridge...")
        
        self.running = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        self.state = ConnectionState.DISCONNECTED
        
        print(f"   Total packets received: {self.packets_received}")
        print(f"   Total bytes received: {self.bytes_received}")
        print("👋 Bridge stopped")
    
    def _receive_loop(self):
        """Main loop for receiving data from MATLAB (runs in thread)."""
        buffer = ""
        
        while self.running:
            # Accept new connection if needed
            if self.client_socket is None and self.server_socket:
                try:
                    self.client_socket, self.client_address = self.server_socket.accept()
                    self.client_socket.settimeout(1.0)
                    self.state = ConnectionState.CONNECTED
                    
                    print(f"✅ MATLAB connected from {self.client_address}")
                    
                    if self.on_connection_change:
                        self.on_connection_change(self.state)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"⚠️  Accept error: {e}")
                    continue
            
            # Receive data from connected client
            if self.client_socket:
                try:
                    data = self.client_socket.recv(self.config.buffer_size)
                    
                    if not data:
                        # Connection closed
                        print("📴 MATLAB disconnected")
                        self._handle_disconnect()
                        continue
                    
                    self.bytes_received += len(data)
                    buffer += data.decode('utf-8')
                    
                    # Process complete messages (newline-delimited JSON)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            self._process_message(line.strip())
                            
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    print("📴 MATLAB connection reset")
                    self._handle_disconnect()
                except Exception as e:
                    if self.running:
                        print(f"⚠️  Receive error: {e}")
                    self._handle_disconnect()
    
    def _handle_disconnect(self):
        """Handle client disconnection."""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        self.client_address = None
        self.state = ConnectionState.LISTENING
        
        if self.on_connection_change:
            self.on_connection_change(self.state)
        
        print("   Waiting for reconnection...")
    
    def _process_message(self, message: str):
        """
        Process received JSON message from MATLAB.
        
        Args:
            message: JSON string containing sensor data
        """
        try:
            data = json.loads(message)
            
            # Convert MATLAB format to PumpSimulator format if needed
            reading = self._convert_to_standard_format(data)
            
            # Update latest reading (thread-safe)
            with self.reading_lock:
                self.latest_reading = reading
            
            # Add to queue (non-blocking)
            try:
                self.data_queue.put_nowait(reading)
            except queue.Full:
                # Remove oldest and add new
                try:
                    self.data_queue.get_nowait()
                except queue.Empty:
                    pass
                self.data_queue.put_nowait(reading)
            
            self.packets_received += 1
            self.last_receive_time = time.time()
            
            # Log received data periodically
            if self.packets_received % 10 == 1:
                print(f"📥 MATLAB data #{self.packets_received}: T={reading.get('temperature', '?')}°C, "
                      f"V={reading.get('vibration', '?')}mm/s, Fault={reading.get('fault_state', '?')}")
            
            # Call callback if registered
            if self.on_data_received:
                self.on_data_received(reading)
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Invalid JSON: {e}")
        except Exception as e:
            print(f"⚠️  Message processing error: {e}")
    
    def _convert_to_standard_format(self, matlab_data: Dict) -> Dict:
        """
        Convert MATLAB sensor data to standard PumpSimulator format.
        This ensures compatibility with existing AI agent and API.
        
        Args:
            matlab_data: Raw data from MATLAB
            
        Returns:
            Standardized sensor reading dictionary
        """
        # Handle both MATLAB format and already-standard format
        amperage = matlab_data.get('amperage', {})
        
        if not amperage and 'current_a' in matlab_data:
            # MATLAB sends individual current values
            phase_a = matlab_data.get('current_a', 10.0)
            phase_b = matlab_data.get('current_b', 10.0)
            phase_c = matlab_data.get('current_c', 10.0)
            avg = (phase_a + phase_b + phase_c) / 3
            max_dev = max(abs(phase_a - avg), abs(phase_b - avg), abs(phase_c - avg))
            imbalance = (max_dev / avg * 100) if avg > 0 else 0
            
            amperage = {
                "phase_a": round(phase_a, 2),
                "phase_b": round(phase_b, 2),
                "phase_c": round(phase_c, 2),
                "average": round(avg, 2),
                "imbalance_pct": round(imbalance, 2)
            }
        
        # Extract fault state
        fault_state = matlab_data.get('fault_state', 'Normal')
        self._fault_state = fault_state
        
        fault_duration = matlab_data.get('fault_duration', 0)
        if fault_state != 'Normal':
            self._fault_duration = fault_duration
        else:
            self._fault_duration = 0
        
        # Build standardized reading
        reading = {
            "timestamp": matlab_data.get('datetime', datetime.now().isoformat()),
            "amperage": amperage,
            "voltage": matlab_data.get('voltage', 230.0),
            "vibration": matlab_data.get('vibration', 1.5),
            "pressure": matlab_data.get('pressure', matlab_data.get('discharge_pressure', 5.0)),
            "temperature": matlab_data.get('temperature', 65.0),
            "fault_state": fault_state,
            "fault_duration": fault_duration,
            # Extended data from MATLAB
            "flow_rate": matlab_data.get('flow_rate', 15.0),
            "rpm": matlab_data.get('rpm', 2900),
            "power": matlab_data.get('power', 5.5),
            "torque": matlab_data.get('torque', 18.0),
            "inlet_pressure": matlab_data.get('inlet_pressure', 1.0),
            "source": "matlab"  # Identify data source
        }
        
        return reading
    
    # =========================================================================
    # PumpSimulator-Compatible Interface
    # =========================================================================
    
    def get_sensor_reading(self) -> Dict:
        """
        Get current sensor reading (compatible with PumpSimulator).
        
        Returns:
            Dictionary containing all sensor values and fault state
        """
        with self.reading_lock:
            if self.latest_reading:
                return self.latest_reading.copy()
        
        # Return default values if no data received yet
        return self._get_default_reading()
    
    def _get_default_reading(self) -> Dict:
        """
        Get default reading when no MATLAB data available.
        Applies fault effects if a fault is currently active.
        """
        import random
        
        # Get fault effects based on current state
        effects = self._get_default_effects(self._fault_state)
        
        # Base values (normal operation)
        base_voltage = 400.0  # 400V 3-phase European standard
        base_current = 10.0
        base_vibration = 1.5
        base_pressure = 5.0
        base_temperature = 65.0
        base_flow = 15.0
        
        # Apply vibration effects
        if effects.get('vibration_base', 0) > 0:
            vibration = effects['vibration_base'] + random.uniform(-0.5, 0.5)
        else:
            vibration = base_vibration * effects.get('vibration_mult', 1.0)
        
        # Apply temperature effects
        if effects.get('temp_base', 0) > 0:
            temperature = effects['temp_base'] + random.uniform(-2, 5)
        else:
            temperature = base_temperature + effects.get('temp_offset', 0)
        
        # Apply current effects with imbalance
        current_mult = effects.get('current_mult', 1.0)
        current_base_effect = effects.get('current_base', 0)
        imbalance = effects.get('current_imbalance', 0)
        
        if current_base_effect > 0:
            avg_current = current_base_effect
        else:
            avg_current = base_current * current_mult
        
        # Generate phase currents with imbalance
        if imbalance > 0:
            phase_a = avg_current * (1 + imbalance + random.uniform(-0.02, 0.02))
            phase_b = avg_current * (1 - imbalance/2 + random.uniform(-0.02, 0.02))
            phase_c = avg_current * (1 - imbalance/2 + random.uniform(-0.02, 0.02))
        else:
            phase_a = avg_current * (1 + random.uniform(-0.02, 0.02))
            phase_b = avg_current * (1 + random.uniform(-0.02, 0.02))
            phase_c = avg_current * (1 + random.uniform(-0.02, 0.02))
        
        actual_avg = (phase_a + phase_b + phase_c) / 3
        max_dev = max(abs(phase_a - actual_avg), abs(phase_b - actual_avg), abs(phase_c - actual_avg))
        imbalance_pct = (max_dev / actual_avg) * 100 if actual_avg > 0 else 0
        
        # Apply voltage variance
        voltage_variance = effects.get('voltage_variance', 0)
        voltage = base_voltage + random.uniform(-voltage_variance, voltage_variance)
        
        # Apply pressure and flow effects
        pressure = base_pressure * effects.get('pressure_mult', 1.0)
        pressure_variance = effects.get('pressure_variance', 0)
        pressure += random.uniform(-pressure_variance, pressure_variance)
        
        flow = base_flow * effects.get('flow_mult', 1.0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "amperage": {
                "phase_a": round(phase_a, 2),
                "phase_b": round(phase_b, 2),
                "phase_c": round(phase_c, 2),
                "average": round(actual_avg, 2),
                "imbalance_pct": round(imbalance_pct, 2)
            },
            "voltage": round(voltage, 1),
            "vibration": round(vibration, 2),
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 1),
            "fault_state": self._fault_state,
            "fault_duration": self._fault_duration,
            "flow_rate": round(flow, 2),
            "rpm": 2900,
            "power": round(5.5 * current_mult, 2),
            "source": "python_fallback"  # Identify this is Python fallback data
        }
    
    def stream_sensor_data(self, interval: float = 1.0) -> Generator[Dict, None, None]:
        """
        Generate continuous stream of sensor data (compatible with PumpSimulator).
        
        Args:
            interval: Minimum time between readings in seconds
            
        Yields:
            Sensor reading dictionaries
        """
        print(f"\n📡 Starting sensor data stream (interval: {interval}s)")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                # Try to get from queue first (real-time data)
                try:
                    reading = self.data_queue.get(timeout=interval)
                    yield reading
                except queue.Empty:
                    # No new data, yield latest
                    yield self.get_sensor_reading()
                    
        except KeyboardInterrupt:
            print("\n\n⏹️  Sensor stream stopped by user")
    
    @property
    def fault_state(self):
        """Current fault state (for compatibility)."""
        return self._fault_state
    
    @property
    def fault_duration(self):
        """Current fault duration (for compatibility)."""
        return self._fault_duration
    
    def inject_fault(self, fault_type, intensity: float = 1.0, scenario_effects: Dict = None):
        """
        Send fault injection command to MATLAB.
        
        This sends a JSON command to MATLAB with fault parameters.
        MATLAB should be listening for these commands to modify its simulation.
        
        Args:
            fault_type: Type of fault to inject (FaultType enum or string)
            intensity: Fault severity (0.5 to 2.0)
            scenario_effects: Optional dict of sensor effect multipliers
        """
        fault_name = str(fault_type.value) if hasattr(fault_type, 'value') else str(fault_type)
        
        # Update internal state tracking
        self._fault_state = fault_name
        self._fault_duration = 0
        
        print(f"\n⚠️  Fault injection: {fault_name}")
        
        # Build command with detailed effects for MATLAB
        command_data = {
            "command": "inject_fault",
            "fault_type": fault_name,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat(),
            # Default effects based on fault type
            "effects": scenario_effects or self._get_default_effects(fault_name)
        }
        
        # Send to MATLAB if connected
        if self.client_socket and self.state == ConnectionState.CONNECTED:
            try:
                command = json.dumps(command_data) + "\n"
                self.client_socket.send(command.encode('utf-8'))
                print(f"   ✅ Injection command sent to MATLAB: {fault_name}")
                print(f"   📤 Effects: {command_data['effects']}")
            except Exception as e:
                print(f"   ⚠️  Failed to send command to MATLAB: {e}")
                print("   ℹ️  Fault state updated locally but MATLAB may not reflect it")
        else:
            print("   ℹ️  MATLAB not connected - fault state updated locally only")
    
    def _get_default_effects(self, fault_name: str) -> Dict:
        """
        Get default sensor effects for a fault type.
        These are multipliers/offsets that MATLAB applies to sensor readings.
        """
        effects_map = {
            "Normal": {
                "vibration_mult": 1.0,
                "temp_offset": 0,
                "current_mult": 1.0,
                "pressure_mult": 1.0,
                "flow_mult": 1.0
            },
            "Winding Defect": {
                "vibration_mult": 1.3,
                "temp_offset": 25,
                "current_mult": 1.15,
                "current_imbalance": 0.12,  # 12% imbalance
                "pressure_mult": 1.0,
                "flow_mult": 0.95
            },
            "Supply Fault": {
                "vibration_mult": 1.2,
                "temp_offset": 12,
                "voltage_variance": 15,  # ±15V variance
                "current_mult": 1.1,
                "current_imbalance": 0.08,
                "pressure_mult": 0.95,
                "flow_mult": 0.92
            },
            "Cavitation": {
                "vibration_mult": 2.5,
                "vibration_base": 5.2,
                "temp_offset": 8,
                "current_mult": 1.05,
                "pressure_mult": 0.75,
                "flow_mult": 0.82,
                "pressure_variance": 0.5  # High variance
            },
            "Bearing Wear": {
                "vibration_mult": 3.0,
                "vibration_base": 7.2,
                "temp_offset": 18,
                "current_mult": 1.12,
                "pressure_mult": 0.9,
                "flow_mult": 0.88
            },
            "Overload": {
                "vibration_mult": 2.8,
                "vibration_base": 8.5,
                "temp_offset": 30,
                "temp_base": 92,
                "current_mult": 1.35,
                "current_base": 32,
                "pressure_mult": 0.7,
                "flow_mult": 0.40
            }
        }
        return effects_map.get(fault_name, effects_map["Normal"])
    
    def reset_fault(self):
        """Send fault reset command to MATLAB."""
        print("\n✅ Resetting to normal operation")
        self._fault_state = "Normal"
        self._fault_duration = 0
        
        command_data = {
            "command": "reset_fault",
            "fault_type": "Normal",
            "intensity": 1.0,
            "timestamp": datetime.now().isoformat(),
            "effects": self._get_default_effects("Normal")
        }
        
        if self.client_socket and self.state == ConnectionState.CONNECTED:
            try:
                command = json.dumps(command_data) + "\n"
                self.client_socket.send(command.encode('utf-8'))
                print("   ✅ Reset command sent to MATLAB")
            except Exception as e:
                print(f"   ⚠️  Failed to send reset command: {e}")
    
    # =========================================================================
    # Status and Diagnostics
    # =========================================================================
    
    def get_status(self) -> Dict:
        """Get bridge status information."""
        return {
            "state": self.state.value,
            "connected": self.state == ConnectionState.CONNECTED,
            "client_address": str(self.client_address) if self.client_address else None,
            "packets_received": self.packets_received,
            "bytes_received": self.bytes_received,
            "last_receive_time": self.last_receive_time,
            "queue_size": self.data_queue.qsize(),
            "has_data": self.latest_reading is not None
        }
    
    def is_connected(self) -> bool:
        """Check if MATLAB is connected."""
        return self.state == ConnectionState.CONNECTED
    
    def wait_for_connection(self, timeout: float = 60.0) -> bool:
        """
        Wait for MATLAB to connect.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if connected, False if timeout
        """
        print(f"⏳ Waiting for MATLAB connection (timeout: {timeout}s)...")
        
        start = time.time()
        while time.time() - start < timeout:
            if self.state == ConnectionState.CONNECTED:
                return True
            time.sleep(0.5)
        
        print("⚠️  Timeout waiting for MATLAB connection")
        return False


class HybridSimulator:
    """
    Hybrid simulator that can switch between Python and MATLAB sources.
    Provides unified interface regardless of data source.
    
    Usage:
        simulator = HybridSimulator(source='matlab')  # or 'python'
        reading = simulator.get_sensor_reading()
    """
    
    def __init__(self, source: str = 'python', matlab_config: Optional[MATLABBridgeConfig] = None):
        """
        Initialize hybrid simulator.
        
        Args:
            source: Data source ('python' or 'matlab')
            matlab_config: Configuration for MATLAB bridge
        """
        self.source = source.lower()
        self._matlab_bridge: Optional[MATLABBridge] = None
        self._python_simulator = None
        
        if self.source == 'matlab':
            self._matlab_bridge = MATLABBridge(matlab_config)
        else:
            # Import here to avoid circular imports
            from src.simulator import PumpSimulator
            self._python_simulator = PumpSimulator()
        
        print(f"🔀 Hybrid Simulator initialized (source: {self.source})")
    
    def start(self) -> bool:
        """Start the simulator/bridge."""
        if self.source == 'matlab' and self._matlab_bridge:
            return self._matlab_bridge.start_server()
        return True
    
    def stop(self):
        """Stop the simulator/bridge."""
        if self._matlab_bridge:
            self._matlab_bridge.stop_server()
    
    def get_sensor_reading(self) -> Dict:
        """Get current sensor reading from active source."""
        if self.source == 'matlab' and self._matlab_bridge:
            return self._matlab_bridge.get_sensor_reading()
        elif self._python_simulator:
            return self._python_simulator.get_sensor_reading()
        return {}
    
    def inject_fault(self, fault_type, intensity: float = 1.0):
        """Inject fault into active source."""
        if self.source == 'matlab' and self._matlab_bridge:
            self._matlab_bridge.inject_fault(fault_type, intensity)
        elif self._python_simulator:
            self._python_simulator.inject_fault(fault_type, intensity)
    
    def reset_fault(self):
        """Reset fault state."""
        if self.source == 'matlab' and self._matlab_bridge:
            self._matlab_bridge.reset_fault()
        elif self._python_simulator:
            self._python_simulator.reset_fault()
    
    def switch_source(self, new_source: str):
        """Switch between Python and MATLAB sources."""
        if new_source.lower() == self.source:
            return
        
        # Stop current source
        self.stop()
        
        # Switch
        self.source = new_source.lower()
        
        if self.source == 'matlab':
            if not self._matlab_bridge:
                self._matlab_bridge = MATLABBridge()
            self._matlab_bridge.start_server()
        else:
            if not self._python_simulator:
                from src.simulator import PumpSimulator
                self._python_simulator = PumpSimulator()
        
        print(f"🔀 Switched to {self.source} source")
    
    def get_status(self) -> Dict:
        """Get current status."""
        status = {
            "source": self.source,
            "active": True
        }
        
        if self.source == 'matlab' and self._matlab_bridge:
            status["matlab"] = self._matlab_bridge.get_status()
        
        return status


# =============================================================================
# Standalone Server Mode
# =============================================================================

def run_bridge_server(host: str = "0.0.0.0", port: int = 5555):
    """
    Run the MATLAB bridge as a standalone server.
    
    This can be used for testing or when running the bridge
    independently of the main API.
    
    Args:
        host: Server host
        port: Server port
    """
    print("\n" + "="*60)
    print("🌉 MATLAB BRIDGE - STANDALONE SERVER MODE")
    print("="*60 + "\n")
    
    config = MATLABBridgeConfig(host=host, port=port)
    bridge = MATLABBridge(config)
    
    # Add callback to display received data
    def on_data(data: Dict):
        print(f"\n📥 Received sensor data:")
        print(f"   Timestamp: {data.get('timestamp')}")
        print(f"   Voltage: {data.get('voltage')}V")
        print(f"   Temperature: {data.get('temperature')}°C")
        print(f"   Vibration: {data.get('vibration')} mm/s")
        print(f"   Fault State: {data.get('fault_state')}")
    
    bridge.on_data_received = on_data
    
    try:
        if bridge.start_server():
            print("\n📡 Server running. Press Ctrl+C to stop.\n")
            
            # Keep running
            while bridge.running:
                time.sleep(1)
                
                # Print periodic status
                status = bridge.get_status()
                if status['connected']:
                    print(f"   [Connected] Packets: {status['packets_received']}, "
                          f"Queue: {status['queue_size']}")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    
    finally:
        bridge.stop_server()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MATLAB-Python Bridge for Digital Twin")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5555, help="Server port (default: 5555)")
    parser.add_argument("--server", action="store_true", help="Run as standalone server")
    
    args = parser.parse_args()
    
    if args.server:
        run_bridge_server(args.host, args.port)
    else:
        # Interactive mode for testing
        print("\n" + "="*60)
        print("🌉 MATLAB BRIDGE - INTERACTIVE MODE")
        print("="*60)
        print("\nUsage:")
        print("  python -m src.matlab_bridge --server    # Run server")
        print("  python -m src.matlab_bridge --help      # Show help")
        print("\nIn MATLAB, run:")
        print("  run_simulation('port', 5555)")
        print("="*60 + "\n")

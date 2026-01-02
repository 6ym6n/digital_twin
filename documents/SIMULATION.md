# Simulation Guide

The simulator is MATLAB-based and publishes telemetry to MQTT.

## Run

- Auto-start (Windows): run `start_matlab_simulation.bat` from the repo root.
- Manual (MATLAB):

```matlab
addpath('matlab');
mqtt_digital_twin;
```

Publishes to `pump/telemetry` every ~2 seconds.

For more details, see:

- [matlab/README.md](../matlab/README.md)
- [COMPREHENSIVE_DOCUMENTATION.md](COMPREHENSIVE_DOCUMENTATION.md)

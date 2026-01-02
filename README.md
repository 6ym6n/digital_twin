# 🏭 Digital Twin for Predictive Maintenance

Real-time IoT monitoring system for **Grundfos CR Pump** with AI-powered diagnostics using RAG (Retrieval-Augmented Generation).

## 🎯 Overview

Monitor pump health through MQTT telemetry and get intelligent fault diagnostics from Google Gemini AI trained on manufacturer documentation.

**Features:**
- 🔌 Real-time MQTT telemetry from MATLAB/Simulink
- 📊 React dashboard with live charts & 3D visualization  
- 🤖 AI diagnostics with RAG (Gemini 2.5 Flash)
- 📋 Dynamic troubleshooting checklists
- 💬 Maintenance chatbot

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI + WebSocket |
| Simulation | MATLAB/Simulink (required) |
| Protocol | MQTT (Mosquitto) |
| AI/LLM | Google Gemini 2.5 Flash |
| Vector DB | ChromaDB + LangChain |

## 📁 Project Structure

```
digital_twin/
├── .env.example                   # Environment template (set GOOGLE_API_KEY)
├── backend/                       # FastAPI backend
│   ├── api.py                     # REST + WebSocket endpoints
│   └── mqtt_bridge.py             # MQTT subscriber
├── frontend/                      # React dashboard
│   ├── public/models/             # 3D assets served at /models
│   └── src/App.jsx                # Main UI component
├── src/                           # Core modules
│   ├── rag_engine.py              # Vector search engine
│   └── ai_agent.py                # Gemini AI integration
├── matlab/                        # MATLAB simulation (required)
│   └── mqtt_digital_twin.m        # Telemetry publisher
├── data/                          # Knowledge base
│   └── grundfos-cr-pump-troubleshooting.pdf
├── documents/                     # Documentation
├── start_backend.bat              # Launch scripts
├── start_frontend.bat
└── start_matlab_simulation.bat
```

## ⚡ Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+
- [Google Gemini API Key](https://makersuite.google.com/app/apikey)
- MQTT Broker (Mosquitto)
- MATLAB R2020b+ (required for simulation)

### Installation

**1. Install MQTT Broker**
```bash
# Windows
choco install mosquitto ; net start mosquitto

# macOS
brew install mosquitto ; brew services start mosquitto

# Linux
sudo apt install mosquitto ; sudo systemctl start mosquitto
```

**2. Clone & Setup**
```bash
git clone https://github.com/6ym6n/digital_twin.git
cd digital_twin

# Backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd frontend ; npm install ; cd ..

# Configure
cp .env.example .env  # Add GOOGLE_API_KEY (IMPORTANT)
```

**3. Start Services**
```bash

#In 3 Separate Terminals
.\start_backend.bat       # Terminal 1
.\start_frontend.bat      # Terminal 2  
.\start_matlab_simulation.bat  # Terminal 3 (required)

# Or manually
uvicorn backend.api:app --reload --port 8000
cd frontend ; npm run dev
# MATLAB simulation must be running
```

**4. Access**
- Dashboard: http://localhost:5173
- API: http://localhost:8000/docs

## 🎮 Usage

1. Start all services (backend, frontend, MQTT, MATLAB)
2. Open http://localhost:5173
3. View real-time sensor data
4. Click **"Diagnose"** for AI analysis
5. Use chat for maintenance questions

### MATLAB Simulation (Required)
```bash
# Windows: Auto-start
start_matlab_simulation.bat

# Manual: In MATLAB
addpath('matlab'); mqtt_digital_twin;
```
Publishes sensor data to `pump/telemetry` every 2 seconds.

## 🏗️ Architecture

```
MATLAB → MQTT → FastAPI → WebSocket → React
                    ↓
                RAG Engine → ChromaDB
                    ↓
                Gemini AI → Diagnostics
```

**Components:**
- **RAG Engine** - Semantic search in pump manual
- **AI Agent** - Gemini-powered diagnostics & chat
- **MATLAB Simulator** - 6 fault types (cavitation, bearing wear, etc.)
- **MQTT Bridge** - Telemetry relay
- **Frontend** - Real-time charts & 3D model

## 🐛 Troubleshooting

**MQTT Issues**
```bash
# Check broker
mosquitto -v

# Restart (Windows)
net stop mosquitto && net start mosquitto
```

**Frontend Not Loading**
- Verify backend: http://localhost:8000/docs
- Check browser console for errors
- Ensure MQTT broker is running

**No Data Displayed**
- Start MATLAB simulation (required)
- Check backend logs for MQTT connection
- Verify broker on localhost:1883

**Vector DB Errors**
```bash
# Rebuild ChromaDB
rm -rf chroma_db
python src/rag_engine.py
```

## 📚 Documentation

- [Installation Guide](documents/INSTALLATION.md)
- [Architecture Details](documents/PIPELINE.md)
- [Simulation Guide](documents/SIMULATION.md)
- [Presentation Deck](documents/slideready.md)
- [MATLAB Setup](matlab/README.md)

## 📄 License

Educational project for demonstration purposes.

---

**Repository:** [github.com/6ym6n/digital_twin](https://github.com/6ym6n/digital_twin)

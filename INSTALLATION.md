# 🚀 Installation Guide - Digital Twin for Predictive Maintenance

A step-by-step guide for running the RAG-Enhanced Digital Twin project.

---

## 📋 Prerequisites

Make sure you have these installed on your machine:

| Tool | Version | Download Link |
|------|---------|---------------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/downloads) |

### Verify Installation
```powershell
python --version   # Should show Python 3.10+
node --version     # Should show v18+
npm --version      # Should show 9+
git --version      # Should show git version
```

---

## 🔑 Step 1: Get Google API Key (Required)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

> ⚠️ **Keep this key private!** Never share it or commit it to Git.

---

## 📦 Step 2: Clone the Repository

```powershell
# Clone the project
git clone https://github.com/6ym6n/digital_twin.git

# Navigate to the project folder
cd digital_twin
```

---

## 🐍 Step 3: Setup Python Environment

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install Python dependencies
pip install -r requirements.txt
```

### Verify Python Installation
```powershell
python -c "import chromadb; import langchain; print('✅ All packages installed!')"
```

---

## ⚛️ Step 4: Setup Frontend (React)

```powershell
# Navigate to frontend folder
cd frontend

# Install Node.js dependencies
npm install

# Go back to project root
cd ..
```

---

## 🔐 Step 5: Configure Environment Variables

```powershell
# Copy the example environment file
Copy-Item .env.example .env
```

Now open the `.env` file and add your Google API key:

```env
GOOGLE_API_KEY=AIzaSyC...your_actual_key_here
```

> 💡 **Tip:** You can open the file with: `notepad .env`

---

## ▶️ Step 6: Run the Application

You need **2 terminals** - one for the backend, one for the frontend.

### Terminal 1 - Start Backend (FastAPI)

```powershell
# Make sure you're in the project root
cd C:\path\to\digital_twin

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the backend server
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2 - Start Frontend (React + Vite)

```powershell
# Navigate to frontend folder
cd C:\path\to\digital_twin\frontend

# Start the development server
npm run dev
```

You should see:
```
VITE v5.4.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

## 📡 Optional: Run with MQTT (External Simulator)

By default, the backend uses the built-in Python simulator. If you want to **decouple simulation from the backend** (e.g., MATLAB/Simulink publishing telemetry), you can run in MQTT mode.

### 1) Install and start a local MQTT broker (Windows)

Install Mosquitto via winget:

```powershell
winget install -e --id EclipseFoundation.Mosquitto --accept-source-agreements --accept-package-agreements
```

After installation, the **Mosquitto Broker** Windows service usually starts automatically. If needed, you can start it in Services.

### 2) (Demo) Start a fake MQTT telemetry publisher

In a terminal from the project root:

```powershell
cd C:\path\to\digital_twin
.\venv\Scripts\Activate.ps1
python tools\mqtt_fake_matlab.py
```

### 3) Start the backend in MQTT mode

In another terminal:

```powershell
cd C:\path\to\digital_twin
.\venv\Scripts\Activate.ps1

$env:SENSOR_SOURCE='mqtt'
$env:MQTT_HOST='localhost'
$env:MQTT_PORT='1883'
$env:MQTT_PUMP_ID='pump01'
$env:MQTT_BASE_TOPIC='digital_twin'

python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

At this point, the frontend works unchanged: live sensor data streams from MQTT, and fault injection / emergency-stop publish MQTT commands.

---

## 🌐 Step 7: Open the Dashboard

Open your browser and go to:

### 👉 **http://localhost:3000**

You should see the Digital Twin Dashboard with:
- ✅ Live sensor data (updating every second)
- ✅ 3-phase current chart
- ✅ Fault injection buttons
- ✅ AI diagnostic panel
- ✅ Chat interface

---

## 🛠️ Troubleshooting

### ❌ "GOOGLE_API_KEY not found"
- Make sure `.env` file exists in the project root
- Check that the key is correct and not expired

### ❌ "vite is not recognized as a command"
```powershell
cd frontend
npm install
```

### ❌ "Module not found" errors
```powershell
# Reinstall Python dependencies
pip install -r requirements.txt --force-reinstall
```

### ❌ Frontend shows "Disconnected"
- Make sure the backend is running on port 8000
- Check the backend terminal for errors

### ❌ Execution Policy Error (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📁 Project Structure

```
digital_twin/
├── backend/
│   └── api.py              # FastAPI server (REST + WebSocket)
├── frontend/
│   ├── src/
│   │   └── App.jsx         # React dashboard
│   └── package.json        # Node.js dependencies
├── src/
│   ├── rag_engine.py       # RAG with ChromaDB
│   ├── simulator.py        # IoT pump simulator
│   └── ai_agent.py         # Gemini AI integration
├── data/
│   └── grundfos-cr-pump-troubleshooting.pdf
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── .env                   # Your API key (DO NOT COMMIT)
```

---

## 🎮 How to Use

1. **View Live Data** - Watch sensor readings update in real-time
2. **Inject Faults** - Click fault buttons to simulate problems:
   - ⚡ Supply Fault
   - 🔥 Winding Defect
   - 💨 Cavitation
   - ⚙️ Bearing Wear
   - 📈 Overload
3. **Get Diagnosis** - AI analyzes sensor data and provides recommendations
4. **Chat with AI** - Ask questions about pump maintenance

---

## 👥 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Make sure both terminals are running without errors
3. Try restarting both servers

---

## 🔧 Quick Start Commands (Copy-Paste)

### First Time Setup:
```powershell
git clone https://github.com/6ym6n/digital_twin.git
cd digital_twin
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend
npm install
cd ..
Copy-Item .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Start Backend:
```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend (new terminal):
```powershell
cd frontend
npm run dev
```

### Open Dashboard:
👉 **http://localhost:3000**

---

Made with ❤️ for Industrial IoT & AI-Powered Maintenance

# 🏭 RAG-Enhanced Digital Twin for Predictive Maintenance

A real-time IoT digital twin combining sensor simulation, anomaly detection, and AI-powered diagnostics using RAG (Retrieval-Augmented Generation).

## 🎯 Project Overview

This system simulates a **Grundfos CR Pump** with real-time sensor monitoring and uses Google Gemini AI to provide intelligent fault diagnostics based on manufacturer documentation.

### Key Features
- 📊 **Real-time IoT Simulation** - Physics-based pump sensor behavior
- 🔍 **Anomaly Detection** - Threshold-based monitoring with progressive faults
- 🤖 **AI Diagnostics** - RAG-powered chatbot using Gemini 1.5 Flash
- 📈 **Live Dashboard** - Streamlit-based interactive visualization
- 📚 **Knowledge Base** - Retrieval from Grundfos CR pump manual

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **UI Framework** | Streamlit | 1.31.0 |
| **LLM Provider** | Google Gemini API | - |
| **Model** | gemini-1.5-flash | Latest |
| **Embeddings** | text-embedding-004 | Latest |
| **Vector DB** | ChromaDB | 0.4.22 |
| **Orchestration** | LangChain | 0.1.10 |
| **PDF Processing** | PyPDFLoader (pypdf) | 4.0.1 |
| **Visualization** | Plotly | 5.18.0 |

---

## 📁 Project Structure

```
digital_twin/
├── app.py                      # Main Streamlit application (Step 5)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (DO NOT COMMIT)
├── .env.example               # Template for environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── test_rag_quality.py        # RAG retrieval quality testing suite
│
├── data/                      # Knowledge base documents
│   └── grundfos-cr-pump-troubleshooting.pdf
│
├── src/                       # Source modules
│   ├── __init__.py
│   ├── rag_engine.py          # RAG & vector store logic (Step 2)
│   ├── simulator.py           # IoT pump simulator (Step 3)
│   └── ai_agent.py            # Gemini AI integration (Step 4)
│
└── chroma_db/                 # ChromaDB persistence (auto-created)
    └── [vector database files]
```

---

## 🚀 Complete Setup Guide

### Step 1: Get Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"** (or "Get API Key")
4. Copy the generated key (starts with `AIza...`)

### Step 2: Clone & Configure Environment

```powershell
# Clone the repository
git clone https://github.com/6ym6n/digital_twin.git
cd digital_twin

# Copy the example environment file
Copy-Item .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=AIzaSyC...your_actual_key_here
```

### Step 3: Install Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all packages
pip install -r requirements.txt

# Verify ChromaDB installation
python -c "import chromadb; print('ChromaDB version:', chromadb.__version__)"
```

### Step 4: Run Component Tests

#### Test RAG Engine:
```powershell
# Basic test - loads PDF and creates vector store
python src/rag_engine.py

# Advanced quality testing
python test_rag_quality.py
```

#### Test IoT Simulator:
```powershell
# Runs through all 6 fault scenarios
python src/simulator.py
```

#### Test AI Agent:
```powershell
# Tests auto-diagnostic and chat modes
python src/ai_agent.py
```

### Step 5: Launch the Application

```powershell
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## 📚 Detailed Implementation Guide

### 🟢 STEP 1: Project Structure & Dependencies ✅

**Objective:** Establish professional project foundation with proper configuration management.

#### What Was Created:
1. **`requirements.txt`** - Complete dependency manifest:
   - Streamlit for UI framework
   - LangChain + Google Generative AI for LLM integration
   - ChromaDB for vector storage
   - PyPDF for document processing
   - Plotly for data visualization
   - python-dotenv for environment management

2. **`.env.example`** - Template for API key configuration
   - Provides clear instructions for obtaining Google API key
   - Ensures sensitive credentials aren't committed to version control

3. **`.gitignore`** - Protection rules:
   - Excludes `.env` file (API keys)
   - Excludes `chroma_db/` (local vector database)
   - Standard Python build artifacts
   - IDE configurations

4. **Project Directory Structure:**
   ```
   digital_twin/
   ├── data/                   # Knowledge base storage
   ├── src/                    # Source code modules
   └── chroma_db/             # Vector database (auto-created)
   ```

#### Key Decisions:
- **Google Gemini over OpenAI:** Lower latency with `gemini-1.5-flash`
- **ChromaDB over Pinecone/Weaviate:** Local-first, no external dependencies
- **Streamlit over Flask/FastAPI:** Rapid prototyping, built-in state management

---

### 🟢 STEP 2: RAG Engine (Knowledge Base) ✅

**Objective:** Build retrieval system to query pump troubleshooting manual.

#### Implementation Details (`src/rag_engine.py`):

```python
class RAGEngine:
    """Manages PDF loading, embedding, and semantic retrieval"""
```

**Core Components:**

1. **PDF Loading & Chunking:**
   ```python
   loader = PyPDFLoader("data/grundfos-cr-pump-troubleshooting.pdf")
   documents = loader.load()
   
   text_splitter = RecursiveCharacterTextSplitter(
       chunk_size=1000,      # Optimal for context window
       chunk_overlap=200,    # Prevents info loss at boundaries
       separators=["\n\n", "\n", " ", ""]
   )
   chunks = text_splitter.split_documents(documents)
   ```

2. **Embeddings Generation:**
   ```python
   embeddings = GoogleGenerativeAIEmbeddings(
       model="models/text-embedding-004",  # Latest Google embedding model
       google_api_key=os.getenv("GOOGLE_API_KEY")
   )
   ```

3. **Vector Store (ChromaDB):**
   ```python
   vector_store = Chroma.from_documents(
       documents=chunks,
       embedding=embeddings,
       persist_directory="./chroma_db",
       collection_name="pump_manual"
   )
   ```

4. **Retrieval Function:**
   ```python
   def query_knowledge_base(query: str, top_k: int = 3):
       """Returns top-3 most relevant chunks with scores"""
       results = self.vector_store.similarity_search_with_score(
           query=query, k=top_k
       )
       return formatted_results
   ```

#### Key Features:
- ✅ **Persistent Storage** - Vector DB saved to disk, loads instantly on restart
- ✅ **Automatic Indexing** - Creates embeddings on first run, reuses thereafter
- ✅ **Metadata Preservation** - Tracks source page numbers for citations
- ✅ **Similarity Scoring** - Returns relevance scores for transparency

#### Testing (`test_rag_quality.py`):
Created comprehensive test suite with 5 testing modes:
1. **Fault Diagnosis Scenarios** - Real-world pump failures
2. **Specific Technical Queries** - Maintenance procedures
3. **Context Formatting** - LLM prompt preparation
4. **Edge Cases** - Irrelevant query handling
5. **Retrieval Strategy Comparison** - Top-1 vs Top-3 vs Top-5

**Run Test:**
```powershell
python test_rag_quality.py
# Interactive menu for testing retrieval quality
```

---

### 🟢 STEP 3: IoT Simulator (Physics Engine) ✅

**Objective:** Create realistic pump sensor simulation with fault injection.

#### Implementation Details (`src/simulator.py`):

```python
class PumpSimulator:
    """Physics-based Grundfos CR Pump simulator"""
```

**Sensor Array:**

| Sensor | Normal Range | Fault Indicators | Source |
|--------|-------------|------------------|--------|
| **Amperage (3-Phase)** | 10A ±2% | >5% imbalance | PDF Page 8 |
| **Voltage** | 230V ±2% | <207V (10% drop) | PDF Page 9 |
| **Vibration** | <2 mm/s | >5 mm/s spikes | PDF Page 6 |
| **Pressure** | 5 bar ±5% | Fluctuations | Cavitation logic |
| **Temperature** | 65°C ±3°C | >80°C overheating | Winding defect |

**Fault Injection System:**

```python
class FaultType(Enum):
    NORMAL = "Normal"
    WINDING_DEFECT = "Winding Defect"      # Phase imbalance + heat
    SUPPLY_FAULT = "Supply Fault"          # Voltage drop
    CAVITATION = "Cavitation"              # High vibration + pressure swings
    BEARING_WEAR = "Bearing Wear"          # Progressive vibration increase
    OVERLOAD = "Overload"                  # Elevated current + temp
```

**Progressive Fault Logic:**
```python
# Faults worsen over time (realistic behavior)
imbalance = 0.05 + (self.fault_duration * 0.01)  # Start 5%, increases
imbalance = min(imbalance, 0.25)  # Cap at 25%
```

**Data Output Format:**
```json
{
    "timestamp": "2025-11-26T14:30:15",
    "amperage": {
        "phase_a": 10.2,
        "phase_b": 10.1,
        "phase_c": 13.5,
        "average": 11.3,
        "imbalance_pct": 19.5
    },
    "voltage": 228.5,
    "vibration": 1.6,
    "pressure": 4.95,
    "temperature": 67.2,
    "fault_state": "Winding Defect",
    "fault_duration": 12
}
```

**Streaming Mode:**
```python
# Continuous data generation (for dashboard)
for reading in pump.stream_sensor_data(interval=1.0):
    # Yields sensor data every 1 second
    process_reading(reading)
```

#### Key Features:
- ✅ **Physics-Based** - Realistic sensor correlations (e.g., high current → heat)
- ✅ **Progressive Faults** - Defects worsen gradually, not instantly
- ✅ **Random Variations** - Mimics real sensor noise
- ✅ **Manual Page References** - Logic traced to PDF troubleshooting guide
- ✅ **Easy Testing** - Built-in test mode cycles through all faults

**Run Test:**
```powershell
python src/simulator.py
# Demonstrates all 6 fault scenarios with sensor readings
```

---

### 🟢 STEP 4: AI Agent (Gemini Integration) ✅

**Objective:** Integrate Google Gemini for intelligent diagnostics combining RAG with real-time sensor analysis.

#### Implementation Details (`src/ai_agent.py`):

```python
class MaintenanceAIAgent:
    """AI-powered diagnostic agent for pump troubleshooting"""
```

**Core Architecture:**

1. **LLM Initialization:**
   ```python
   llm = ChatGoogleGenerativeAI(
       model="gemini-1.5-flash",     # Low latency model
       temperature=0.3,               # Focused, consistent responses
       max_output_tokens=500,         # Concise for dashboard
       convert_system_message_to_human=True  # Gemini compatibility
   )
   ```

2. **System Prompt (Senior Engineer Persona):**
   ```
   You are a Senior Maintenance Engineer specialized in Grundfos CR 
   centrifugal pumps with 15+ years of experience...
   
   Responsibilities:
   - Analyze sensor data to identify root causes
   - Provide actionable diagnostic steps
   - Recommend specific tools and measurements
   - Prioritize safety and equipment protection
   
   Response Structure: DIAGNOSIS → ROOT CAUSE → ACTION ITEMS
   ```

3. **Intelligent RAG Query Construction:**
   ```python
   def _build_diagnostic_query(sensor_data):
       # Automatically builds query based on sensor anomalies
       if imbalance > 5%: query += "motor winding defect phase imbalance"
       if voltage < 207V: query += "voltage supply fault"
       if vibration > 5: query += "cavitation high vibration"
       # Returns optimized query for retrieval
   ```

4. **Sensor Data Formatting:**
   ```python
   # Converts simulator output to structured text for LLM
   """
   Current Sensor Readings:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   • FAULT STATE: Winding Defect
   • ELECTRICAL:
     - Phase A: 10.2A, Phase B: 10.1A, Phase C: 13.5A
     - Imbalance: 19.5%
     - Voltage: 228.5V
   • MECHANICAL:
     - Vibration: 1.6 mm/s
     - Pressure: 4.95 bar
   • THERMAL:
     - Temperature: 82.5°C
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   """
   ```

**Two Operating Modes:**

**A. Auto-Diagnostic Mode** (Fault Detection):
```python
result = agent.get_diagnostic(sensor_data)
# Returns:
{
    "diagnosis": "PRIMARY DIAGNOSIS: Motor winding defect...",
    "context_used": [...],  # Retrieved manual pages
    "rag_query": "motor winding defect phase imbalance",
    "fault_detected": True,
    "sensor_summary": {...}
}
```

**B. Chat Mode** (User Questions):
```python
answer = agent.ask_question(
    "What tools do I need to inspect the impeller?",
    sensor_data=current_reading
)
# Returns context-aware answer with manual references
```

**Integration Flow:**
```
Sensor Data → AI Agent → RAG Query → Vector Search → Context Retrieval
                ↓                                          ↓
            Format Prompt ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
                ↓
         Gemini LLM (gemini-1.5-flash)
                ↓
         Diagnostic Response
```

#### Key Features:
- ✅ **Context-Aware** - Combines real-time sensor data with historical documentation
- ✅ **Intelligent Retrieval** - Automatically constructs optimal RAG queries based on anomalies
- ✅ **Dual Mode** - Auto-diagnostic for faults + chat for user questions
- ✅ **Structured Output** - Diagnosis → Root Cause → Action Items
- ✅ **Safety-First** - Recommends immediate actions for critical conditions
- ✅ **Dashboard-Optimized** - Concise responses (300 words max)

#### Response Example:
```
PRIMARY DIAGNOSIS: Motor winding defect detected in Phase C

ROOT CAUSE: 
The 19.5% current imbalance indicates a potential short circuit or 
insulation breakdown in Phase C winding. This is significantly above 
the 5% threshold specified in the manual (Page 8).

IMMEDIATE ACTIONS:
1. STOP THE PUMP - Continuing operation risks complete motor failure
2. Measure winding resistance using a megohmmeter
3. Check for ground faults between windings and motor frame
4. Inspect for signs of overheating or burning smell

VERIFICATION STEPS:
- Compare resistance readings across all three phases
- Normal: <5% variance between phases
- Failed winding: >20% variance or infinite resistance
```

**Run Test:**
```powershell
python src/ai_agent.py
# Cycles through fault scenarios with AI diagnostics
# Tests both auto-diagnostic and chat modes
```

---

### � STEP 5: Streamlit Dashboard - PENDING

**Objective:** Create interactive real-time dashboard.

#### Planned Layout:
```
┌─────────────────────────────────────┬──────────────────────┐
│  DIGITAL TWIN MONITOR (70%)        │  AI ASSISTANT (30%) │
│                                     │                      │
│  [Metrics: Amps, Voltage, Vib]     │  💬 Chat Interface   │
│  [Real-time Plotly Chart]          │  Auto-diagnosis on   │
│  [Fault Injection Buttons]         │  fault detection     │
└─────────────────────────────────────┴──────────────────────┘
```

**Status:** � Not yet implemented

---

## 🔧 Usage Examples

### RAG Engine:
```python
from src.rag_engine import RAGEngine

rag = RAGEngine()

# Query the manual
results = rag.query_knowledge_base("motor overheating causes")
for r in results:
    print(f"Page {r['page']}: {r['content'][:100]}...")

# Get formatted context for LLM
context = rag.get_context_for_prompt("voltage imbalance diagnosis")
```

### IoT Simulator:
```python
from src.simulator import PumpSimulator, FaultType

pump = PumpSimulator()

# Normal operation
data = pump.get_sensor_reading()
print(data)

# Inject fault
pump.inject_fault(FaultType.CAVITATION)
data = pump.get_sensor_reading()  # Shows high vibration

# Continuous stream
for reading in pump.stream_sensor_data(interval=1.0):
    if reading['vibration'] > 5.0:
        print("⚠️ CAVITATION DETECTED!")
```

### AI Agent:
```python
from src.ai_agent import MaintenanceAIAgent
from src.simulator import PumpSimulator, FaultType

# Initialize
agent = MaintenanceAIAgent()
pump = PumpSimulator()

# Auto-diagnostic mode
pump.inject_fault(FaultType.WINDING_DEFECT)
sensor_data = pump.get_sensor_reading()
result = agent.get_diagnostic(sensor_data)
print(result['diagnosis'])

# Chat mode
answer = agent.ask_question(
    "How do I measure voltage imbalance?",
    sensor_data=sensor_data
)
print(answer)
```

---

## 🏗️ Development Progress

| Phase | Status | Description |
|-------|--------|-------------|
| **Step 1** | ✅ Complete | Project structure, dependencies, configuration |
| **Step 2** | ✅ Complete | RAG engine with ChromaDB and embeddings |
| **Step 3** | ✅ Complete | Physics-based IoT simulator with 6 fault modes |
| **Step 4** | ✅ Complete | AI agent with Gemini 1.5 Flash integration |
| **Step 5** | 🔴 Pending | Streamlit dashboard with real-time visualization |

---

## 📊 Testing & Validation

### RAG Quality Assurance:
```powershell
python test_rag_quality.py
```
- Tests retrieval relevance for fault scenarios
- Validates context quality for LLM prompts
- Checks edge case handling

### Simulator Validation:
```powershell
python src/simulator.py
```
- Cycles through 6 fault scenarios
- Validates sensor correlations (e.g., winding defect → heat + imbalance)
- Demonstrates progressive fault behavior

---

## 🔐 Security Notes

- ✅ `.env` file is excluded from version control
- ✅ API keys never hardcoded in source files
- ✅ `chroma_db/` directory excluded from Git (local only)
- ⚠️ **Never commit your `.env` file to GitHub**
- ⚠️ If API key is exposed, regenerate immediately at [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🐛 Troubleshooting

### RAG Engine Issues:
```powershell
# If vector store is corrupted
python -c "from src.rag_engine import RAGEngine; RAGEngine().rebuild_index()"
```

### Import Errors:
```powershell
# Verify all packages installed
pip list | Select-String "streamlit|langchain|chromadb"
```

### ChromaDB Errors:
```powershell
# Delete and recreate vector store
Remove-Item -Recurse -Force chroma_db
python src/rag_engine.py
```

---

## 📄 License

This is an educational project for demonstration purposes.

---

## 👨‍💻 Author

Built by a Senior AI & IoT Engineer  
**Repository:** [github.com/6ym6n/digital_twin](https://github.com/6ym6n/digital_twin)

---

## 📅 Project Timeline

- **2025-11-26:** Project initialization
  - ✅ Steps 1-3: Foundation, RAG, Simulator
  - ✅ Step 4: AI Agent with Gemini
- **Next:** Streamlit dashboard (Step 5)

# 🏭 RAG-Enhanced Digital Twin for Predictive Maintenance

A real-time IoT digital twin combining sensor simulation, anomaly detection, and AI-powered diagnostics using RAG (Retrieval-Augmented Generation).

## 🎯 Project Overview

This system simulates a **Grundfos CR Pump** with real-time sensor monitoring and uses Google Gemini AI to provide intelligent fault diagnostics based on manufacturer documentation.

### Key Features
- 📊 **Real-time IoT Simulation** - Mimics pump sensor behavior
- 🔍 **Anomaly Detection** - Threshold-based monitoring
- 🤖 **AI Diagnostics** - RAG-powered chatbot for troubleshooting
- 📈 **Live Dashboard** - Streamlit-based visualization

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **UI Framework** | Streamlit |
| **LLM Provider** | Google Gemini API |
| **Model** | gemini-1.5-flash |
| **Embeddings** | text-embedding-004 |
| **Vector DB** | ChromaDB |
| **Orchestration** | LangChain |
| **PDF Processing** | PyPDFLoader |

## 📁 Project Structure

```
digital_twin/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── data/                  # Knowledge base documents
│   └── grundfos-cr-pump-troubleshooting.pdf
├── src/                   # Source modules
│   ├── __init__.py
│   ├── rag_engine.py      # RAG & vector store logic
│   ├── simulator.py       # IoT pump simulator
│   └── ai_agent.py        # Gemini AI integration
└── chroma_db/             # ChromaDB persistence (auto-created)
```

## 🚀 Setup Instructions

### 1. Get Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

### 2. Configure Environment

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 4. Run the Application

```powershell
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📚 Knowledge Base

Place your pump troubleshooting manual in the `data/` folder:
- `data/grundfos-cr-pump-troubleshooting.pdf`

The RAG engine will automatically:
1. Extract and chunk the PDF content
2. Generate embeddings using Google's text-embedding-004
3. Store vectors in ChromaDB for fast retrieval

## 🔧 Usage

1. **Monitor Live Metrics** - View real-time sensor readings
2. **Simulate Faults** - Click buttons to trigger anomalies:
   - Winding Defect (Amperage imbalance)
   - Supply Fault (Voltage drop)
   - Cavitation (Vibration spike)
3. **AI Diagnostics** - Automatic fault analysis when errors occur
4. **Ask Questions** - Chat with AI about maintenance procedures

## 🏗️ Development Phases

- [x] **Phase 1:** Project structure & dependencies
- [ ] **Phase 2:** RAG engine implementation
- [ ] **Phase 3:** IoT simulator
- [ ] **Phase 4:** AI agent integration
- [ ] **Phase 5:** Streamlit dashboard

## 📄 License

This is an educational project for demonstration purposes.

## 👨‍💻 Author

Built by a Senior AI & IoT Engineer

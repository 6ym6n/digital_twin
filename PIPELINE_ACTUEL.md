# 🔄 Pipeline d'Exécution Actuel - Digital Twin Grundfos CR 15

> **Document technique décrivant le flux d'exécution réel du système**  
> Dernière mise à jour : 13 Décembre 2025

---

## 📊 Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DIGITAL TWIN SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐    │
│  │   FRONTEND   │◄───►│   BACKEND    │◄───►│      AI + RAG ENGINE     │    │
│  │  React/Vite  │     │   FastAPI    │     │  Gemini + ChromaDB       │    │
│  │  Port 3001   │     │  Port 8000   │     │  (41 docs du manuel)     │    │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘    │
│         │                    │                         │                    │
│         │                    ▼                         │                    │
│         │            ┌──────────────┐                  │                    │
│         │            │  SIMULATOR   │                  │                    │
│         │            │ Python/MATLAB│                  │                    │
│         │            └──────────────┘                  │                    │
│         │                    │                         │                    │
│         └────────────────────┴─────────────────────────┘                    │
│                              │                                              │
│                              ▼                                              │
│                    ┌──────────────────┐                                     │
│                    │   PDF GRUNDFOS   │                                     │
│                    │  (Manuel CR 15)  │                                     │
│                    └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Séquence de Démarrage

### Étape 1 : Lancement du Backend (`python backend/api.py`)

```
1. Chargement des variables d'environnement (.env)
   └── GOOGLE_API_KEY pour Gemini

2. Initialisation du Simulateur
   ├── Mode PYTHON : PumpSimulator (simulation locale)
   └── Mode MATLAB : HybridSimulator + MATLABBridge (TCP port 5555)

3. Initialisation de l'Agent IA
   ├── Connexion à Google Gemini (gemini-2.5-flash)
   ├── Chargement du RAG Engine
   │   ├── Google Generative AI Embeddings
   │   └── ChromaDB Vector Store (41 documents)
   └── Configuration : Temperature=0.3, MaxTokens=1000000

4. Démarrage du serveur FastAPI
   └── Uvicorn sur http://0.0.0.0:8000
```

### Étape 2 : Lancement du Frontend (`npm run dev`)

```
1. Vite compile les fichiers React
2. Serveur de développement sur http://localhost:3001
3. Proxy configuré vers le backend (port 8000)
```

---

## 🔁 Pipeline en Temps Réel (WebSocket)

### Flux Principal : Streaming des Données Capteurs

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│   FRONTEND  │                    │   BACKEND   │                    │  SIMULATOR  │
│   App.jsx   │                    │   api.py    │                    │ simulator.py│
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                  │                                  │
       │ 1. WebSocket Connect             │                                  │
       │ ─────────────────────────────────►                                  │
       │    ws://localhost:8000/ws        │                                  │
       │                                  │                                  │
       │                                  │ 2. Toutes les 1 seconde          │
       │                                  │ ─────────────────────────────────►
       │                                  │    get_sensor_data()             │
       │                                  │                                  │
       │                                  │ 3. Données capteurs              │
       │                                  │ ◄─────────────────────────────────
       │                                  │    {flow_rate, pressure,         │
       │                                  │     temperature, vibration,      │
       │                                  │     power, rpm, current}         │
       │                                  │                                  │
       │ 4. JSON broadcast                │                                  │
       │ ◄─────────────────────────────────                                  │
       │    sensor_data + timestamp       │                                  │
       │                                  │                                  │
       ▼                                  │                                  │
  Mise à jour UI                          │                                  │
  - Jauges temps réel                     │                                  │
  - Graphiques historiques                │                                  │
  - Modèle 3D                             │                                  │
```

### Structure des Données Capteurs

```json
{
  "timestamp": "2025-12-13T14:30:00.000Z",
  "sensor_data": {
    "flow_rate": 15.2,        // m³/h
    "pressure": 4.8,          // bar
    "temperature": 45.3,      // °C
    "vibration": 2.1,         // mm/s
    "power": 5.5,             // kW
    "rpm": 2950,              // tr/min
    "current": 12.3           // A
  },
  "pump_state": "RUNNING",
  "active_fault": "NORMAL",
  "data_source": "PYTHON"
}
```

---

## ⚠️ Pipeline d'Injection de Panne

### Séquence Complète

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FRONTEND   │     │   BACKEND    │     │  SIMULATOR   │     │   AI AGENT   │
│ FaultControl │     │    api.py    │     │ simulator.py │     │ ai_agent.py  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │ 1. POST /api/inject-fault               │                    │
       │    {"fault_type": "CAVITATION"}         │                    │
       │ ───────────────────►                    │                    │
       │                    │                    │                    │
       │                    │ 2. inject_fault()  │                    │
       │                    │ ───────────────────►                    │
       │                    │    CAVITATION      │                    │
       │                    │                    │                    │
       │                    │ 3. Modification paramètres              │
       │                    │    ◄───────────────                     │
       │                    │    flow: -30%                           │
       │                    │    vibration: +50%                      │
       │                    │    pressure: -20%                       │
       │                    │                    │                    │
       │ 4. {"status": "ok"}│                    │                    │
       │ ◄───────────────────                    │                    │
       │                    │                    │                    │
       │                    │ 5. WebSocket: nouvelles données         │
       │ ◄═══════════════════════════════════════                    │
       │    (valeurs anormales)                  │                    │
       │                    │                    │                    │
```

### Types de Pannes Disponibles

| ID | Nom | Effets sur les Capteurs |
|----|-----|------------------------|
| `CAVITATION` | Cavitation | ↓ Flow -30%, ↑ Vibration +50%, ↓ Pressure -20% |
| `BEARING_FAILURE` | Défaillance Roulement | ↑ Vibration +100%, ↑ Temperature +30°C |
| `SEAL_LEAK` | Fuite Joint | ↓ Pressure -40%, ↓ Flow -20% |
| `IMPELLER_DAMAGE` | Dommage Impeller | ↓ Flow -50%, ↑ Power +20% |
| `OVERLOAD` | Surcharge Moteur | ↑ Current +40%, ↑ Power +35%, ↑ Temp +25°C |
| `BLOCKAGE` | Blocage | ↓ Flow -70%, ↑ Pressure +50% |

---

## 🤖 Pipeline de Diagnostic IA

### Flux de Diagnostic

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FRONTEND   │     │   BACKEND    │     │   AI AGENT   │     │  RAG ENGINE  │
│DiagnosisPanel│     │    api.py    │     │ ai_agent.py  │     │rag_engine.py │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │ 1. POST /api/diagnose                   │                    │
       │    {sensor_data: {...}}                 │                    │
       │ ───────────────────►                    │                    │
       │                    │                    │                    │
       │                    │ 2. get_diagnostic()│                    │
       │                    │ ───────────────────►                    │
       │                    │                    │                    │
       │                    │                    │ 3. RAG Query       │
       │                    │                    │ ───────────────────►
       │                    │                    │ "cavitation symptoms│
       │                    │                    │  troubleshooting"  │
       │                    │                    │                    │
       │                    │                    │ 4. Chunks du manuel│
       │                    │                    │ ◄───────────────────
       │                    │                    │ (Pages 3, 5, 6)    │
       │                    │                    │                    │
       │                    │                    │ 5. Prompt Gemini   │
       │                    │                    │ ───────────────────►
       │                    │                    │ [Sensor Data +     │
       │                    │                    │  Manual Context]   │
       │                    │                    │                    │
       │                    │                    │ 6. Réponse structurée
       │                    │                    │ ◄───────────────────
       │                    │                    │                    │
       │                    │ 7. Diagnostic JSON │                    │
       │                    │ ◄───────────────────                    │
       │                    │                    │                    │
       │ 8. Affichage       │                    │                    │
       │ ◄───────────────────                    │                    │
       │ - Diagnosis        │                    │                    │
       │ - Root Cause       │                    │                    │
       │ - Action Items     │                    │                    │
       │ - Manual Refs      │                    │                    │
```

### Structure de la Réponse Diagnostic

```json
{
  "diagnosis": "Cavitation détectée - Formation de bulles de vapeur",
  "detected_scenario": "CAVITATION",
  "confidence": 0.85,
  "shutdown_decision": {
    "should_shutdown": false,
    "urgency": "MEDIUM",
    "reason": "Cavitation peut endommager l'impeller à long terme"
  },
  "manual_references": ["Page 5", "Page 6"],
  "recommended_actions": [
    "Vérifier le niveau NPSH disponible",
    "Inspecter la ligne d'aspiration"
  ]
}
```

---

## 📖 Pipeline du Guide Manuel (RAG)

### Flux de Requête Manuel

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FRONTEND   │     │   BACKEND    │     │  RAG ENGINE  │     │   CHROMADB   │
│FaultTreeDiag │     │    api.py    │     │rag_engine.py │     │  (41 docs)   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │ 1. GET /api/manual-guide/CAVITATION     │                    │
       │ ───────────────────►                    │                    │
       │                    │                    │                    │
       │                    │ 2. Build RAG Query │                    │
       │                    │    "cavitation symptoms causes          │
       │                    │     troubleshooting corrective actions" │
       │                    │                    │                    │
       │                    │ 3. query_knowledge_base()               │
       │                    │ ───────────────────►                    │
       │                    │                    │                    │
       │                    │                    │ 4. Vector Search   │
       │                    │                    │ ───────────────────►
       │                    │                    │ Embedding → Cosine │
       │                    │                    │    Similarity      │
       │                    │                    │                    │
       │                    │                    │ 5. Top 5 Chunks    │
       │                    │                    │ ◄───────────────────
       │                    │                    │                    │
       │                    │ 6. Raw Manual Text │                    │
       │                    │ ◄───────────────────                    │
       │                    │                    │                    │
       │ 7. Display         │                    │                    │
       │ ◄───────────────────                    │                    │
       │ - manual_content   │                    │                    │
       │ - manual_references│                    │                    │
       │ - query_used       │                    │                    │
```

### Exemple de Réponse RAG

```json
{
  "id": "CAVITATION",
  "name": "🟠 Cavitation",
  "severity": 2,
  "description": "Information retrieved from Grundfos manual for: Cavitation",
  "query_used": "cavitation symptoms causes troubleshooting corrective actions",
  "manual_content": "Pump is cavitating\nTurn the pump off, close the isolation valve(s), and remove the priming plug.\nCheck the level of the water within the pump...\n\nInstall a compound gauge on the suction port's pressure tap...",
  "manual_references": ["Page 5", "Page 3", "Page 2"]
}
```

---

## 🎨 Pipeline de Rendu Frontend

### Composants Principaux

```
App.jsx
├── Header
│   └── Titre + Status connexion
│
├── MainContent
│   ├── PumpViewer3D.jsx ──────────► Modèle 3D (Three.js/React Three Fiber)
│   │   └── Couleurs selon état :
│   │       - Vert : Normal
│   │       - Jaune : Attention
│   │       - Rouge : Critique
│   │
│   ├── SensorGauges ──────────────► Jauges en temps réel
│   │   ├── Flow Rate (m³/h)
│   │   ├── Pressure (bar)
│   │   ├── Temperature (°C)
│   │   ├── Vibration (mm/s)
│   │   ├── Power (kW)
│   │   └── Current (A)
│   │
│   └── HistoryChart ──────────────► Graphiques (dernières 60 sec)
│
├── ControlPanel
│   ├── FaultControl ──────────────► Injection de pannes
│   │   └── Boutons pour chaque type de panne
│   │
│   └── DataSourceToggle ──────────► Python / MATLAB
│
├── DiagnosisPanel ────────────────► Analyse IA
│   ├── Section Diagnosis (cyan)
│   ├── Section Root Cause (orange)
│   ├── Section Action Items (vert)
│   └── Section Manual Refs (bleu)
│
└── FaultTreeDiagram.jsx ──────────► Guide Manuel (RAG)
    ├── Query RAG affichée
    ├── Contenu du manuel formaté
    └── Références aux pages
```

---

## 📁 Fichiers Clés et Leurs Rôles

| Fichier | Rôle | Pipeline |
|---------|------|----------|
| `backend/api.py` | API REST + WebSocket | Tous |
| `src/simulator.py` | Simulation capteurs | Données temps réel |
| `src/ai_agent.py` | Agent IA Gemini | Diagnostic |
| `src/rag_engine.py` | Moteur RAG | Guide manuel |
| `src/matlab_bridge.py` | Pont TCP MATLAB | Données (si MATLAB) |
| `frontend/src/App.jsx` | UI principale | Affichage |
| `frontend/src/components/PumpViewer3D.jsx` | Modèle 3D | Visualisation |
| `frontend/src/components/FaultTreeDiagram.jsx` | Guide manuel | RAG Display |
| `backend/fault_scenarios.py` | Définition des pannes | Injection |
| `chroma_db/` | Base vectorielle | RAG queries |

---

## 🔧 Configuration

### Variables d'Environnement (.env)

```env
GOOGLE_API_KEY=xxx          # Clé API Google Gemini
DATA_SOURCE=PYTHON          # ou MATLAB
MATLAB_HOST=127.0.0.1       # Si MATLAB
MATLAB_PORT=5555            # Port TCP MATLAB
```

### Ports Utilisés

| Port | Service |
|------|---------|
| 3001 | Frontend Vite |
| 8000 | Backend FastAPI |
| 5555 | MATLAB Bridge (TCP) |

---

## ✅ Résumé du Flux Complet

```
1. Utilisateur ouvre http://localhost:3001
   │
2. Frontend établit WebSocket avec Backend
   │
3. Backend démarre streaming données (1/sec)
   │
4. [Optionnel] Utilisateur injecte une panne
   │
5. Données capteurs modifiées selon la panne
   │
6. IA analyse et détecte le scénario
   │
7. RAG interroge le manuel Grundfos
   │
8. Frontend affiche :
   ├── Données temps réel (jauges + graphiques)
   ├── Diagnostic IA structuré
   └── Guide du manuel (contenu réel du PDF)
```

---

*Ce document décrit le pipeline tel qu'il fonctionne au 13 Décembre 2025.*

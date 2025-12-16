# Explications Détaillées et Code Correspondant

Ce document associe chaque slide de la présentation aux extraits de code Python pertinents du projet.

## Slide 1 : Objectif & périmètre
**Description :** Vue d'ensemble du projet.
**Code Correspondant :** Point d'entrée du backend (`backend/api.py`) qui initialise les composants principaux.

```python
# backend/api.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    global pump_simulator, ai_agent, mq_bridge
    
    # Initialize simulator (kept for fallback and local-only mode)
    pump_simulator = PumpSimulator()

    # Initialize MQTT bridge if enabled
    if _get_sensor_source() == "mqtt":
        mq_bridge = MQTTBridge(load_mqtt_config_from_env(), max_history=MAX_HISTORY)
        mq_bridge.start()
    
    # Initialize AI agent (may take a few seconds for embeddings)
    ai_agent = MaintenanceAIAgent()
```

## Slide 2 : Architecture globale
**Description :** Flux de données de la simulation à l'interface utilisateur.
**Code Correspondant :** Configuration de l'application FastAPI et des middlewares (`backend/api.py`).

```python
# backend/api.py

# Create FastAPI app
app = FastAPI(
    title="Digital Twin API",
    description="Real-time IoT Digital Twin for Grundfos CR Pump Predictive Maintenance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Slide 3 : Concepts clés (définitions)
**Description :** Définitions de RAG, Ingestion, Embeddings.
**Code Correspondant :** Initialisation du moteur RAG et des embeddings (`src/rag_engine.py`).

```python
# src/rag_engine.py

class RAGEngine:
    def __init__(self, ...):
        # Initialize embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Load or create vector store
        self.vector_store = self._initialize_vector_store()
```

## Slide 4 : Ingestion (Manuel PDF → ChromaDB)
**Description :** Processus de chargement, découpage et vectorisation du manuel.
**Code Correspondant :** Méthodes de chargement et de split du PDF (`src/rag_engine.py`).

```python
# src/rag_engine.py

def _load_and_split_pdf(self) -> List:
    # Load PDF
    loader = PyPDFLoader(self.pdf_path)
    documents = loader.load()
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    return chunks
```

## Slide 5 : Entrée online (MQTT → Snapshot)
**Description :** Récupération des données capteurs en temps réel.
**Code Correspondant :** Fonction pour obtenir la dernière lecture capteur (`backend/api.py`).

```python
# backend/api.py

def _get_latest_sensor_reading() -> Optional[Dict]:
    source = _get_sensor_source()
    if source == "mqtt" and mq_bridge:
        reading = mq_bridge.latest()
        if reading:
            _track_fault_context(reading)
        return reading
    if pump_simulator:
        reading = pump_simulator.get_sensor_reading()
        if reading:
            _track_fault_context(reading)
        return reading
    return None
```

## Slide 6 : Capteurs → RAG Query
**Description :** Transformation des anomalies capteurs en requête textuelle.
**Code Correspondant :** Construction de la requête RAG (`src/ai_agent.py`).

```python
# src/ai_agent.py

def _build_diagnostic_query(self, sensor_data: Dict) -> str:
    # Build query based on detected anomalies
    query_parts = []
    
    # Grundfos Manual Page 7: "If the current imbalance does not exceed 5%"
    if imbalance > 5:
        query_parts.append("motor winding defect phase imbalance")
    
    # Grundfos Manual Page 8: "voltage should be within 10% (+ or -)"
    if voltage < 207:
        query_parts.append("voltage supply fault low voltage")
    
    # ISO 10816: Vibration > 5 mm/s = unacceptable for pumps
    if vibration > 5:
        query_parts.append("cavitation high vibration")
    
    return " ".join(query_parts)
```

## Slide 7 : RAG (Retrieval → Augmentation → Generation)
**Description :** Le flux complet du RAG.
**Code Correspondant :** Récupération du contexte et génération du diagnostic (`src/ai_agent.py`).

```python
# src/ai_agent.py

def get_diagnostic(self, sensor_data: Dict, ...):
    # 1. Retrieval
    rag_query = self._build_diagnostic_query(sensor_data)
    retrieved_chunks = self.rag_engine.query_knowledge_base(query=rag_query, top_k=3)
    context = self._format_context(retrieved_chunks)
    
    # 2. Augmentation (Prompt Building)
    prompt = f"""{self.system_prompt}
    {sensor_text}
    DOCUMENTATION CONTEXT:
    {context}
    TASK: Analyze the sensor readings above..."""
    
    # 3. Generation
    response = self.llm.invoke([HumanMessage(content=prompt)])
```

## Slide 8 : Backend (Endpoints & Orchestration)
**Description :** Les endpoints API exposés au frontend.
**Code Correspondant :** Définition des routes FastAPI (`backend/api.py`).

```python
# backend/api.py

@app.post("/api/diagnose")
async def get_diagnosis(request: DiagnosticRequest):
    """Get AI diagnostic for current sensor data including shutdown decision"""
    result = ai_agent.get_diagnostic(request.sensor_data)
    return {
        "diagnosis": result["diagnosis"],
        "shutdown_decision": result.get("shutdown_decision", {}),
        "references": [...]
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with AI maintenance assistant"""
    # ... logic to call ai_agent.ask_question ...
```

## Slide 9 : Front-end (Rendu "rapport lisible")
**Description :** Parsing et affichage du diagnostic côté client.
**Code Correspondant :** Logique de parsing dans le composant React (`frontend/src/App.jsx`).

```javascript
// frontend/src/App.jsx

const parseDiagnosisText = (text) => {
    // Regex to identify sections like DIAGNOSIS, ROOT CAUSE, etc.
    const headerRegex = /^(?:#+\s*)?(?:\*\*)?\s*(DIAGNOSIS|ROOT\s*CAUSE|ACTION\s*ITEMS?|VERIFICATION\s*STEPS?|RECOMMENDATION)\s*(?:\*\*)?\s*:?\s*$/i
    
    // ... parsing logic to split text into sections ...
    
    return {
      diagnosis: toText(sections.diagnosis),
      rootCause: toText(sections.rootCause),
      actionItems: toList(sections.actionItems),
      verification: toList(sections.verification),
      recommendation: toText(sections.recommendation)
    }
}
```

## Slide 10 : Chatbot (Contexte + Mémoire)
**Description :** Intégration de la mémoire de session (historique de chat) et du contexte événementiel.
**Code Correspondant :** Injection de l’historique dans le prompt de chat (`src/ai_agent.py`) + gestion `session_id` côté API et front.

### Mémoire de session (chat history) — ce qu’on garde et comment

Objectif : garder le **contexte uniquement pendant la session de chat** (un seul chat), sans rien persister sur disque.

Ce que ça permet :
- Le chatbot “se souvient” de ce que l’utilisateur vient de dire (ex : “réponds en français”, “on parle de cavitation”).
- Mais si on redémarre le backend ou si on ouvre une nouvelle session, la mémoire repart de zéro.

#### Comment c’est fait (principe)
1) Le front envoie un `session_id` avec chaque message.
2) Le backend garde une liste en mémoire RAM : derniers messages `{role, content}` pour ce `session_id`.
3) À chaque question, on injecte cet historique dans le prompt sous **CHAT HISTORY**.

Extrait (frontend : envoi de `session_id`) :

```javascript
// frontend/src/App.jsx

body: JSON.stringify({
  message,
  include_sensor_context: true,
  session_id: chatSessionIdRef.current,
})
```

Extrait (backend : stockage RAM + passage à l’agent) :

```python
# backend/api.py

sid = (request.session_id or "default").strip() or "default"
history = chat_sessions.get(sid, [])
history.append({"role": "user", "content": msg})

response = ai_agent.ask_question(msg, sensor_data, fault_context=fault_context, chat_history=history)

history.append({"role": "assistant", "content": response})
chat_sessions[sid] = history[-CHAT_MAX_TURNS:]
```

Extrait (agent : injection dans le prompt) :

```python
# src/ai_agent.py

prompt = f"""{self.system_prompt}

CHAT HISTORY (this session, most recent):
{history_text if history_text else "(none)"}

DOCUMENTATION CONTEXT:
{context}

USER QUESTION: {question}
"""
```

## Slide 11 : Guardrails (Rester "maintenance")
**Description :** Instructions pour garder le chatbot focalisé.
**Code Correspondant :**
1) Guardrail **au niveau backend** (on refuse avant d’appeler le LLM).
2) Guardrail **dans le prompt** (instructions strictes pour le style/règles).

### Comment on force “maintenance-only”

Le plus important est le filtrage **avant** l’appel LLM : si la question n’est pas liée à la pompe/maintenance, on renvoie une réponse de recadrage.

#### Pourquoi filtrer avant le LLM ?
- Plus robuste qu’une simple consigne dans le prompt.
- Moins coûteux (pas d’appel LLM si hors sujet).
- Réduit les réponses “hors domaine” pendant la démo.

#### Comment on décide “maintenance” ? (principe)
- On détecte des  : mots-clés liés à la pompe, capteurs, défauts, tests, actions, etc.
- Si aucun mots-clés : on refuse + on demande de reformuler.

Extrait (filtre keywords, backend) :

```python
# backend/api.py

def _is_maintenance_question(text: str) -> bool:
    msg = (text or "").strip().lower()
    return any(k in msg for k in MAINTENANCE_KEYWORDS)

@app.post("/api/chat")
async def chat(request: ChatRequest):
    msg = (request.message or "").strip()
    if not _is_maintenance_question(msg):
        return {"response": _maintenance_refusal_message(msg)}
```

#### Limites (à connaître pour l’oral)
- Faux négatifs possibles : une question maintenance très courte sans mots-clés (“Pourquoi ?”) peut être refusée.
- Pour améliorer : ajouter un 2ème filtre **sémantique** (embedding similarity) en complément des keywords (décrit dans les slides), mais la version actuelle reste volontairement simple.

Ensuite, côté agent, on garde des instructions de chat pour rester concis et orienté action :

```python
# src/ai_agent.py

prompt = f"""{self.system_prompt}

CHAT MODE INSTRUCTIONS (must follow):
- Reply in the same language as the user's question.
- Give a DIRECT answer to the user's question.
- Do NOT output headings like: DIAGNOSIS, ROOT CAUSE...
- If the safety evaluation indicates IMMEDIATE_SHUTDOWN, say to stop immediately.
- Only include the 1–2 most relevant verification checks.
"""
```

## Slide 12 : Takeaways
**Description :** Résumé final.
**Code Correspondant :** (Pas de code spécifique, résumé de l'architecture globale).

---

# Schéma détaillé du Chatbot (end‑to‑end)

Ce schéma résume **exactement** ce qui se passe quand l’utilisateur envoie un message dans le chat.

## 1) Vue “pipeline” (avec décisions)

```
[Frontend React]
    |
    |  POST /api/chat
    |  body: { message, include_sensor_context, session_id }
    v
[FastAPI backend/api.py]
    |
    |--(A) Guardrail "maintenance-only"
    |      if NOT maintenance(question):
    |           return { response: refusal_message }
    |
    |--(B) Session memory (RAM)
    |      history = chat_sessions[session_id]
    |      history += {role:user, content:message}
    |
    |--(C) Contexte capteurs (optionnel)
    |      if include_sensor_context:
    |           sensor_data = latest_mqtt_or_simulator_snapshot()
    |      else:
    |           sensor_data = None
    |
    |--(D) Contexte événementiel (fault start snapshot)
    |      fault_context = last_fault_start_snapshot_if_any()
    |
    v
[MaintenanceAIAgent.ask_question]
    |
    |--(E) RAG retrieval (manuel) via RAGEngine
    |      top_k chunks = similarity_search(query)
    |
    |--(F) Prompt augmentation
    |      prompt = system_rules
    |             + CHAT HISTORY (this session)
    |             + SENSOR SNAPSHOT (if any)
    |             + FAULT START SNAPSHOT (if any)
    |             + DOCUMENTATION CONTEXT (top-k)
    |             + USER QUESTION
    |
    |--(G) LLM generation (Gemini)
    |      answer = llm.invoke(prompt)
    v
[FastAPI backend/api.py]
    |
    |--(H) Session memory update (RAM)
    |      history += {role:assistant, content:answer}
    |      keep last CHAT_MAX_TURNS
    v
return { response: answer }
```

## 2) Lecture rapide (ce que tu peux dire à l’oral)

- Le front envoie `message` + `session_id`.
- Le backend bloque d’abord les questions hors maintenance (guardrail).
- Le backend conserve **uniquement** l’historique du chat en RAM (par `session_id`).
- L’agent fait du RAG sur le manuel (top‑k chunks) et injecte : historique + capteurs + manuel dans le prompt.
- Le LLM répond, puis on sauvegarde la réponse dans l’historique de session.

## 3) Cas limites (important pour la démo)

- Si le backend redémarre : la RAM est reset ⇒ l’historique de chat est perdu (normal, “session-only”).
- Si `session_id` change : on démarre une nouvelle session (historique vide).
- Si `include_sensor_context=false` : le chat répond avec RAG + historique, sans snapshot capteurs.

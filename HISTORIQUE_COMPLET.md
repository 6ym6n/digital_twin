# 📚 Historique Complet du Projet Digital Twin Grundfos CR 15

> **Documentation exhaustive de toutes les décisions, implémentations et évolutions du projet**  
> Dernière mise à jour : 13 Décembre 2025

---

## 📋 Table des Matières

1. [Vue d'Ensemble du Projet](#1-vue-densemble-du-projet)
2. [Architecture Technique](#2-architecture-technique)
3. [Fonctionnalités Implémentées](#3-fonctionnalités-implémentées)
4. [Fonctionnalités Retirées](#4-fonctionnalités-retirées)
5. [Décisions de Conception](#5-décisions-de-conception)
6. [Évolution du Code](#6-évolution-du-code)
7. [État Actuel](#7-état-actuel)

---

## 1. Vue d'Ensemble du Projet

### 1.1 Objectif Initial
Créer un **jumeau numérique (Digital Twin)** pour une pompe centrifuge **Grundfos CR 15** permettant :
- La simulation en temps réel des capteurs
- L'injection de pannes pour la formation
- Le diagnostic IA basé sur le manuel technique
- La visualisation 3D interactive

### 1.2 Stack Technologique Choisie

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Backend | FastAPI (Python) | Async, WebSocket natif, performant |
| Frontend | React + Vite | Rapide, moderne, hot reload |
| IA | Google Gemini 2.5 Flash | Gratuit, performant, 1M tokens |
| RAG | LangChain + ChromaDB | Standard industrie, local |
| 3D | React Three Fiber | Intégration React native |
| Styling | Tailwind CSS | Utility-first, rapide |

### 1.3 Source de Données
- **Manuel PDF Grundfos CR 15** : Document technique officiel
- **41 chunks** indexés dans ChromaDB via RAG
- Embedding via Google Generative AI

---

## 2. Architecture Technique

### 2.1 Structure des Fichiers

```
digital_twin/
├── backend/
│   ├── api.py                 # API REST + WebSocket
│   └── fault_scenarios.py     # Définition des pannes
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Application principale
│   │   ├── main.jsx           # Point d'entrée
│   │   ├── index.css          # Styles Tailwind
│   │   └── components/
│   │       ├── PumpViewer3D.jsx      # Modèle 3D
│   │       └── FaultTreeDiagram.jsx  # Guide manuel RAG
│   ├── public/models/         # Fichiers GLTF 3D
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── src/
│   ├── __init__.py
│   ├── ai_agent.py            # Agent IA Gemini
│   ├── rag_engine.py          # Moteur RAG
│   ├── simulator.py           # Simulation Python
│   ├── matlab_bridge.py       # Pont TCP MATLAB
│   └── config.py              # Configuration
│
├── data/
│   └── grundfos_cr15_manual.pdf  # Manuel source
│
├── chroma_db/                 # Base vectorielle persistante
│
├── .env                       # Variables d'environnement
├── requirements.txt           # Dépendances Python
└── run.py                     # Script de lancement
```

### 2.2 Communication

```
┌─────────────┐  WebSocket   ┌─────────────┐  TCP/5555   ┌─────────────┐
│   REACT     │◄────────────►│   FASTAPI   │◄───────────►│   MATLAB    │
│  (Port 3001)│              │  (Port 8000)│             │  Simulink   │
└─────────────┘              └──────┬──────┘             └─────────────┘
                                    │
                                    ▼
                             ┌─────────────┐
                             │  GEMINI IA  │
                             │  + RAG      │
                             └─────────────┘
```

---

## 3. Fonctionnalités Implémentées

### 3.1 ✅ Streaming Temps Réel des Capteurs

**Description** : Données capteurs envoyées toutes les secondes via WebSocket.

**Capteurs simulés** :
| Capteur | Unité | Plage Normale |
|---------|-------|---------------|
| Flow Rate | m³/h | 12-18 |
| Pressure | bar | 4-6 |
| Temperature | °C | 35-55 |
| Vibration | mm/s | 0-3 |
| Power | kW | 4-7 |
| RPM | tr/min | 2900-3000 |
| Current | A | 10-15 |

**Code clé** : `backend/api.py` - fonction `broadcast_sensor_data()`

---

### 3.2 ✅ Injection de Pannes

**Description** : 6 scénarios de pannes injectables via API.

**Pannes disponibles** :

| ID | Nom | Sévérité | Effets |
|----|-----|----------|--------|
| `CAVITATION` | Cavitation | 2/4 | ↓Flow, ↑Vibration, ↓Pressure |
| `BEARING_FAILURE` | Roulement | 3/4 | ↑Vibration++, ↑Temperature |
| `SEAL_LEAK` | Fuite Joint | 2/4 | ↓Pressure, ↓Flow |
| `IMPELLER_DAMAGE` | Impeller | 3/4 | ↓Flow--, ↑Power |
| `OVERLOAD` | Surcharge | 3/4 | ↑Current, ↑Power, ↑Temperature |
| `BLOCKAGE` | Blocage | 4/4 | ↓Flow---, ↑Pressure++ |

**Endpoint** : `POST /api/inject-fault`

---

### 3.3 ✅ Diagnostic IA avec Gemini

**Description** : Analyse automatique des données capteurs pour détecter les anomalies.

**Fonctionnement** :
1. Données capteurs envoyées à l'agent IA
2. RAG récupère le contexte du manuel Grundfos
3. Gemini génère un diagnostic structuré

**Prompt système** :
```
Tu es un expert en maintenance de pompes industrielles.
Analyse les données capteurs et fournis :
- Un diagnostic précis
- La cause racine probable
- Les actions correctives recommandées
- Les références au manuel technique
```

**Format de sortie** (parsé par le frontend) :
```
**Diagnosis:** Description du problème
**Root Cause:** Cause identifiée
**Action Items:**
- Action 1
- Action 2
**Manual References:** Pages du manuel
```

---

### 3.4 ✅ Guide Manuel RAG (Requêtes Réelles)

**Description** : Interrogation du manuel PDF via recherche vectorielle.

**Évolution importante** : Cette fonctionnalité a beaucoup évolué (voir section 4).

**État actuel** :
- Endpoint : `GET /api/manual-guide/{scenario_id}`
- Requête RAG construite dynamiquement : `"{fault_name} symptoms causes troubleshooting corrective actions"`
- Retourne le **contenu brut du manuel** (pas de données pré-définies)
- Inclut les références de pages

**Exemple de réponse** :
```json
{
  "manual_content": "Pump is cavitating\nTurn the pump off, close the isolation valve(s)...",
  "manual_references": ["Page 5", "Page 3", "Page 2"],
  "query_used": "cavitation symptoms causes troubleshooting corrective actions"
}
```

---

### 3.5 ✅ Visualisation 3D Interactive

**Description** : Modèle 3D de la pompe qui change de couleur selon l'état.

**Composant** : `PumpViewer3D.jsx`

**États visuels** :
| État | Couleur | Condition |
|------|---------|-----------|
| Normal | Vert | `active_fault === "NORMAL"` |
| Attention | Jaune | Sévérité 1-2 |
| Critique | Rouge | Sévérité 3-4 |

---

### 3.6 ✅ Interface Utilisateur Moderne

**Composants UI** :
- Jauges circulaires animées
- Graphiques historiques (60 dernières secondes)
- Panneau de contrôle des pannes
- Panneau de diagnostic structuré
- Thème sombre slate/cyan

---

### 3.7 ✅ Support Dual Source (Python/MATLAB)

**Description** : Le système peut recevoir des données de deux sources.

**Mode Python** (`DATA_SOURCE=PYTHON`) :
- Simulation locale via `PumpSimulator`
- Pas de dépendance externe

**Mode MATLAB** (`DATA_SOURCE=MATLAB`) :
- `HybridSimulator` + `MATLABBridge`
- TCP sur port 5555
- Synchronisation avec Simulink

---

## 4. Fonctionnalités Retirées

### 4.1 ❌ Système de Progression des Pannes avec Probabilités

**Ce qui existait** :
```python
@dataclass
class FaultProgression:
    current_fault: str
    next_faults: List[str]
    probability: float          # ← RETIRÉ
    time_to_progress: str       # ← RETIRÉ
    prevention_action: str      # ← RETIRÉ
```

**Interface associée** : Arbre de décision IF/ELSE avec pourcentages

**Raison du retrait** :
> "D'où viennent ces probabilités ?" → Elles étaient **inventées** (estimations générales), pas issues du manuel Grundfos.

**Décision utilisateur** : 
> "Je veux m'en tenir strictement au manuel. Pas de données inventées."

---

### 4.2 ❌ Estimations de Temps de Progression

**Ce qui existait** :
- "Si non traité → Bearing Failure dans 2-4 heures"
- "Temps estimé avant défaillance critique : 30 min"

**Raison du retrait** :
> Ces temps étaient des **estimations fictives** basées sur des connaissances générales, non documentées dans le manuel Grundfos.

---

### 4.3 ❌ Actions de Prévention Génériques

**Ce qui existait** :
```
To Prevent — Do This:
"Schedule bearing inspection immediately"
"Check lubrication system"
```

**Raison du retrait** :
> Ces recommandations venaient de **connaissances générales en maintenance**, pas du manuel Grundfos spécifique.

---

### 4.4 ❌ Données Pré-définies dans fault_scenarios.py

**Ce qui existait** :
```python
FAULT_SCENARIOS = {
    "CAVITATION": {
        "symptoms": ["Bruit de claquement", "Vibrations irrégulières"],
        "causes": ["NPSH insuffisant", "Air dans la ligne"],
        "repair_action": "Vérifier NPSH et purger l'air"
    }
}
```

**Problème identifié** :
> "Il me met direct les symptoms et tous comme si y'avait un JSON ou quoi, d'où il prend ça ?"

**Solution** : Remplacé par des **requêtes RAG réelles** au manuel PDF.

---

### 4.5 ❌ Affichage IF/ELSE Decision Tree

**Ce qui existait** :
```
IF cavitation continues → 70% chance → Bearing Failure
   └── Time: 2-4 hours
ELSE → 30% chance → Impeller Damage
   └── Time: 4-8 hours
```

**Raison du retrait** :
- Probabilités fictives
- Temps fictifs
- Donnait une fausse impression de précision scientifique

---

## 5. Décisions de Conception

### 5.1 📌 "Strictement le Manuel"

**Contexte** : Discussion sur les sources de données.

**Décision finale** :
> Toutes les informations affichées concernant les pannes, symptômes, causes et actions doivent provenir **exclusivement du manuel Grundfos CR 15** via RAG.

**Implications** :
- Pas de probabilités inventées
- Pas d'estimations de temps
- Pas de recommandations génériques
- Contenu brut du RAG affiché

---

### 5.2 📌 Anglais pour l'Interface

**Contexte** : L'interface était initialement en français.

**Décision** :
> Convertir toute l'interface en anglais pour cohérence avec le manuel (en anglais).

**Changements** :
- Labels des capteurs
- Messages de diagnostic
- Titres des sections
- Texte des boutons

---

### 5.3 📌 Structure du Diagnostic en Sections

**Format choisi** :
```
┌─────────────────────────────┐
│ 📋 DIAGNOSIS (cyan)         │
├─────────────────────────────┤
│ 🔍 ROOT CAUSE (orange)      │
├─────────────────────────────┤
│ ✅ ACTION ITEMS (vert)      │
├─────────────────────────────┤
│ 📖 MANUAL REFS (bleu tags)  │
└─────────────────────────────┘
```

**Raison** : Clarté et facilité de lecture pour l'opérateur.

---

### 5.4 📌 RAG Query Dynamique

**Format de requête** :
```
"{fault_name} symptoms causes troubleshooting corrective actions"
```

**Exemple pour CAVITATION** :
```
"cavitation symptoms causes troubleshooting corrective actions"
```

**Raison** : Maximise les chances de récupérer le contenu pertinent du manuel.

---

## 6. Évolution du Code

### 6.1 FaultTreeDiagram.jsx

**Version 1 - Arbre de Décision avec Probabilités** :
```jsx
// Structure IF/ELSE avec probabilités
<TreeNode>
  IF continues → 70% → Bearing Failure (2-4h)
  ELSE → 30% → Impeller Damage (4-8h)
</TreeNode>
```

**Version 2 - Guide Manuel (données pré-définies)** :
```jsx
// Sections Symptoms/Causes/Actions
<Section title="Symptoms">{scenario.symptoms.map(...)}</Section>
<Section title="Causes">{scenario.causes.map(...)}</Section>
```

**Version 3 - Guide Manuel (RAG réel)** ✅ **ACTUEL** :
```jsx
// Contenu brut du RAG
<ManualContent>
  {formatManualContent(data.manual_content)}
</ManualContent>
<References>{data.manual_references}</References>
<QueryUsed>{data.query_used}</QueryUsed>
```

---

### 6.2 API /api/manual-guide/{scenario_id}

**Version 1 - Données Statiques** :
```python
return {
    "symptoms": FAULT_SCENARIOS[id].symptoms,
    "causes": FAULT_SCENARIOS[id].causes,
    "repair_action": FAULT_SCENARIOS[id].repair_action
}
```

**Version 2 - RAG Réel** ✅ **ACTUEL** :
```python
# Requête RAG dynamique
rag_query = f"{fault_name} symptoms causes troubleshooting corrective actions"
chunks = ai_agent.rag_engine.query_knowledge_base(query=rag_query, top_k=5)

# Extraction du contenu brut
manual_content = "\n\n".join([chunk['content'] for chunk in chunks])

return {
    "manual_content": manual_content,
    "manual_references": [f"Page {c['page']}" for c in chunks],
    "query_used": rag_query
}
```

---

### 6.3 DiagnosisPanel dans App.jsx

**Ajout du parsing structuré** :
```javascript
const parseDiagnosis = (text) => {
  const sections = {
    diagnosis: extractSection(text, '**Diagnosis:**'),
    rootCause: extractSection(text, '**Root Cause:**'),
    actionItems: extractBulletPoints(text, '**Action Items:**'),
    manualRefs: extractSection(text, '**Manual References:**')
  };
  return sections;
};
```

---

## 7. État Actuel

### 7.1 Ce qui Fonctionne ✅

| Fonctionnalité | Status | Notes |
|----------------|--------|-------|
| Streaming capteurs WebSocket | ✅ | 1 message/seconde |
| Injection de pannes | ✅ | 6 scénarios |
| Diagnostic IA Gemini | ✅ | Structuré en sections |
| RAG sur manuel PDF | ✅ | 41 documents indexés |
| Guide manuel (contenu réel) | ✅ | Pas de données inventées |
| Visualisation 3D | ✅ | Couleurs dynamiques |
| Support Python/MATLAB | ✅ | Configurable via .env |

### 7.2 Ce qui a été Retiré ❌

| Fonctionnalité | Raison |
|----------------|--------|
| Probabilités de progression | Données fictives |
| Temps de progression | Données fictives |
| Actions de prévention génériques | Pas dans le manuel |
| Arbre IF/ELSE | Représentation trompeuse |
| Données pré-définies symptoms/causes | Remplacé par RAG réel |

### 7.3 Fichiers Principaux Modifiés

| Fichier | Modifications Majeures |
|---------|----------------------|
| `FaultTreeDiagram.jsx` | 3 réécritures complètes |
| `api.py` | Ajout endpoint RAG réel |
| `App.jsx` | Parsing diagnostic structuré |
| `fault_scenarios.py` | Simplifié (métadonnées seulement) |

### 7.4 Endpoints API Actifs

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/ws` | WebSocket | Streaming capteurs |
| `/api/inject-fault` | POST | Injection de panne |
| `/api/clear-fault` | POST | Remise à zéro |
| `/api/diagnose` | POST | Diagnostic IA |
| `/api/manual-guide/{id}` | GET | Guide RAG du manuel |
| `/api/chat` | POST | Chat avec l'IA |
| `/api/sensor-data` | GET | Données actuelles |
| `/api/scenarios` | GET | Liste des scénarios |

---

## 📝 Leçons Apprises

### 1. Transparence des Sources de Données
> Ne jamais présenter des estimations comme des faits. Si une donnée n'est pas dans la documentation officielle, soit l'indiquer clairement, soit ne pas l'afficher.

### 2. RAG vs Données Statiques
> Le RAG est plus lent mais garantit que le contenu vient réellement de la source. Les données statiques sont plus rapides mais peuvent devenir obsolètes ou incorrectes.

### 3. Simplicité vs Fonctionnalités
> Mieux vaut une fonctionnalité simple et correcte qu'une fonctionnalité complexe avec des données douteuses.

### 4. Itération Utilisateur
> Les besoins évoluent. Le système de progression semblait utile au départ, mais l'exigence de rigueur l'a rendu inapproprié.

---

## 🔮 Évolutions Futures Possibles

1. **Historique des diagnostics** : Sauvegarder les diagnostics passés
2. **Alertes automatiques** : Notifications quand seuils dépassés
3. **Export PDF** : Générer des rapports de maintenance
4. **Multi-pompes** : Surveiller plusieurs équipements
5. **Mode hors-ligne** : Cache local pour le RAG

---

*Document généré le 13 Décembre 2025*  
*Projet Digital Twin Grundfos CR 15*

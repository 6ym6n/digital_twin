# Digital Twin — Pipeline RAG de maintenance (Slide-ready)

---

## 1) Objectif & périmètre

- Exploiter la télémétrie d’une pompe (MATLAB/Simulink → MQTT) pour aider au **diagnostic maintenance**
- Générer un **rapport actionnable** (diagnostic, cause probable, actions, vérifications)
- Appuyer les recommandations par le **manuel** via **RAG (ChromaDB)**
- Présenter le résultat dans une UI (dashboard + chatbot) orientée technicien

---

## 2) Architecture globale (schéma)

```
       (MATLAB/Simulink + MQTT)
              │
              ▼
       ┌──────────────────┐
       │ Backend FastAPI   │
       │ - snapshot        │
       │ - RAG (manuel)    │
       │ - prompt          │
       └───────┬──────────┘
               │
               ▼
         [ LLM (Gemini) ]
               │
               ▼
   Rapport diagnostic / Réponse Chat
               │
               ▼
        [ Front-end React ]
      (cartes/sections + chat)
```

---

## 3) Concepts clés (définitions)

- **Ingestion (PDF → ChromaDB)** : extraire le texte du PDF, le découper en **chunks**, calculer des **embeddings**, puis stocker (vecteurs + pages + contenu) dans ChromaDB.
- **Chunk** : petit extrait du manuel (quelques paragraphes) + métadonnées (page, source).
- **Embedding** : vecteur numérique qui représente le **sens** d’un texte.
- **Vector DB (ChromaDB)** : base qui permet de retrouver les chunks **les plus similaires** à une requête.
- **Similarity search** : recherche des **top‑k** vecteurs les plus proches (cosine/distance).
- **Prompt** : entrée structurée du LLM (rôle + données + contexte + tâche).
- **Guardrails** : filtres qui limitent le chatbot aux sujets maintenance.
- **Mémoire de session (chat history)** : historique court du chat courant réinjecté dans le prompt (pas de persistance).

Définition RAG (en 3 étapes) :
1) **Retrieval (rechercher des extraits pertinents)** : on transforme la question (ou la RAG query) en embedding, puis on récupère les **top‑k chunks** du manuel les plus proches.
2) **Augmentation (comment on “augmente”)** : on **injecte** ces chunks (avec page/source) dans le prompt, en plus du **snapshot capteurs** et des consignes (format, sécurité, limites).
3) **Generation (réponse LLM)** : le LLM génère la réponse/rapport **en s’appuyant sur le contexte injecté**.

---

## 4) Ingestion : manuel PDF → ChromaDB (offline)

```
      Manuel PDF
         │
         ▼
  1) Extraction texte
         │
         ▼
  2) Chunking (+ overlap)
         │
         ▼
  3) Embeddings (texte → vecteurs)
         │
         ▼
  4) Stockage ChromaDB
     (vecteur + page + source + contenu)
```

---

## 5) Entrée online : MQTT → snapshot capteurs

- Source : MQTT (MATLAB/Simulink publie la télémétrie, le backend lit le dernier snapshot)
- Contenu typique : courant 3 phases + déséquilibre, tension, vibration, pression, température, fault_state + durée
- Ce snapshot devient le **contexte temps réel** pour l’IA

---

## 6) Capteurs → RAG query (normalisation en texte)

Objectif : convertir des valeurs brutes en requête “texte” proche du vocabulaire du manuel.

- Exemples (anomalies → mots‑clés) :
  - déséquilibre courant > 5% → `motor winding defect phase imbalance`
  - tension < 207V → `voltage supply fault low voltage`
  - vibration > 5 mm/s → `cavitation high vibration`
  - température > 80°C → `motor overheating causes`

---

## 7) RAG : schéma (retrieval → augmentation → génération)

```
Question / anomalies capteurs
       │
       ▼
   RAG query (texte)
       │
       ▼
Embedding(query) + Similarity search
       │
       ▼
  Top‑k chunks (manuel)
       │
       ▼
Prompt augmenté = capteurs + chunks + consignes
       │
       ▼
      LLM
       │
       ▼
Rapport / actions / réponse chat
```

---

## 8) Backend : endpoints et orchestration

- `POST /api/diagnose` :
  - reçoit un snapshot capteurs
  - exécute RAG + LLM
  - renvoie : `diagnosis` + références + décision “shutdown”

- `POST /api/chat` :
  - questions utilisateur
  - inclut : snapshot capteurs + extraits du manuel (RAG)
  - + contexte début de défaut (si capturé)

---

## 9) Front-end : rendu “rapport lisible”

- Transforme la sortie texte en sections lisibles (cartes + listes)
- But : **lisible en démo**, **actionnable en maintenance**, cohérent avec une UI de supervision

---

## 10) Chatbot : contexte + mémoire

Le chatbot combine :

- **Statut courant** (snapshot capteurs)
- **Contexte manuel** (chunks RAG)
- **Contexte événementiel** (début du défaut si capturé)
- **Mémoire de session** (historique du chat courant)

Schéma très simple (1 ligne) :

```
(Message de l'utilisateur + History + Sensors + Manual)→ Guardrail → LLM → Answer
```

Schéma (où la mémoire de session se place) :

```
Frontend (React)
       │  message + session_id
       ▼
POST /api/chat (FastAPI)
       │
       ├─ Guardrail "maintenance" ?  ── non ─► refus + recadrage
       │
       └─ oui
                      │
                      ├─ Mémoire de session : derniers messages (RAM)
                      ├─ Snapshot capteurs : état courant (si activé)
                      ├─ Snapshot défaut : début du défaut (si capturé)
                      └─ RAG : top‑k chunks du manuel
                                                 │
                                                 ▼
                            Prompt = (règles + historique + capteurs + manuel)
                                                 │
                                                 ▼
                                          LLM (Gemini)
                                                 │
                                                 ▼
                     Réponse courte, actionnable (maintenance)
```

---

## 11) Guardrails : rester “maintenance”

- Filtre 1 (règles) : refuser si aucun signal maintenance (pompe, moteur, vibration, cavitation, défaut, test…)
- Filtre 2 (sémantique) : refuser si similarité trop faible avec des intentions “maintenance”
- Fallback : réponse de cadrage

```
User question
   │
   ├─ (1) Keywords maintenance ?  ── non ─► Refus + recadrage
   │
   └─ oui
        │
        ├─ (2) Similarité sémantique ok ? ── non ─► Refus
        │
        └─ oui ─► RAG + LLM
```

---

## 12) Takeaways

- RAG = capteurs → query → Chroma → contexte → prompt augmenté → rapport
- UI = transforme la sortie en sections lisibles
- Chat = même base, mais orienté Q/R “quoi faire maintenant”
- Guardrails = limitation au domaine maintenance
- Mémoire = contexte conservé uniquement dans la session de chat

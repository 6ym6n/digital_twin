# Demo Checklist — Tests à faire devant les profs

Ce fichier contient une **séquence de tests/démonstrations** (avec résultat attendu) pour prouver que l’implémentation marche : MQTT → Backend → RAG → LLM → UI + Chat + Memory.

---

## 0) Pré-requis (à vérifier avant la soutenance)

- Avoir un fichier `.env` avec `GOOGLE_API_KEY=...` (sinon RAG/LLM/memory ne démarrent pas).
- Avoir Mosquitto (ou broker MQTT) lancé si vous présentez en mode MQTT.
- Avoir le hookup MQTT : MATLAB/Simulink publie bien sur le topic télémétrie attendu.

**Option (recommandé)** : prévoir 1 plan B si MQTT ne marche pas : basculer `SENSOR_SOURCE=simulator` (si vous utilisez encore le simulateur fallback).

---

## 1) Lancer les serveurs

### 1.1 Backend
- Lancer : `start_backend.bat`
- Attendu : dans la console, message “Backend ready” + serveur sur `http://localhost:8000`.

### 1.2 Frontend
- Lancer : `start_frontend.bat`
- Attendu : serveur Vite/React (souvent `http://localhost:3000` ou affiché dans la console).

---

## 2) Test “santé” (smoke test)

1) Ouvrir l’URL backend : `http://localhost:8000/`
- Attendu : JSON avec `status: online`.

2) Ouvrir l’UI React.
- Attendu : dashboard chargé, pas d’erreurs visibles.

---

## 3) Test MQTT → Snapshot capteurs (contexte temps réel)

1) Vérifier que des données capteurs arrivent :
- UI : les valeurs (tension/courant/vibration/température/pression) bougent.

2) Vérifier l’API : `GET /api/sensor-data`
- Attendu : JSON avec `timestamp`, `fault_state`, valeurs capteurs.

**Si ça ne bouge pas** :
- vérifier broker MQTT
- vérifier topic côté Simulink
- vérifier `SENSOR_SOURCE=mqtt`

---

## 4) Test RAG “diagnostic” (rapport)

Objectif : prouver que le système utilise le manuel via ChromaDB.

1) Depuis l’UI, cliquer sur “Diagnose” (ou bouton équivalent)
- Attendu : un texte de diagnostic apparaît.
- Attendu : la réponse contient des recommandations concrètes + références/pages (selon UI).

2) Vérifier l’endpoint : `POST /api/diagnose` avec le snapshot courant
- Attendu : réponse JSON avec :
  - `diagnosis`
  - `references` (pages + scores)
  - `shutdown_decision`

---

## 5) Test Chat (réponse courte et actionnable)

1) Envoyer une question de maintenance :
- Exemple : “Que dois-je vérifier si la vibration est élevée ?”
- Attendu : réponse en **4–8 bullet points**, orientée “quoi faire maintenant”.

2) Tester une question “début du défaut” :
- Exemple : “Au début du défaut, quels étaient les capteurs ?”
- Attendu : la réponse utilise le snapshot de début de défaut **si disponible** (voir test 6).

---

## 6) Test “fault start snapshot” (état capteurs au début)

Objectif : prouver que le backend capture l’état au démarrage d’une panne.

1) Provoquer un défaut (depuis Simulink/MQTT, ou via UI si vous avez un injecteur)
2) Attendre 2–5 secondes pour avoir une transition Normal → Fault.
3) Appeler : `GET /api/fault-context`
- Attendu :
  - `active.fault_state` ≠ Normal
  - `active.fault_start_snapshot` contient les valeurs capteurs au moment du début

4) Poser au chat : “Quels capteurs au début ?”
- Attendu : la réponse mentionne les valeurs de `fault_start_snapshot`.

---

## 7) Test Semantic Memory (persistance + utilisation)

### 7.1 Sauvegarder une note
Option A (chat) :
1) Envoyer : `remember: Always answer in French`
- Attendu : message de confirmation (Saved/Noté)

Option B (API) :
1) `POST /api/memory` avec `{ "text": "Réponds toujours en français", "tag": "preference" }`
- Attendu : JSON `status: success` + un `id`.

### 7.2 Vérifier la recherche
1) `GET /api/memory/search?query=french&k=3`
- Attendu : la note ressort dans `results`.

### 7.3 Vérifier l’effet sur le chat
1) Poser une question en anglais : “What should I do if voltage is low?”
- Attendu : réponse en **français** (si la note est bien récupérée et injectée).

---

## 8) Test “maintenance-only” (guardrails)

Objectif : prouver que le chatbot ne répond pas hors sujet.

1) Envoyer une question hors maintenance :
- Exemple : “Tell me a joke” / “Donne-moi une recette de pizza”
- Attendu : refus + recadrage (“je réponds seulement maintenance…”)

2) Envoyer une question maintenance juste après :
- Exemple : “Comment vérifier un roulement ?”
- Attendu : réponse normale (bullet points).

---

## 9) Test sécurité : Emergency stop

1) Provoquer des conditions “critiques” (si votre simulation le permet) ou utiliser le bouton stop.
2) Cliquer “Emergency Stop”
- Attendu : le backend confirme.
- Attendu : l’UI met les capteurs à zéro (état pump stopped).

---

## 10) Plan B (si démo instable)

- Si MQTT instable : montrer le pipeline avec des snapshots (diagnose + chat) via un exemple enregistré.
- Si LLM rate-limit : montrer RAG retrieval (references/pages) + expliquer que la génération est la dernière étape.

---

## Mini script oral (30 secondes)

1) “Je lance backend + front”
2) “Je montre les capteurs live via MQTT”
3) “Je lance Diagnose → on voit RAG + références”
4) “Je pose une question chat → réponse actionnable”
5) “Je montre mémoire (remember) → le chat suit la préférence”
6) “Je teste une question hors sujet → refus (guardrail)”

# 🏭 Digital Twin - Pompe Grundfos CR 15

> **Jumeau numérique intelligent pour la maintenance prédictive d'une pompe centrifuge industrielle**

![Status](https://img.shields.io/badge/status-en%20développement-yellow)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Table des Matières

1. [C'est quoi ce projet ?](#-cest-quoi-ce-projet-)
2. [Prérequis](#-prérequis)
3. [Installation pas à pas](#-installation-pas-à-pas)
4. [Lancer l'application](#-lancer-lapplication)
5. [Utiliser l'application](#-utiliser-lapplication)
6. [Structure du projet](#-structure-du-projet)
7. [Résolution des problèmes](#-résolution-des-problèmes)
8. [Pour aller plus loin](#-pour-aller-plus-loin)

---

## 🤔 C'est quoi ce projet ?

Ce projet est un **simulateur interactif** d'une pompe industrielle Grundfos CR 15. Il permet de :

- 📊 **Voir en temps réel** les données des capteurs (débit, pression, température, vibrations...)
- ⚠️ **Simuler des pannes** pour comprendre leur impact
- 🤖 **Obtenir un diagnostic IA** qui analyse les données et propose des solutions
- 📖 **Consulter le manuel** technique automatiquement

### À quoi ça sert ?

- **Formation** : Apprendre à diagnostiquer des pannes sans risquer un vrai équipement
- **Démonstration** : Montrer le concept de jumeau numérique
- **Recherche** : Tester des algorithmes de diagnostic

### Comment ça marche ? (Version simple)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SIMULATEUR    │────►│    SERVEUR      │────►│   INTERFACE     │
│   (Python)      │     │    (FastAPI)    │     │   (React)       │
│                 │     │                 │     │                 │
│ Génère les      │     │ Traite les      │     │ Affiche les     │
│ données des     │     │ données et      │     │ jauges, le      │
│ capteurs        │     │ appelle l'IA    │     │ modèle 3D...    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   INTELLIGENCE  │
                        │   ARTIFICIELLE  │
                        │   (Gemini + RAG)│
                        │                 │
                        │ Analyse et      │
                        │ consulte le     │
                        │ manuel PDF      │
                        └─────────────────┘
```

---

## ✅ Prérequis

Avant de commencer, vous devez avoir installé sur votre ordinateur :

### 1. Python 3.10 ou plus récent

**Qu'est-ce que c'est ?** Python est le langage de programmation utilisé pour le serveur et l'IA.

**Vérifier si Python est installé :**
```powershell
python --version
```

✅ Si vous voyez `Python 3.10.x` ou plus, c'est bon !

❌ Sinon :
1. Allez sur [python.org/downloads](https://www.python.org/downloads/)
2. Téléchargez la dernière version
3. Lancez l'installateur
4. ⚠️ **TRÈS IMPORTANT** : Cochez la case **"Add Python to PATH"** en bas de la fenêtre
5. Cliquez sur "Install Now"

### 2. Node.js 18 ou plus récent

**Qu'est-ce que c'est ?** Node.js permet d'exécuter l'interface web (le frontend).

**Vérifier si Node.js est installé :**
```powershell
node --version
```

✅ Si vous voyez `v18.x.x` ou plus, c'est bon !

❌ Sinon :
1. Allez sur [nodejs.org](https://nodejs.org/)
2. Téléchargez la version **LTS** (recommandée)
3. Lancez l'installateur et suivez les étapes

### 3. Une clé API Google Gemini (GRATUIT)

**Qu'est-ce que c'est ?** Une "clé API" est comme un mot de passe qui permet à notre application d'utiliser l'IA de Google.

**Comment l'obtenir (5 minutes) :**

1. Ouvrez votre navigateur et allez sur : [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

2. Connectez-vous avec votre compte Google (créez-en un si nécessaire)

3. Cliquez sur le bouton **"Create API Key"** (Créer une clé API)

4. Une clé apparaît, elle ressemble à : `AIzaSyB1abc123def456ghi789...`

5. **Copiez cette clé** (cliquez sur l'icône copier ou sélectionnez tout et Ctrl+C)

6. **Gardez cette clé précieusement**, vous en aurez besoin plus tard

> 💡 La clé est gratuite et permet ~60 requêtes par minute, largement suffisant pour ce projet.

---

## 📦 Installation pas à pas

### Étape 1 : Ouvrir PowerShell

**Qu'est-ce que PowerShell ?** C'est comme une "télécommande" pour votre ordinateur où vous tapez des commandes.

**Comment l'ouvrir :**
- Appuyez sur les touches `Win` + `X` en même temps
- Cliquez sur "Terminal" ou "Windows PowerShell"

Ou :
- Appuyez sur la touche `Win`
- Tapez "PowerShell"
- Appuyez sur Entrée

Une fenêtre bleue (ou noire) s'ouvre avec du texte.

### Étape 2 : Aller dans le dossier du projet

Tapez cette commande et appuyez sur Entrée :

```powershell
cd C:\projetMaintenanceV2\digital_twin
```

> 📝 `cd` signifie "change directory" (changer de dossier)
> 
> Si votre projet est dans un autre dossier, remplacez le chemin.

### Étape 3 : Créer un environnement virtuel Python

**Qu'est-ce que c'est ?** Un "environnement virtuel" est un espace isolé où on installe les dépendances du projet sans affecter le reste de votre ordinateur.

Tapez :
```powershell
python -m venv venv
```

> Cette commande crée un dossier `venv` dans votre projet.

### Étape 4 : Activer l'environnement virtuel

Tapez :
```powershell
.\venv\Scripts\Activate
```

✅ **Signe de succès** : Vous voyez `(venv)` au début de la ligne de commande :
```
(venv) PS C:\projetMaintenanceV2\digital_twin>
```

⚠️ **Si vous avez une erreur** du type "execution of scripts is disabled" :
1. Tapez cette commande :
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
2. Tapez `O` ou `Y` pour confirmer
3. Réessayez d'activer : `.\venv\Scripts\Activate`

### Étape 5 : Installer les dépendances Python

Tapez :
```powershell
pip install -r requirements.txt
```

> 📝 `pip` est le gestionnaire de packages Python
> 
> `requirements.txt` contient la liste de tout ce qu'il faut installer

⏳ **Patience** : Cette étape télécharge beaucoup de choses, ça peut prendre 2-5 minutes.

Vous verrez défiler des lignes comme :
```
Collecting fastapi==0.109.0
Downloading fastapi-0.109.0.tar.gz ...
Installing collected packages: ...
```

✅ **Signe de succès** : La commande se termine sans erreur rouge.

### Étape 6 : Configurer la clé API Google

Maintenant, on va dire au programme quelle clé API utiliser.

**Créez le fichier de configuration :**
```powershell
notepad .env
```

Le Bloc-notes s'ouvre. C'est un fichier vide.

**Collez ce texte :**
```
GOOGLE_API_KEY=VOTRE_CLE_ICI
DATA_SOURCE=PYTHON
```

**Remplacez `VOTRE_CLE_ICI`** par la clé que vous avez copiée plus tôt.

Par exemple :
```
GOOGLE_API_KEY=AIzaSyB1abc123def456ghi789jkl012mno345
DATA_SOURCE=PYTHON
```

**Sauvegardez** : `Ctrl + S` puis fermez le Bloc-notes.

### Étape 7 : Installer les dépendances du Frontend

Tapez :
```powershell
cd frontend
```

Puis :
```powershell
npm install
```

> 📝 `npm` est le gestionnaire de packages de Node.js

⏳ **Patience** : 1-3 minutes.

### Étape 8 : Revenir à la racine du projet

Tapez :
```powershell
cd ..
```

> 📝 `..` signifie "dossier parent"

---

## 🚀 Lancer l'application

L'application a **deux parties** qui doivent tourner **en même temps** :
- Le **Backend** (serveur) = le cerveau
- Le **Frontend** (interface) = ce que vous voyez

### Ouvrir deux fenêtres PowerShell

Vous avez besoin de **2 fenêtres PowerShell** ouvertes côte à côte.

**Fenêtre 1** : Cliquez droit sur PowerShell dans la barre des tâches → "Windows PowerShell"

**Fenêtre 2** : Répétez l'opération

### Dans la Fenêtre 1 (Backend) :

Tapez ces commandes **une par une** :

```powershell
cd C:\projetMaintenanceV2\digital_twin
```

```powershell
.\venv\Scripts\Activate
```

```powershell
python backend/api.py
```

**Attendez** de voir ces messages :
```
🚀 Starting Digital Twin Backend Server
✅ Loaded vector store with 41 documents
✅ AI Agent initialized successfully!
✅ Backend ready! Waiting for connections...
```

> ⚠️ Ne fermez pas cette fenêtre ! Le serveur doit rester actif.

### Dans la Fenêtre 2 (Frontend) :

Tapez ces commandes :

```powershell
cd C:\projetMaintenanceV2\digital_twin\frontend
```

```powershell
npm run dev
```

**Attendez** de voir :
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3001/
  ➜  Network: use --host to expose
```

### Ouvrir l'application dans le navigateur

1. Ouvrez votre navigateur internet (Chrome, Firefox, Edge...)
2. Dans la barre d'adresse, tapez : `http://localhost:3001`
3. Appuyez sur Entrée

🎉 **L'interface de l'application devrait apparaître !**

---

## 🎮 Utiliser l'application

### Vue d'ensemble de l'interface

Quand l'application est lancée, vous voyez :

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  🏭 DIGITAL TWIN - GRUNDFOS CR 15            [Python] [Connected]  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐   ┌────────────────────────────────────────┐ │
│  │                  │   │  📊 CAPTEURS EN TEMPS RÉEL             │ │
│  │    MODÈLE 3D     │   │                                        │ │
│  │    DE LA POMPE   │   │   💧 Flow Rate      ⬛⬛⬛⬛⬜ 15.2 m³/h │ │
│  │                  │   │   📊 Pressure       ⬛⬛⬛⬜⬜  4.8 bar  │ │
│  │    (tourne en    │   │   🌡️ Temperature    ⬛⬛⬛⬜⬜  45°C    │ │
│  │     vert si OK)  │   │   📳 Vibration      ⬛⬜⬜⬜⬜  2.1 mm/s │ │
│  │                  │   │   ⚡ Power          ⬛⬛⬛⬜⬜  5.5 kW   │ │
│  └──────────────────┘   │   🔌 Current        ⬛⬛⬛⬜⬜  12.3 A   │ │
│                         └────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────────────────┐│
│  │ ⚙️ INJECTION DE PANNES │  │ 🤖 DIAGNOSTIC IA                   ││
│  │                        │  │                                    ││
│  │ [🟠 Cavitation    ]    │  │ 📋 Diagnosis:                      ││
│  │ [🔴 Bearing       ]    │  │ System is operating normally...    ││
│  │ [🟡 Seal Leak     ]    │  │                                    ││
│  │ [🔴 Impeller      ]    │  │ 🔍 Root Cause:                     ││
│  │ [🔴 Overload      ]    │  │ No anomaly detected                ││
│  │ [⚫ Blockage      ]    │  │                                    ││
│  │                        │  │ ✅ Actions:                        ││
│  │ [🔄 Clear Fault   ]    │  │ Continue normal monitoring         ││
│  └────────────────────────┘  └────────────────────────────────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 📖 GUIDE MANUEL (depuis le PDF Grundfos)                        ││
│  │                                                                 ││
│  │ Injectez une panne pour voir le guide du manuel...              ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Ce que vous pouvez faire

#### 1️⃣ Observer les données en temps réel

Les valeurs des capteurs se mettent à jour **automatiquement toutes les secondes**.

| Capteur | Ce qu'il mesure | Unité | Valeur normale |
|---------|----------------|-------|----------------|
| Flow Rate | Débit d'eau pompée | m³/h | 12-18 |
| Pressure | Pression de sortie | bar | 4-6 |
| Temperature | Température du moteur | °C | 35-55 |
| Vibration | Vibrations mécaniques | mm/s | 0-3 |
| Power | Puissance consommée | kW | 4-7 |
| Current | Intensité électrique | A | 10-15 |

#### 2️⃣ Injecter une panne (simulation)

Cliquez sur un bouton de panne pour **simuler un problème** :

| Bouton | Type de panne | Ce qui se passe |
|--------|---------------|-----------------|
| 🟠 Cavitation | Bulles d'air dans la pompe | Débit ↓, Vibrations ↑, Bruit |
| 🔴 Bearing | Roulement endommagé | Vibrations ↑↑, Température ↑ |
| 🟡 Seal Leak | Fuite au niveau du joint | Pression ↓, Débit ↓ |
| 🔴 Impeller | Roue de pompe abîmée | Débit ↓↓, Puissance ↑ |
| 🔴 Overload | Moteur en surcharge | Courant ↑, Puissance ↑, Temp ↑ |
| ⚫ Blockage | Obstruction | Débit ↓↓↓, Pression ↑↑ |

#### 3️⃣ Observer les changements

Quand vous injectez une panne :
- 📊 Les **valeurs des capteurs changent** (certaines montent, d'autres descendent)
- 🎨 Le **modèle 3D change de couleur** :
  - 🟢 Vert = Normal
  - 🟡 Jaune = Attention
  - 🔴 Rouge = Critique
- 🤖 L'**IA génère un diagnostic** avec :
  - Le problème détecté
  - La cause probable
  - Les actions recommandées

#### 4️⃣ Consulter le guide du manuel

Quand une panne est active, le système **interroge automatiquement le manuel PDF Grundfos** et affiche :
- Le contenu pertinent du manuel
- Les pages de référence

> 💡 Ce n'est pas de l'information inventée ! C'est vraiment extrait du PDF.

#### 5️⃣ Réinitialiser

Cliquez sur **"Clear Fault"** pour revenir à l'état normal.

---

## 📁 Structure du projet

Pour ceux qui veulent comprendre l'organisation des fichiers :

```
digital_twin/
│
├── 📂 backend/                    ← Serveur Python
│   ├── api.py                     ← API REST et WebSocket
│   └── fault_scenarios.py         ← Définition des 6 pannes
│
├── 📂 frontend/                   ← Interface utilisateur
│   ├── 📂 src/
│   │   ├── App.jsx                ← Application principale
│   │   ├── main.jsx               ← Point d'entrée
│   │   ├── index.css              ← Styles
│   │   └── 📂 components/
│   │       ├── PumpViewer3D.jsx   ← Modèle 3D de la pompe
│   │       └── FaultTreeDiagram.jsx ← Guide du manuel
│   ├── 📂 public/models/          ← Fichiers 3D
│   ├── package.json               ← Dépendances Node.js
│   ├── vite.config.js             ← Configuration Vite
│   └── tailwind.config.js         ← Configuration styles
│
├── 📂 src/                        ← Logique métier Python
│   ├── ai_agent.py                ← Agent IA (Gemini)
│   ├── rag_engine.py              ← Recherche dans le PDF
│   ├── simulator.py               ← Simulation des capteurs
│   └── matlab_bridge.py           ← Connexion MATLAB (optionnel)
│
├── 📂 data/                       ← Documents
│   └── grundfos_cr15_manual.pdf   ← Manuel technique
│
├── 📂 chroma_db/                  ← Base de données IA
│
├── .env                           ← Configuration (votre clé API)
├── requirements.txt               ← Liste dépendances Python
├── start_backend.bat              ← Script lancement serveur
├── start_frontend.bat             ← Script lancement interface
│
├── PIPELINE_ACTUEL.md             ← Doc technique détaillée
├── HISTORIQUE_COMPLET.md          ← Historique du projet
└── README.md                      ← Ce fichier !
```

---

## 🔧 Résolution des problèmes

### ❌ "python n'est pas reconnu comme commande interne"

**Problème** : Windows ne sait pas où trouver Python.

**Solutions** :

1. **Vérifiez l'installation** : 
   - Ouvrez le menu Démarrer
   - Cherchez "Python"
   - Si vous le trouvez, c'est installé mais pas dans le PATH

2. **Réinstallez Python** :
   - Téléchargez à nouveau depuis [python.org](https://python.org)
   - ⚠️ Cochez bien **"Add Python to PATH"**
   - Choisissez "Repair" ou "Modify"

3. **Redémarrez PowerShell** après l'installation

### ❌ "npm n'est pas reconnu"

**Problème** : Node.js n'est pas installé ou pas dans le PATH.

**Solution** : Réinstallez Node.js depuis [nodejs.org](https://nodejs.org/) et redémarrez PowerShell.

### ❌ Erreur "GOOGLE_API_KEY" ou "API key not valid"

**Problème** : Le fichier `.env` n'existe pas ou la clé est incorrecte.

**Vérifications** :

1. Le fichier `.env` existe-t-il ?
   ```powershell
   dir .env
   ```
   Si "Cannot find path", créez le fichier (voir Étape 6).

2. Vérifiez le contenu :
   ```powershell
   Get-Content .env
   ```
   
   Vous devez voir :
   ```
   GOOGLE_API_KEY=AIzaSy...
   DATA_SOURCE=PYTHON
   ```

3. Vérifiez qu'il n'y a pas :
   - D'espaces avant ou après la clé
   - De guillemets autour de la clé
   - De retour à la ligne dans la clé

### ❌ "Port 8000 already in use"

**Problème** : Le serveur backend tourne déjà.

**Solution** :
```powershell
Get-Process python | Stop-Process -Force
```

Puis relancez le backend.

### ❌ "Port 3001 already in use"

**Problème** : Le frontend tourne déjà.

**Solution** :
```powershell
Get-Process node | Stop-Process -Force
```

Puis relancez le frontend.

### ❌ Page blanche ou erreur de chargement

**Vérifications** :

1. **Le backend tourne-t-il ?**
   - Regardez la fenêtre du backend
   - Vous devez voir "Backend ready!"

2. **Le frontend tourne-t-il ?**
   - Regardez la fenêtre du frontend
   - Vous devez voir "VITE ready"

3. **Bonne URL ?**
   - Vérifiez que vous êtes sur `http://localhost:3001`
   - Pas `https://` (sans le 's')

4. **Rafraîchissez la page** : `Ctrl + F5`

5. **Ouvrez la console** :
   - Appuyez sur `F12`
   - Cliquez sur "Console"
   - Cherchez les erreurs en rouge

### ❌ "ModuleNotFoundError: No module named 'xxx'"

**Problème** : Une bibliothèque Python manque.

**Solution** :
```powershell
.\venv\Scripts\Activate
pip install -r requirements.txt
```

### ❌ Le diagnostic IA ne fonctionne pas

**Vérifications** :

1. La clé API est-elle valide ?
   - Vérifiez dans le fichier `.env`
   - Testez sur [aistudio.google.com](https://aistudio.google.com)

2. Regardez les logs du backend :
   - Des erreurs apparaissent-elles quand vous demandez un diagnostic ?

### ❌ "Cannot connect to WebSocket"

**Problème** : Le frontend ne peut pas communiquer avec le backend.

**Solutions** :
1. Vérifiez que le backend tourne
2. Vérifiez que vous avez bien `http://` et non `https://`
3. Désactivez temporairement votre antivirus/firewall pour tester

---

## 📚 Pour aller plus loin

### Documentation du projet

| Document | Contenu |
|----------|---------|
| [PIPELINE_ACTUEL.md](PIPELINE_ACTUEL.md) | Comment le système fonctionne techniquement |
| [HISTORIQUE_COMPLET.md](HISTORIQUE_COMPLET.md) | Tout ce qui a été fait et pourquoi |

### Technologies utilisées

| Technologie | Rôle | Pour en savoir plus |
|-------------|------|---------------------|
| **Python** | Langage du serveur | [python.org](https://python.org) |
| **FastAPI** | Framework API | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| **React** | Framework interface | [react.dev](https://react.dev) |
| **Vite** | Outil de build | [vitejs.dev](https://vitejs.dev) |
| **Google Gemini** | IA générative | [ai.google.dev](https://ai.google.dev) |
| **LangChain** | Framework RAG | [langchain.com](https://langchain.com) |
| **ChromaDB** | Base vectorielle | [trychroma.com](https://trychroma.com) |
| **Three.js** | 3D dans le navigateur | [threejs.org](https://threejs.org) |
| **Tailwind CSS** | Framework CSS | [tailwindcss.com](https://tailwindcss.com) |

### Vocabulaire technique

| Terme | Explication simple |
|-------|-------------------|
| **API** | Interface pour que les programmes communiquent entre eux |
| **WebSocket** | Connexion temps réel entre navigateur et serveur |
| **RAG** | Technique pour que l'IA consulte des documents |
| **Embedding** | Conversion de texte en nombres pour l'IA |
| **Vector Store** | Base de données optimisée pour la recherche IA |
| **Digital Twin** | Copie virtuelle d'un équipement réel |

---

## 💡 Conseils

1. **Gardez les deux fenêtres PowerShell ouvertes** pendant l'utilisation
2. **Ne modifiez pas les fichiers** sauf si vous savez ce que vous faites
3. **Sauvegardez votre clé API** dans un endroit sûr
4. **En cas de problème**, relancez tout (fermez PowerShell, rouvrez, relancez)

---

## 🆘 Besoin d'aide ?

Si vous êtes bloqué :
1. Relisez ce README attentivement
2. Cherchez votre erreur dans la section "Résolution des problèmes"
3. Consultez les messages d'erreur dans PowerShell

---

*Dernière mise à jour : 13 Décembre 2025*

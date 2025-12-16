# Présentation du Pipeline Digital Twin

Ce document décrit chaque slide de la présentation `slideready.md`.

## Slide 1 : Objectif & périmètre
**Description :** Présentation des objectifs du projet : utiliser la télémétrie d'une pompe (simulée via MATLAB/Simulink) pour fournir un diagnostic de maintenance assisté par IA (RAG), avec une interface utilisateur pour les techniciens.

## Slide 2 : Architecture globale
**Description :** Vue d'ensemble du flux de données :
1.  **Source :** MATLAB/Simulink envoie les données via MQTT.
2.  **Backend (FastAPI) :** Reçoit les données, gère le RAG (manuel technique) et construit le prompt.
3.  **IA (LLM Gemini) :** Génère le diagnostic ou la réponse au chat.
4.  **Frontend (React) :** Affiche le rapport et l'interface de chat.

## Slide 3 : Concepts clés (définitions)
**Description :** Définition des termes techniques essentiels :
*   **Ingestion :** Transformation du PDF en vecteurs dans ChromaDB.
*   **RAG (Retrieval-Augmented Generation) :** Processus en 3 étapes (Retrieval, Augmentation, Generation) pour ancrer les réponses de l'IA dans la documentation technique.
*   **Embeddings & Vector DB :** Représentation numérique du sens du texte et stockage optimisé pour la recherche de similarité.

## Slide 4 : Ingestion (Manuel PDF → ChromaDB)
**Description :** Détail de la phase "offline" de préparation des données : extraction du texte du manuel, découpage en "chunks", calcul des embeddings et stockage dans ChromaDB.

## Slide 5 : Entrée online (MQTT → Snapshot)
**Description :** Fonctionnement de la réception des données en temps réel. Le backend s'abonne au topic MQTT et maintient un "snapshot" (état instantané) des capteurs (courant, tension, vibration, etc.) qui servira de contexte à l'IA.

## Slide 6 : Capteurs → RAG Query
**Description :** Logique de transformation des données brutes en requête textuelle pour le RAG. Les anomalies détectées (ex: vibration > 5mm/s) sont traduites en mots-clés (ex: "cavitation high vibration") pour rechercher les pages pertinentes dans le manuel.

## Slide 7 : RAG (Retrieval → Augmentation → Generation)
**Description :** Schéma détaillé du flux RAG lors d'une requête :
1.  Conversion de la requête en embedding.
2.  Recherche des chunks similaires dans ChromaDB.
3.  Construction du "prompt augmenté" combinant capteurs, extraits du manuel et consignes.
4.  Génération de la réponse par le LLM.

## Slide 8 : Backend (Endpoints & Orchestration)
**Description :** Présentation des points d'entrée de l'API FastAPI :
*   `POST /api/diagnose` : Pour le rapport complet.
*   `POST /api/chat` : Pour les questions interactives, incluant le contexte capteurs et manuel.

## Slide 9 : Front-end (Rendu "rapport lisible")
**Description :** Rôle de l'interface React : parser la réponse structurée du LLM pour l'afficher sous forme de cartes (Diagnostic, Cause, Actions) lisibles pour un opérateur.

## Slide 10 : Chatbot (Contexte + Mémoire)
**Description :** Explication de la richesse du contexte fourni au chatbot : snapshot actuel, contexte du début du défaut (si applicable), extraits du manuel (RAG) et mémoire sémantique à long terme (préférences utilisateur).

## Slide 11 : Guardrails (Rester "maintenance")
**Description :** Mécanismes de sécurité pour limiter le chatbot au domaine de la maintenance : filtrage par mots-clés et vérification de similarité sémantique.

## Slide 12 : Takeaways
**Description :** Résumé des points clés à retenir sur le pipeline RAG, l'interface utilisateur et la gestion du contexte.

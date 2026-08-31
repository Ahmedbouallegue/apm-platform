# Documentation : Assistant IA DSI (Chatbot)

La plateforme APM intègre un **Assistant IA conversationnel** conçu spécifiquement pour aider les équipes de la DSI à interroger, analyser et piloter le patrimoine applicatif en langage naturel. 

Ce module repose sur la technologie **Google Gemini** et une architecture de type **RAG structuré** (Retrieval-Augmented Generation).

---

## 1. Architecture et Fonctionnement

Contrairement aux systèmes RAG classiques basés sur la vectorisation (embeddings, ChromaDB, etc.) qui sont très utiles pour rechercher dans des textes non-structurés, notre SI contient des données hautement structurées (PostgreSQL).

L'architecture choisie est un **Text-to-SQL assisté par contexte structuré** :

1. **Requête Utilisateur** : L'utilisateur pose une question (ex: *"Quelles sont les applications critiques ?"*).
2. **Context Builder (`context_builder.py`)** : Le système exécute des requêtes ORM optimisées sur la base PostgreSQL pour extraire un "cliché" (snapshot) en temps réel de la DSI (statut des certificats, incidents ouverts, budget des contrats...).
3. **Injection LLM (`gemini_client.py`)** : Le système envoie la question de l'utilisateur, accompagnée de ce cliché JSON et d'un "System Prompt" strict au modèle Google Gemini.
4. **Réponse** : Gemini analyse le contexte JSON et génère une réponse précise en français, formatée en Markdown.

> **Avantage majeur** : Zéro hallucination sur les chiffres, puisque le modèle lit directement le résultat exact de la base de données.

---

## 2. Emplacement dans le Code

L'intégralité du code lié à l'IA est isolée dans l'application Django `apps/chatbot/` :

```text
apps/chatbot/
├── services/
│   ├── context_builder.py   # Extrait les données DB et formatte le contexte JSON
│   ├── gemini_client.py     # Gère la communication avec l'API Google Gemini
│   └── chat_service.py      # Orchestre la session et l'historique utilisateur
├── views.py                 # Points d'entrée HTTP (API AJAX et Vues HTML)
├── serializers.py           # Validation de la requête entrante (DRF)
└── urls_web.py              # Routes URL
```

### Interface Utilisateur
- **Widget Flottant** : Injecté globalement via `templates/base.html` pour tous les utilisateurs connectés.
- **Page dédiée** : Accessible via `/chatbot/` (`templates/chatbot/chat.html`).
- **Assets** : Design dynamique et animations dans `static/css/chatbot.css` et `static/js/chatbot.js`.

---

## 3. Configuration et Prérequis

L'application requiert le package `google-generativeai`.
Dans le fichier `.env`, vous devez impérativement renseigner la variable suivante :

```dotenv
# IA Chatbot DSI — Google Gemini
GEMINI_API_KEY=votre_cle_api_ici
```

Si la clé est absente ou invalide, l'interface renverra un message d'erreur clair sans faire crasher le reste de la plateforme.

---

## 4. Modèle IA Utilisé

Le projet utilise **`gemini-3.6-flash`**, la version la plus récente et optimisée pour des requêtes rapides (faible latence) et complexes.

### System Prompt
Le modèle est contraint par un **System Prompt** strict qui l'oblige à :
- Toujours répondre en français.
- Agir en tant qu'expert DSI.
- Utiliser uniquement les données fournies dans le contexte.
- Signaler l'urgence visuelle (🔴, 🟡, 🟢) pour les dates d'expiration (Certificats SSL, Contrats).

---

## 5. Gestion de l'Historique

L'historique des conversations est géré via les **Sessions Django** (qui sont stockées de façon performante dans **Redis** selon la configuration du projet).
- Chaque utilisateur possède son propre historique de session.
- La limite technique est fixée à **20 messages** pour éviter d'exploser la limite de tokens de l'API lors des envois consécutifs.
- Un bouton "Effacer la conversation" permet de purger la session Redis instantanément (`/chatbot/clear/`).

---

## 6. Domaines de Compétences Actuels (Contexte injecté)

Actuellement, le contexte construit par le `context_builder.py` donne à l'IA la visibilité sur :
- **Applications** : Volume total, répartition par statut et criticité, liste des apps critiques en production.
- **Certificats SSL** : Liste des certificats expirant dans moins de 30 jours, et ceux déjà expirés.
- **Contrats** : Contrats expirant dans les 60 jours, coût annuel global.
- **Incidents** : Incidents ouverts/en cours, volumétrie des incidents résolus ce mois.
- **Serveurs & Fournisseurs** : Inventaire quantitatif.

*Pour étendre les connaissances de l'IA (par exemple ajouter la gestion des licences), il suffit d'ajouter la requête correspondante dans `apps/chatbot/services/context_builder.py`.*

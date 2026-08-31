"""
Gemini Client — Envoie le prompt au modèle Gemini de Google
et retourne la réponse textuelle.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es l'Assistant IA DSI de Topnet — un expert en gestion du patrimoine applicatif.
Tu aides les équipes DSI à analyser et piloter leur SI (Système d'Information).

RÈGLES ABSOLUES :
1. Réponds TOUJOURS en français, de façon claire et structurée.
2. Utilise les données fournies dans le CONTEXTE pour répondre précisément.
3. Si une information n'est pas dans le contexte, dis-le honnêtement.
4. Formate tes réponses avec des listes à puces, tableaux markdown ou titres si pertinent.
5. Sois concis mais complet. Pas de bavardage inutile.
6. Pour les dates d'expiration, signale toujours l'urgence (🔴 urgent, 🟡 attention, 🟢 ok).
7. Tu peux faire des recommandations basées sur les bonnes pratiques DSI/ITIL.

DOMAINES DE COMPÉTENCE :
- Applications (catalogue, criticité, statut, cycle de vie)
- Certificats SSL (expiration, renouvellement)
- Contrats (fournisseurs, coûts, échéances)
- Incidents (ouverture, résolution, impact)
- Serveurs et environnements
- Indicateurs et KPIs DSI
"""


def call_gemini(
    user_message: str,
    context_json: str,
    history: list[dict],
) -> str:
    """
    Appelle l'API Gemini avec le contexte DB + historique de conversation.
    
    Args:
        user_message: La question de l'utilisateur
        context_json: Le snapshot JSON du patrimoine applicatif  
        history: Liste de dicts [{"role": "user"|"model", "parts": "..."}]
    
    Returns:
        La réponse textuelle de Gemini
    """
    try:
        import google.generativeai as genai
    except ImportError:
        logger.error("google-generativeai non installé. Lancez: pip install google-generativeai")
        return "❌ Le module IA n'est pas installé. Contactez l'administrateur système."

    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return "❌ Clé API Gemini non configurée. Ajoutez `GEMINI_API_KEY` dans le fichier `.env`."

    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name="gemini-3.6-flash",
            system_instruction=SYSTEM_PROMPT,
        )

        # Construire le message complet avec contexte
        full_message = f"""CONTEXTE TEMPS RÉEL DE LA PLATEFORME APM TOPNET :
```json
{context_json}
```

QUESTION DE L'UTILISATEUR :
{user_message}"""

        # Construire l'historique de conversation pour Gemini
        gemini_history = []
        for msg in history[-8:]:  # max 8 tours d'historique
            gemini_history.append({
                "role": msg["role"],
                "parts": [msg["content"]],
            })

        # Créer une session de chat avec historique
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(full_message)

        return response.text

    except Exception as exc:
        logger.exception("Erreur appel Gemini API: %s", exc)
        error_msg = str(exc)
        if "API_KEY" in error_msg.upper() or "INVALID" in error_msg.upper():
            return "❌ Clé API Gemini invalide. Vérifiez votre fichier `.env`."
        if "QUOTA" in error_msg.upper() or "RATE" in error_msg.upper():
            return "⚠️ Quota API Gemini dépassé. Réessayez dans quelques secondes."
        return f"❌ Erreur lors de la communication avec l'IA : {error_msg[:200]}"

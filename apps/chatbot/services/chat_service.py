"""
Chat Service — Orchestre le context builder et le client Gemini.
Gère l'historique de conversation via la session Django (stockée dans Redis).
"""
from __future__ import annotations

import logging

from .context_builder import build_context
from .gemini_client import call_gemini

logger = logging.getLogger(__name__)

SESSION_KEY = "chatbot_history"
MAX_HISTORY = 20  # messages max conservés en session


def ask(user_message: str, user, session) -> dict:
    """
    Point d'entrée principal du chatbot.
    
    Args:
        user_message: Le message de l'utilisateur
        user: L'utilisateur Django connecté
        session: La session Django (persistée dans Redis)
    
    Returns:
        dict avec 'answer' (str) et 'history_count' (int)
    """
    # 1. Récupérer l'historique de la session
    history: list[dict] = session.get(SESSION_KEY, [])

    # 2. Construire le contexte DB en temps réel
    try:
        context_json = build_context(user)
    except Exception as exc:
        logger.exception("Erreur construction contexte: %s", exc)
        context_json = '{"error": "Impossible de charger le contexte DSI"}'

    # 3. Appeler Gemini
    answer = call_gemini(
        user_message=user_message,
        context_json=context_json,
        history=history,
    )

    # 4. Mettre à jour l'historique
    history.append({"role": "user", "content": user_message})
    history.append({"role": "model", "content": answer})

    # Garder seulement les MAX_HISTORY derniers messages
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    session[SESSION_KEY] = history
    session.modified = True

    return {
        "answer": answer,
        "history_count": len(history) // 2,
    }


def clear_history(session) -> None:
    """Efface l'historique de conversation de la session."""
    session.pop(SESSION_KEY, None)
    session.modified = True


def get_history(session) -> list[dict]:
    """Retourne l'historique formaté pour l'affichage."""
    raw = session.get(SESSION_KEY, [])
    result = []
    for i in range(0, len(raw) - 1, 2):
        if i + 1 < len(raw):
            result.append({
                "question": raw[i]["content"],
                "answer": raw[i + 1]["content"],
            })
    return result

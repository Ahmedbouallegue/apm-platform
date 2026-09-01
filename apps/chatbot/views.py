"""
Vues du Chatbot IA DSI.
"""
from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .serializers import ChatMessageSerializer
from .services import chat_service

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class ChatbotPageView(View):
    """Page dédiée au chatbot IA."""

    def get(self, request):
        history = chat_service.get_history(request.session)
        return render(request, "chatbot/chat.html", {
            "page_title": "Assistant IA DSI",
            "history": history,
        })


@method_decorator(login_required, name="dispatch")
class ChatbotAskView(View):
    """
    Endpoint AJAX POST — reçoit un message, retourne la réponse IA.
    
    Request JSON: { "message": "..." }
    Response JSON: { "answer": "...", "history_count": N } | { "error": "..." }
    """

    def post(self, request):
        import json

        try:
            body = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Corps de requête JSON invalide."}, status=400)

        serializer = ChatMessageSerializer(data=body)
        if not serializer.is_valid():
            errors = serializer.errors
            first_error = next(iter(errors.values()))[0] if errors else "Données invalides."
            return JsonResponse({"error": str(first_error)}, status=400)

        user_message = serializer.validated_data["message"]

        try:
            result = chat_service.ask(
                user_message=user_message,
                user=request.user,
                session=request.session,
            )
            return JsonResponse(result)
        except Exception as exc:
            logger.exception("Erreur chatbot ask: %s", exc)
            return JsonResponse(
                {"error": "Une erreur interne s'est produite. Réessayez."},
                status=500,
            )


@method_decorator(login_required, name="dispatch")
class ChatbotClearView(View):
    """Efface l'historique de conversation."""

    def post(self, request):
        chat_service.clear_history(request.session)
        return JsonResponse({"status": "cleared"})

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assistant.models import ChatSession, KnowledgeSource
from apps.assistant.permissions import CanManageKnowledge, CanUseAssistant
from apps.assistant.serializers import (
    AskSerializer,
    ChatSessionSerializer,
    ManualKnowledgeSerializer,
)
from apps.assistant.services.indexing import reindex_all, reindex_source
from apps.assistant.services.rag import ask_question
from apps.assistant.tasks import task_reindex_all
from apps.core.views import AppHealthView


class HealthView(AppHealthView):
    app_name = "assistant"


class AskView(APIView):
    permission_classes = [CanUseAssistant]

    @extend_schema(
        tags=["Assistant RAG"],
        request=AskSerializer,
        responses={200: dict},
        summary="Poser une question à l'assistant APM",
    )
    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = None
        session_id = serializer.validated_data.get("session_id")
        if session_id:
            try:
                session = ChatSession.objects.get(pk=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return Response(
                    {"detail": "Session introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        result = ask_question(
            user=request.user,
            question=serializer.validated_data["question"],
            session=session,
        )
        return Response(result)


class ReindexView(APIView):
    permission_classes = [CanManageKnowledge]

    @extend_schema(
        tags=["Assistant RAG"],
        summary="Réindexer le patrimoine APM",
        responses={200: dict},
    )
    def post(self, request):
        async_mode = str(request.data.get("async", "")).lower() in {"1", "true", "yes"}
        if async_mode:
            task = task_reindex_all.delay()
            return Response({"status": "queued", "task_id": task.id})
        stats = reindex_all()
        return Response({"status": "done", "stats": stats})


@extend_schema_view(
    list=extend_schema(tags=["Assistant RAG"]),
    retrieve=extend_schema(tags=["Assistant RAG"]),
)
class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [CanUseAssistant]
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).prefetch_related("messages")


@extend_schema_view(
    list=extend_schema(tags=["Assistant RAG"]),
    retrieve=extend_schema(tags=["Assistant RAG"]),
    create=extend_schema(tags=["Assistant RAG"]),
    destroy=extend_schema(tags=["Assistant RAG"]),
)
class ManualKnowledgeViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageKnowledge]
    serializer_class = ManualKnowledgeSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return KnowledgeSource.objects.filter(source_type=KnowledgeSource.SourceType.MANUAL)

    def perform_create(self, serializer):
        source = serializer.save()
        reindex_source(source)

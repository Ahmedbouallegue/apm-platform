from rest_framework import serializers

from apps.assistant.models import ChatMessage, ChatSession, KnowledgeSource
from apps.core.validators import require_non_empty


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=5, max_length=2000)
    session_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_question(self, value):
        return require_non_empty(value, "La question")


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "role", "content", "sources", "created_at")


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ("id", "title", "created_at", "updated_at", "messages")


class ManualKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeSource
        fields = ("id", "title", "content", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        return require_non_empty(value, "Le titre")

    def validate_content(self, value):
        text = require_non_empty(value, "Le contenu")
        if len(text) < 20:
            raise serializers.ValidationError("Le contenu doit contenir au moins 20 caractères.")
        return text

    def create(self, validated_data):
        validated_data["source_type"] = KnowledgeSource.SourceType.MANUAL
        # source_id unique for manuals
        import uuid

        validated_data["source_id"] = f"manual-{uuid.uuid4().hex[:12]}"
        return super().create(validated_data)

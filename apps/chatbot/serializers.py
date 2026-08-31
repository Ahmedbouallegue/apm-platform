from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    """Valide la requête entrante du chatbot."""

    message = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        error_messages={
            "blank": "Le message ne peut pas être vide.",
            "max_length": "Le message ne doit pas dépasser 2000 caractères.",
        },
    )

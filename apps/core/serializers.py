from rest_framework import serializers


class AppHealthSerializer(serializers.Serializer):
    """Schema for temporary per-app health stubs."""

    app = serializers.CharField()
    status = serializers.CharField()

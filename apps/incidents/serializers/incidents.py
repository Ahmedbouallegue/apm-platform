from rest_framework import serializers

from apps.core.validators import require_non_empty
from apps.incidents.models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    impact_display = serializers.CharField(source="get_impact_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    application_name = serializers.CharField(source="application.name", read_only=True)
    reported_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = (
            "id", "title", "description", "occurred_at", "impact", "impact_display",
            "root_cause", "solution", "status", "status_display", "application",
            "application_name", "reported_by", "reported_by_name", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "created_at", "updated_at", "impact_display", "status_display",
            "application_name", "reported_by_name",
        )

    def get_reported_by_name(self, obj):
        if not obj.reported_by:
            return None
        return obj.reported_by.get_full_name() or obj.reported_by.username


class IncidentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = (
            "title", "description", "occurred_at", "impact", "root_cause",
            "solution", "status", "application",
        )

    def validate_title(self, value):
        return require_non_empty(value, "Le titre")

    def validate_description(self, value):
        return require_non_empty(value, "La description")

    def create(self, validated_data):
        from apps.incidents.services.incidents import incident_create

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return incident_create(data=validated_data, user=user)

    def update(self, instance, validated_data):
        from apps.incidents.services.incidents import incident_update

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return incident_update(incident=instance, data=validated_data, user=user)

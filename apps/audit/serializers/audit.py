from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id", "action", "entity", "entity_id", "details",
            "occurred_at", "user", "user_name", "ip_address",
        )
        read_only_fields = fields

    def get_user_name(self, obj):
        if not obj.user:
            return None
        return obj.user.get_full_name() or obj.user.username

from rest_framework import serializers

from apps.core.validators import require_non_empty
from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id", "title", "message", "notification_type", "notification_type_display",
            "sent_at", "status", "status_display", "user", "user_name", "link",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "sent_at", "created_at", "updated_at",
            "notification_type_display", "status_display", "user_name",
        )

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class NotificationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("title", "message", "notification_type", "user", "link", "status")

    def validate_title(self, value):
        return require_non_empty(value, "Le titre")

    def validate_message(self, value):
        return require_non_empty(value, "Le message")

    def create(self, validated_data):
        from apps.notifications.services.notifications import notification_create

        return notification_create(data=validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance

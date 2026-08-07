from rest_framework import serializers

from apps.core.validators import require_non_empty, validate_resource_label, validate_server_name
from apps.servers.models import Server


class ServerSerializer(serializers.ModelSerializer):
    server_type_display = serializers.CharField(source="get_server_type_display", read_only=True)
    env_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Server
        fields = (
            "id",
            "name",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "datacenter",
            "server_type",
            "server_type_display",
            "is_active",
            "notes",
            "env_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "server_type_display",
            "env_count",
        )


class ServerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = (
            "name",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "datacenter",
            "server_type",
            "is_active",
            "notes",
        )

    def validate_name(self, value):
        name = validate_server_name(value)
        qs = Server.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un serveur avec ce nom existe déjà.")
        return name

    def validate_ip_address(self, value):
        ip = require_non_empty(str(value or ""), "L'adresse IP")
        qs = Server.objects.filter(ip_address=ip, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Cette adresse IP est déjà attribuée à un autre serveur."
            )
        return ip

    def validate_cpu(self, value):
        return validate_resource_label(value, "CPU")

    def validate_ram(self, value):
        return validate_resource_label(value, "RAM")

    def create(self, validated_data):
        from apps.servers.services.servers import server_create

        return server_create(data=validated_data, user=getattr(self.context.get("request"), "user", None))

    def update(self, instance, validated_data):
        from apps.servers.services.servers import server_update

        return server_update(
            server=instance,
            data=validated_data,
            user=getattr(self.context.get("request"), "user", None),
        )

from django.db.models import Q
from rest_framework import serializers

from apps.servers.models import Server, ServerMetric


class ServerMetricWriteSerializer(serializers.Serializer):
    """Accepts data from VM agents — matches server by hostname/IP."""

    hostname = serializers.CharField(max_length=255)
    cpu_percent = serializers.FloatField(min_value=0, max_value=100)
    memory_total = serializers.IntegerField(min_value=0)
    memory_used = serializers.IntegerField(min_value=0)
    memory_percent = serializers.FloatField(min_value=0, max_value=100)
    disk_total = serializers.IntegerField(min_value=0)
    disk_used = serializers.IntegerField(min_value=0)
    disk_percent = serializers.FloatField(min_value=0, max_value=100)
    net_bytes_sent = serializers.IntegerField(min_value=0, default=0)
    net_bytes_recv = serializers.IntegerField(min_value=0, default=0)
    load_avg_1 = serializers.FloatField(default=0)
    uptime_seconds = serializers.FloatField(min_value=0, default=0)

    def validate_hostname(self, value):
        try:
            self._server = Server.objects.get(
                Q(name__iexact=value) | Q(ip_address=value),
                is_deleted=False,
            )
        except Server.DoesNotExist:
            raise serializers.ValidationError(
                f"Aucun serveur actif ne correspond au hostname « {value} »."
            )
        return value

    def create(self, validated_data):
        return ServerMetric.objects.create(server=self._server, **validated_data)


class ServerMetricReadSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source="server.name", read_only=True)

    class Meta:
        model = ServerMetric
        fields = (
            "id",
            "server",
            "server_name",
            "hostname",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "memory_total",
            "memory_used",
            "disk_total",
            "disk_used",
            "net_bytes_sent",
            "net_bytes_recv",
            "load_avg_1",
            "uptime_seconds",
            "collected_at",
        )

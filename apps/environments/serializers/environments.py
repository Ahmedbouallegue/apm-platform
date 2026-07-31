from rest_framework import serializers

from apps.core.validators import require_non_empty, validate_optional_url, validate_resource_label
from apps.environments.models import Environment


class EnvironmentSerializer(serializers.ModelSerializer):
    env_type_display = serializers.CharField(source="get_env_type_display", read_only=True)
    application_name = serializers.CharField(source="application.name", read_only=True)
    server_name = serializers.CharField(source="server.name", read_only=True, default=None)

    class Meta:
        model = Environment
        fields = (
            "id",
            "application",
            "application_name",
            "server",
            "server_name",
            "name",
            "env_type",
            "env_type_display",
            "url",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "hosting_provider",
            "docker",
            "kubernetes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "env_type_display",
            "application_name",
            "server_name",
        )


class EnvironmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = (
            "application",
            "server",
            "name",
            "env_type",
            "url",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "hosting_provider",
            "docker",
            "kubernetes",
            "is_active",
        )

    def validate_name(self, value):
        return require_non_empty(value, "Le nom")

    def validate_url(self, value):
        return validate_optional_url(value)

    def validate_cpu(self, value):
        return validate_resource_label(value, "CPU")

    def validate_ram(self, value):
        return validate_resource_label(value, "RAM")

    def validate(self, attrs):
        application = attrs.get("application", getattr(self.instance, "application", None))
        env_type = attrs.get("env_type", getattr(self.instance, "env_type", None))
        if application and env_type:
            qs = Environment.objects.filter(application=application, env_type=env_type)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        "env_type": (
                            "Cet environnement (DEV/RECETTE/PREPROD/PROD) existe déjà "
                            "pour cette application."
                        )
                    }
                )
        server = attrs.get("server")
        if server is None and self.instance is None:
            server = None
        elif "server" not in attrs and self.instance:
            server = self.instance.server
        if server and getattr(server, "is_deleted", False):
            raise serializers.ValidationError(
                {"server": "Ce serveur est archivé et ne peut pas être sélectionné."}
            )
        return attrs

    def create(self, validated_data):
        from apps.environments.services.environments import environment_create

        return environment_create(data=validated_data)

    def update(self, instance, validated_data):
        from apps.environments.services.environments import environment_update

        return environment_update(environment=instance, data=validated_data)

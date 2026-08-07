from rest_framework import serializers

from apps.dependencies.models import Dependency


class DependencySerializer(serializers.ModelSerializer):
    dependency_type_display = serializers.CharField(source="get_dependency_type_display", read_only=True)
    source_name = serializers.CharField(source="source_application.name", read_only=True)
    target_name = serializers.CharField(source="target_application.name", read_only=True, allow_null=True)

    class Meta:
        model = Dependency
        fields = (
            "id", "dependency_type", "dependency_type_display", "description",
            "source_application", "source_name", "target_application", "target_name",
            "target_external", "is_active", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "created_at", "updated_at", "dependency_type_display",
            "source_name", "target_name",
        )


class DependencyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependency
        fields = (
            "dependency_type", "description", "source_application",
            "target_application", "target_external", "is_active",
        )

    def validate(self, attrs):
        source = attrs.get("source_application", getattr(self.instance, "source_application", None))
        target = attrs.get("target_application", getattr(self.instance, "target_application", None))
        external = attrs.get("target_external", getattr(self.instance, "target_external", ""))
        if not target and not external:
            raise serializers.ValidationError("Indiquez une application cible ou une cible externe.")
        if target and external:
            raise serializers.ValidationError("Choisissez soit une application cible, soit une cible externe.")
        if source and target and source.pk == target.pk:
            raise serializers.ValidationError("Une application ne peut pas dépendre d'elle-même.")
        return attrs

    def create(self, validated_data):
        from apps.dependencies.services.dependencies import dependency_create

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return dependency_create(data=validated_data, user=user)

    def update(self, instance, validated_data):
        from apps.dependencies.services.dependencies import dependency_update

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return dependency_update(dependency=instance, data=validated_data, user=user)

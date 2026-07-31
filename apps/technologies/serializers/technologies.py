from rest_framework import serializers

from apps.core.validators import validate_tech_name, validate_version
from apps.technologies.models import Technology


class TechnologySerializer(serializers.ModelSerializer):
    tech_type_display = serializers.CharField(source="get_tech_type_display", read_only=True)
    app_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Technology
        fields = (
            "id",
            "name",
            "tech_type",
            "tech_type_display",
            "version",
            "description",
            "app_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "tech_type_display", "app_count")


class TechnologyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ("name", "tech_type", "version", "description")

    def validate_name(self, value):
        return validate_tech_name(value)

    def validate_version(self, value):
        return validate_version(value)

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", None))
        version = attrs.get("version", getattr(self.instance, "version", "") if self.instance else "")
        version = version or ""
        if name:
            qs = Technology.objects.filter(name__iexact=name, version=version)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Cette technologie (nom + version) existe déjà dans le référentiel."
                )
        return attrs

    def create(self, validated_data):
        from apps.technologies.services.technologies import technology_create

        return technology_create(data=validated_data)

    def update(self, instance, validated_data):
        from apps.technologies.services.technologies import technology_update

        return technology_update(technology=instance, data=validated_data)

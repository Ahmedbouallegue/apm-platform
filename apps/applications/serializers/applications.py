from rest_framework import serializers

from apps.applications.models import Application
from apps.core.validators import validate_app_name, validate_date_range
from apps.technologies.models import Technology


class TechnologyNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ("id", "name", "tech_type", "version")


class ApplicationSerializer(serializers.ModelSerializer):
    criticality_display = serializers.CharField(source="get_criticality_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True, default=None)
    technologies = TechnologyNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = (
            "id",
            "name",
            "description",
            "criticality",
            "criticality_display",
            "status",
            "status_display",
            "go_live_date",
            "end_of_life_date",
            "user_count",
            "business_unit",
            "owner",
            "owner_username",
            "technologies",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ApplicationWriteSerializer(serializers.ModelSerializer):
    technology_ids = serializers.PrimaryKeyRelatedField(
        source="technologies",
        queryset=Technology.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Application
        fields = (
            "name",
            "description",
            "criticality",
            "status",
            "go_live_date",
            "end_of_life_date",
            "user_count",
            "business_unit",
            "owner",
            "technology_ids",
        )

    def validate_name(self, value):
        name = validate_app_name(value)
        qs = Application.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Une application avec ce nom existe déjà.")
        return name

    def validate_user_count(self, value):
        if value is None:
            return 0
        if value < 0:
            raise serializers.ValidationError("Le nombre d'utilisateurs ne peut pas être négatif.")
        if value > 10_000_000:
            raise serializers.ValidationError("Nombre d'utilisateurs trop élevé.")
        return value

    def validate(self, attrs):
        go_live = attrs.get("go_live_date", getattr(self.instance, "go_live_date", None))
        end = attrs.get("end_of_life_date", getattr(self.instance, "end_of_life_date", None))
        try:
            validate_date_range(
                go_live,
                end,
                start_label="Date de mise en production",
                end_label="Date de fin de vie",
            )
        except Exception as exc:
            raise serializers.ValidationError({"end_of_life_date": list(getattr(exc, "messages", [str(exc)]))}) from exc
        return attrs

    def create(self, validated_data):
        from apps.applications.services.applications import application_create

        request = self.context.get("request")
        actor = request.user if request and request.user.is_authenticated else None
        return application_create(data=validated_data, user=actor)

    def update(self, instance, validated_data):
        from apps.applications.services.applications import application_update

        request = self.context.get("request")
        actor = request.user if request and request.user.is_authenticated else None
        return application_update(application=instance, data=validated_data, user=actor)

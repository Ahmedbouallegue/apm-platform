from rest_framework import serializers

from apps.core.validators import require_non_empty, validate_date_range
from apps.domains.models import Domain


class DomainSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    application_name = serializers.CharField(
        source="application.name", read_only=True, allow_null=True
    )
    environment_name = serializers.CharField(
        source="environment.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Domain
        fields = (
            "id",
            "fqdn",
            "registrar",
            "dns_provider",
            "registered_at",
            "expires_at",
            "status",
            "status_display",
            "application",
            "application_name",
            "environment",
            "environment_name",
            "is_primary",
            "auto_renew",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "status_display",
            "application_name",
            "environment_name",
        )


class DomainWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = (
            "fqdn",
            "registrar",
            "dns_provider",
            "registered_at",
            "expires_at",
            "status",
            "application",
            "environment",
            "is_primary",
            "auto_renew",
            "is_active",
            "notes",
        )

    def validate_fqdn(self, value):
        fqdn = require_non_empty(value, "Le nom de domaine").lower()
        qs = Domain.objects.filter(fqdn__iexact=fqdn, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce nom de domaine existe déjà.")
        return fqdn

    def validate(self, attrs):
        start = attrs.get("registered_at", getattr(self.instance, "registered_at", None))
        end = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        try:
            validate_date_range(
                start,
                end,
                start_label="Date d'enregistrement",
                end_label="Date d'expiration",
            )
        except Exception as exc:
            raise serializers.ValidationError({"expires_at": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        from apps.domains.services.domains import domain_create

        return domain_create(data=validated_data, user=getattr(self.context.get("request"), "user", None))

    def update(self, instance, validated_data):
        from apps.domains.services.domains import domain_update

        return domain_update(
            domain=instance,
            data=validated_data,
            user=getattr(self.context.get("request"), "user", None),
        )

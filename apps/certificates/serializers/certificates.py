from rest_framework import serializers

from apps.certificates.models import Certificate
from apps.core.validators import require_non_empty, validate_date_range


class CertificateSerializer(serializers.ModelSerializer):
    certificate_type_display = serializers.CharField(
        source="get_certificate_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    application_name = serializers.CharField(
        source="application.name", read_only=True, allow_null=True
    )
    environment_name = serializers.CharField(
        source="environment.name", read_only=True, allow_null=True
    )
    domain_fqdn = serializers.CharField(source="domain.fqdn", read_only=True, allow_null=True)

    class Meta:
        model = Certificate
        fields = (
            "id",
            "common_name",
            "san_domains",
            "issuer",
            "certificate_type",
            "certificate_type_display",
            "status",
            "status_display",
            "application",
            "application_name",
            "environment",
            "environment_name",
            "domain",
            "domain_fqdn",
            "issued_at",
            "expires_at",
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
            "certificate_type_display",
            "status_display",
            "application_name",
            "environment_name",
            "domain_fqdn",
        )


class CertificateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = (
            "common_name",
            "san_domains",
            "issuer",
            "certificate_type",
            "status",
            "application",
            "environment",
            "domain",
            "issued_at",
            "expires_at",
            "auto_renew",
            "is_active",
            "notes",
        )

    def validate_common_name(self, value):
        return require_non_empty(value, "Le nom commun").lower()

    def validate(self, attrs):
        start = attrs.get("issued_at", getattr(self.instance, "issued_at", None))
        end = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        try:
            validate_date_range(
                start,
                end,
                start_label="Date d'émission",
                end_label="Date d'expiration",
            )
        except Exception as exc:
            raise serializers.ValidationError({"expires_at": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        from apps.certificates.services.certificates import certificate_create

        return certificate_create(data=validated_data, user=getattr(self.context.get("request"), "user", None))

    def update(self, instance, validated_data):
        from apps.certificates.services.certificates import certificate_update

        return certificate_update(
            certificate=instance,
            data=validated_data,
            user=getattr(self.context.get("request"), "user", None),
        )

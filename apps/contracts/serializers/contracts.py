from rest_framework import serializers

from apps.contracts.models import Contract
from apps.core.validators import require_non_empty, validate_date_range


class ContractSerializer(serializers.ModelSerializer):
    contract_type_display = serializers.CharField(
        source="get_contract_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    application_name = serializers.CharField(
        source="application.name", read_only=True, allow_null=True
    )
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            "id",
            "reference",
            "title",
            "vendor",
            "vendor_name",
            "application",
            "application_name",
            "contract_type",
            "contract_type_display",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "annual_cost",
            "currency",
            "auto_renew",
            "sla_level",
            "owner",
            "owner_name",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "contract_type_display",
            "status_display",
            "vendor_name",
            "application_name",
            "owner_name",
        )

    def get_owner_name(self, obj):
        if not obj.owner:
            return None
        return obj.owner.get_full_name() or obj.owner.username


class ContractWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = (
            "reference",
            "title",
            "vendor",
            "application",
            "contract_type",
            "status",
            "start_date",
            "end_date",
            "annual_cost",
            "currency",
            "auto_renew",
            "sla_level",
            "owner",
            "is_active",
            "notes",
        )

    def validate_reference(self, value):
        ref = require_non_empty(value, "La référence")
        qs = Contract.objects.filter(reference__iexact=ref, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Cette référence de contrat existe déjà.")
        return ref

    def validate_title(self, value):
        return require_non_empty(value, "L'intitulé")

    def validate_vendor(self, value):
        if value.is_deleted or not value.is_active:
            raise serializers.ValidationError("Le fournisseur sélectionné est inactif ou archivé.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        try:
            validate_date_range(start, end)
        except Exception as exc:
            raise serializers.ValidationError({"end_date": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        from apps.contracts.services.contracts import contract_create

        return contract_create(data=validated_data, user=getattr(self.context.get("request"), "user", None))

    def update(self, instance, validated_data):
        from apps.contracts.services.contracts import contract_update

        return contract_update(
            contract=instance,
            data=validated_data,
            user=getattr(self.context.get("request"), "user", None),
        )

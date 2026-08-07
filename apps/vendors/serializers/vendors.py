from rest_framework import serializers

from apps.core.validators import require_non_empty, validate_optional_url, validate_phone
from apps.vendors.models import Vendor


class VendorSerializer(serializers.ModelSerializer):
    vendor_type_display = serializers.CharField(source="get_vendor_type_display", read_only=True)
    contract_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Vendor
        fields = (
            "id",
            "name",
            "vendor_type",
            "vendor_type_display",
            "contact_name",
            "contact_email",
            "contact_phone",
            "website",
            "address",
            "is_active",
            "notes",
            "contract_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "vendor_type_display", "contract_count")


class VendorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "name",
            "vendor_type",
            "contact_name",
            "contact_email",
            "contact_phone",
            "website",
            "address",
            "is_active",
            "notes",
        )

    def validate_name(self, value):
        name = require_non_empty(value, "Le nom")
        qs = Vendor.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un fournisseur avec ce nom existe déjà.")
        return name

    def validate_contact_phone(self, value):
        return validate_phone(value)

    def validate_website(self, value):
        return validate_optional_url(value)

    def create(self, validated_data):
        from apps.vendors.services.vendors import vendor_create

        return vendor_create(data=validated_data)

    def update(self, instance, validated_data):
        from apps.vendors.services.vendors import vendor_update

        return vendor_update(vendor=instance, data=validated_data)

from rest_framework import serializers

from apps.core.validators import require_non_empty
from apps.documents.models import Document, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        name = require_non_empty(value, "Le nom du tag")
        qs = Tag.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce tag existe déjà.")
        return name

    def create(self, validated_data):
        from apps.documents.services.documents import tag_create

        return tag_create(name=validated_data["name"])


class DocumentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    application_name = serializers.CharField(source="application.name", read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id", "title", "file_type", "category", "category_display", "description",
            "file", "uploaded_at", "application", "application_name", "uploaded_by",
            "uploaded_by_name", "tags", "is_active", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "uploaded_at", "created_at", "updated_at", "category_display",
            "application_name", "uploaded_by_name", "tags",
        )

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return None
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username


class DocumentWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)

    class Meta:
        model = Document
        fields = (
            "title", "file_type", "category", "description", "file",
            "application", "tags", "is_active",
        )

    def validate_title(self, value):
        return require_non_empty(value, "Le nom du fichier")

    def create(self, validated_data):
        from apps.documents.services.documents import document_create

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return document_create(data=validated_data, user=user)

    def update(self, instance, validated_data):
        from apps.documents.services.documents import document_update

        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return document_update(document=instance, data=validated_data, user=user)

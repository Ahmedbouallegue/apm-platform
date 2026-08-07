from django.contrib import admin

from apps.documents.models import Document, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "file_type",
        "application",
        "uploaded_by",
        "uploaded_at",
        "is_active",
    )
    list_filter = ("category", "is_active", "is_deleted")
    search_fields = ("title", "description", "file_type")
    raw_id_fields = ("application", "uploaded_by")
    filter_horizontal = ("tags",)

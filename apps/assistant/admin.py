from django.contrib import admin

from apps.assistant.models import ChatMessage, ChatSession, KnowledgeChunk, KnowledgeSource


class KnowledgeChunkInline(admin.TabularInline):
    model = KnowledgeChunk
    extra = 0
    readonly_fields = ("chunk_index", "token_count", "created_at")
    fields = ("chunk_index", "content", "token_count", "created_at")


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "source_id", "is_active", "updated_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("title", "content", "source_id")
    inlines = [KnowledgeChunkInline]


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "updated_at")
    search_fields = ("title", "user__username")
    inlines = [ChatMessageInline]

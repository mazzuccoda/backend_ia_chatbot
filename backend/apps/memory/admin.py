from django.contrib import admin

from .models import ConversationMemory


@admin.register(ConversationMemory)
class ConversationMemoryAdmin(admin.ModelAdmin):
    list_display = ("user_id", "conversation_id", "key", "updated_at")
    list_filter = ("user_id", "conversation_id")
    search_fields = ("user_id", "conversation_id", "key")
    readonly_fields = ("created_at", "updated_at")

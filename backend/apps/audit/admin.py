from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("tool_used", "status", "user_id", "execution_time_ms", "created_at")
    list_filter = ("status", "tool_used", "created_at")
    search_fields = ("user_id", "conversation_id", "message")
    readonly_fields = (
        "user_id",
        "conversation_id",
        "message",
        "intent",
        "tool_used",
        "input_payload",
        "output_payload",
        "sql_generated",
        "status",
        "error_code",
        "execution_time_ms",
        "idempotency_key",
        "endpoint",
        "created_at",
    )

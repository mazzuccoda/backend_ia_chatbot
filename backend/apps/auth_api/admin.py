from django.contrib import admin

from .models import ApiClient


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "scopes", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("key_hash", "created_at")

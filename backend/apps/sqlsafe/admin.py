from django.contrib import admin

from .models import Dimension, Metrica, VistaPermitida


class DimensionInline(admin.TabularInline):
    model = Dimension
    extra = 1


@admin.register(Metrica)
class MetricaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "vista", "activa", "expone_tool_determinista", "permite_flexible", "handler")
    list_filter = ("activa", "expone_tool_determinista", "permite_flexible")
    search_fields = ("nombre", "sinonimos", "descripcion")
    inlines = [DimensionInline]


@admin.register(VistaPermitida)
class VistaPermitidaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

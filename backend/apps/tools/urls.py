from django.urls import path

from .views import ConsultaFlexibleView, ToolCatalogView, ToolRunView

urlpatterns = [
    path("", ToolCatalogView.as_view(), name="tool-catalog"),
    path("consulta-flexible/", ConsultaFlexibleView.as_view(), name="consulta-flexible"),
    path("<str:nombre_metrica>/", ToolRunView.as_view(), name="tool-run"),
]

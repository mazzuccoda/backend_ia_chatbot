from django.urls import path

from .views import ChartGenerateView

urlpatterns = [
    path("generate/", ChartGenerateView.as_view(), name="chart-generate"),
]

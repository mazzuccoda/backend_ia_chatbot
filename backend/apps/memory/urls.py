from django.urls import path

from .views import MemoryGetView, MemorySaveView

urlpatterns = [
    path("save/", MemorySaveView.as_view(), name="memory-save"),
    path("get/", MemoryGetView.as_view(), name="memory-get"),
]

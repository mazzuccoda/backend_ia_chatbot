from django.db import models


class AppConfig(models.Model):
    """Runtime-editable configuration key/value store."""

    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key: str, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

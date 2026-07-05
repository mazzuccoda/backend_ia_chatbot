from django.core.exceptions import ValidationError
from django.db import models


class VistaPermitida(models.Model):
    """Whitelist of database views that tools are allowed to query."""

    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vista Permitida"
        verbose_name_plural = "Vistas Permitidas"

    def __str__(self):
        return self.nombre


class Metrica(models.Model):
    """Defines a queryable metric backed by a database view."""

    nombre = models.CharField(max_length=100, unique=True)
    vista = models.CharField(max_length=100)
    filtro_fijo = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    sinonimos = models.JSONField(default=list, blank=True)
    medida_columna = models.CharField(max_length=50)
    medida_alias = models.CharField(max_length=50, default="tariff_value")
    unidad_columna = models.CharField(max_length=50, blank=True)
    moneda_columna = models.CharField(max_length=50, blank=True)
    orden_por = models.CharField(max_length=50, default="valid_from")
    orden_desc = models.BooleanField(default=True)
    expone_tool_determinista = models.BooleanField(default=True)
    permite_flexible = models.BooleanField(default=True)
    handler = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre de función registrada en handlers.py; vacío = lookup genérico",
    )
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Métrica"
        verbose_name_plural = "Métricas"

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.vista:
            if not VistaPermitida.objects.filter(nombre=self.vista, activa=True).exists():
                raise ValidationError(
                    {"vista": f"La vista '{self.vista}' no está en la lista de vistas permitidas activas."}
                )


class Dimension(models.Model):
    TIPO_CHOICES = [
        ("texto", "texto"),
        ("periodo", "periodo"),
        ("numero", "numero"),
    ]
    COMPARADOR_CHOICES = [
        ("=", "="),
        ("ILIKE", "ILIKE"),
    ]

    metrica = models.ForeignKey(Metrica, related_name="dimensiones", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    columna = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    requerido = models.BooleanField(default=False)
    comparador = models.CharField(max_length=10, default="=", choices=COMPARADOR_CHOICES)

    class Meta:
        verbose_name = "Dimensión"
        verbose_name_plural = "Dimensiones"
        unique_together = ("metrica", "nombre")

    def __str__(self):
        return f"{self.metrica.nombre}.{self.nombre}"

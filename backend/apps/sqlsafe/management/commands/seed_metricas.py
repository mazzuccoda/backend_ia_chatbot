"""Seed initial metrics and allowed views if they don't already exist."""

import logging

from django.core.management.base import BaseCommand

from apps.sqlsafe.models import Dimension, Metrica, VistaPermitida

logger = logging.getLogger(__name__)

INITIAL_VIEWS = [
    "vw_tarifas",
    "vw_budget_vs_real",
    "vw_costos_transporte",
    "vw_volumen",
    "vw_kpi_logistica",
]

INITIAL_METRICAS = [
    {
        "nombre": "tarifa_flete",
        "vista": "vw_tarifas",
        "filtro_fijo": "tariff_type = 'flete'",
        "descripcion": "Consulta la tarifa de flete vigente filtrada por origen, destino y otros parámetros.",
        "sinonimos": ["flete", "transporte", "freight"],
        "medida_columna": "tariff_value",
        "medida_alias": "tariff_value",
        "unidad_columna": "unit",
        "moneda_columna": "currency",
        "orden_por": "valid_from",
        "orden_desc": True,
        "dimensiones": [
            {"nombre": "origin", "columna": "origin", "tipo": "texto", "requerido": True, "comparador": "ILIKE"},
            {"nombre": "destination", "columna": "destination", "tipo": "texto", "requerido": True, "comparador": "ILIKE"},
            {"nombre": "mode", "columna": "mode", "tipo": "texto", "requerido": False, "comparador": "="},
            {"nombre": "client", "columna": "client", "tipo": "texto", "requerido": False, "comparador": "ILIKE"},
            {"nombre": "period", "columna": "period", "tipo": "periodo", "requerido": False, "comparador": "="},
        ],
    },
    {
        "nombre": "tarifa_almacenaje",
        "vista": "vw_tarifas",
        "filtro_fijo": "tariff_type = 'almacenaje'",
        "descripcion": "Consulta la tarifa de almacenaje vigente filtrada por depósito y cliente.",
        "sinonimos": ["almacenaje", "storage", "warehousing"],
        "medida_columna": "tariff_value",
        "medida_alias": "tariff_value",
        "unidad_columna": "unit",
        "moneda_columna": "currency",
        "orden_por": "valid_from",
        "orden_desc": True,
        "dimensiones": [
            {"nombre": "warehouse", "columna": "warehouse", "tipo": "texto", "requerido": True, "comparador": "ILIKE"},
            {"nombre": "client", "columna": "client", "tipo": "texto", "requerido": False, "comparador": "ILIKE"},
            {"nombre": "period", "columna": "period", "tipo": "periodo", "requerido": False, "comparador": "="},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed initial metrics, dimensions, and allowed views"

    def handle(self, *args, **options):
        # Create allowed views
        for view_name in INITIAL_VIEWS:
            obj, created = VistaPermitida.objects.get_or_create(nombre=view_name, defaults={"activa": True})
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created VistaPermitida: {view_name}"))

        # Create metrics with dimensions
        for m_data in INITIAL_METRICAS:
            dims_data = m_data.pop("dimensiones")
            metrica, created = Metrica.objects.get_or_create(
                nombre=m_data["nombre"],
                defaults=m_data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Metrica: {metrica.nombre}"))
                for d_data in dims_data:
                    Dimension.objects.create(metrica=metrica, **d_data)
                    self.stdout.write(f"  + Dimension: {d_data['nombre']}")
            else:
                self.stdout.write(f"Metrica '{metrica.nombre}' already exists — skipping.")
            # Restore for potential re-run
            m_data["dimensiones"] = dims_data

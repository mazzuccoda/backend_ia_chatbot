import pytest
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.sqlsafe.models import Dimension, Metrica, VistaPermitida


@pytest.fixture
def setup_metrica(db):
    """Create a test metric with an actual test table behind it."""
    from django.db import connection

    # Create a real test view
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE OR REPLACE VIEW vw_test_metric AS
            SELECT
                'Buenos Aires'::text AS origin,
                'Mendoza'::text AS destination,
                150.50::numeric AS tariff_value,
                'USD'::text AS currency,
                'per_ton'::text AS unit,
                '2024-01'::text AS valid_from,
                'flete'::text AS tariff_type
        """)

    VistaPermitida.objects.get_or_create(nombre="vw_test_metric", defaults={"activa": True})

    metrica = Metrica.objects.create(
        nombre="test_metric",
        vista="vw_test_metric",
        filtro_fijo="tariff_type = 'flete'",
        descripcion="Test metric for pytest",
        medida_columna="tariff_value",
        medida_alias="tariff_value",
        unidad_columna="unit",
        moneda_columna="currency",
        orden_por="valid_from",
        orden_desc=True,
        expone_tool_determinista=True,
        permite_flexible=True,
    )
    Dimension.objects.create(metrica=metrica, nombre="origin", columna="origin", tipo="texto", requerido=True, comparador="ILIKE")
    Dimension.objects.create(metrica=metrica, nombre="destination", columna="destination", tipo="texto", requerido=False, comparador="ILIKE")
    return metrica


@pytest.mark.django_db
class TestToolCatalog:
    def test_catalog_lists_active_metrics(self, auth_headers, setup_metrica):
        client = APIClient()
        response = client.get("/api/v1/tools/", **auth_headers)
        assert response.status_code == 200
        data = response.json()
        names = [t["name"] for t in data["data"]]
        assert "test_metric" in names

    def test_new_metric_appears_automatically(self, auth_headers, setup_metrica):
        """Creating a new Metrica via ORM makes it appear in the catalog — no code changes needed."""
        VistaPermitida.objects.get_or_create(nombre="vw_new_test", defaults={"activa": True})
        Metrica.objects.create(
            nombre="dynamic_new_tool",
            vista="vw_new_test",
            descripcion="A dynamically added tool",
            medida_columna="value",
            activa=True,
            expone_tool_determinista=True,
        )
        client = APIClient()
        response = client.get("/api/v1/tools/", **auth_headers)
        names = [t["name"] for t in response.json()["data"]]
        assert "dynamic_new_tool" in names


@pytest.mark.django_db
class TestToolRun:
    def test_deterministic_tool_returns_data(self, auth_headers, setup_metrica):
        client = APIClient()
        response = client.post(
            "/api/v1/tools/test_metric/",
            data={"origin": "Buenos Aires"},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "tariff_value" in data
        assert data["currency"] == "USD"

    def test_missing_required_param(self, auth_headers, setup_metrica):
        client = APIClient()
        response = client.post(
            "/api/v1/tools/test_metric/",
            data={},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "MISSING_REQUIRED_PARAM"

    def test_nonexistent_metric(self, auth_headers):
        client = APIClient()
        response = client.post(
            "/api/v1/tools/does_not_exist/",
            data={},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "METRIC_NOT_FOUND"

    def test_view_not_found(self, auth_headers, db):
        VistaPermitida.objects.get_or_create(nombre="vw_nonexistent", defaults={"activa": True})
        Metrica.objects.create(
            nombre="broken_metric",
            vista="vw_nonexistent",
            medida_columna="val",
            expone_tool_determinista=True,
        )
        client = APIClient()
        response = client.post(
            "/api/v1/tools/broken_metric/",
            data={},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "VIEW_NOT_FOUND"


@pytest.mark.django_db
class TestIdempotency:
    def test_idempotency_key_prevents_duplicate_audit(self, auth_headers, setup_metrica):
        client = APIClient()
        headers = {**auth_headers, "HTTP_IDEMPOTENCY_KEY": "idem-123"}

        r1 = client.post(
            "/api/v1/tools/test_metric/",
            data={"origin": "Buenos Aires"},
            format="json",
            **headers,
        )
        assert r1.status_code == 200

        r2 = client.post(
            "/api/v1/tools/test_metric/",
            data={"origin": "Buenos Aires"},
            format="json",
            **headers,
        )
        assert r2.status_code == 200

        # Only one AuditLog should be created
        count = AuditLog.objects.filter(idempotency_key="idem-123").count()
        assert count == 1

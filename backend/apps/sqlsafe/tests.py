import pytest

from apps.sqlsafe.models import VistaPermitida
from apps.sqlsafe.validators import validar_sql


@pytest.mark.django_db
class TestValidarSql:
    def setup_method(self):
        VistaPermitida.objects.get_or_create(nombre="vw_tarifas", defaults={"activa": True})

    def test_valid_select(self):
        result = validar_sql("SELECT tariff_value FROM vw_tarifas WHERE origin = 'BUE'")
        assert result["valido"] is True
        assert "LIMIT 500" in result["sql_final"]

    def test_select_with_limit_not_doubled(self):
        result = validar_sql("SELECT tariff_value FROM vw_tarifas LIMIT 10")
        assert result["valido"] is True
        assert result["sql_final"].count("LIMIT") == 1

    def test_rejects_non_select(self):
        result = validar_sql("DELETE FROM vw_tarifas")
        assert result["valido"] is False

    def test_rejects_forbidden_table(self):
        result = validar_sql("SELECT * FROM users")
        assert result["valido"] is False
        assert "not in the allowed list" in result["error"]

    def test_rejects_system_schema(self):
        result = validar_sql("SELECT * FROM information_schema.tables")
        assert result["valido"] is False
        assert "forbidden" in result["error"]

    def test_rejects_pg_catalog(self):
        result = validar_sql("SELECT * FROM pg_catalog.pg_tables")
        assert result["valido"] is False

    def test_rejects_multiple_statements(self):
        result = validar_sql("SELECT 1; SELECT 2")
        assert result["valido"] is False

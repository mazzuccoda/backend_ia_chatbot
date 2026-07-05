"""Generic deterministic metric execution engine.

Builds a parameterized SQL query from a Metrica + its Dimensions, executes it
against the default DB connection, and returns the first matching row.
"""

import logging
from decimal import Decimal

from django.db import ProgrammingError, connections, transaction

from .handlers import HANDLERS
from .models import Metrica

logger = logging.getLogger(__name__)


def ejecutar_metrica_determinista(nombre_metrica: str, params: dict) -> dict:
    """Main entry point: execute a deterministic metric by name."""
    try:
        metrica = Metrica.objects.prefetch_related("dimensiones").get(
            nombre=nombre_metrica,
            activa=True,
            expone_tool_determinista=True,
        )
    except Metrica.DoesNotExist:
        return {"status": "error", "error_code": "METRIC_NOT_FOUND", "message": f"Metric '{nombre_metrica}' not found or not active."}

    # Delegate to custom handler if defined
    if metrica.handler and metrica.handler in HANDLERS:
        return HANDLERS[metrica.handler](metrica, params)

    # Validate required dimensions
    for dim in metrica.dimensiones.filter(requerido=True):
        if dim.nombre not in params:
            return {
                "status": "error",
                "error_code": "MISSING_REQUIRED_PARAM",
                "message": f"Missing required parameter: {dim.nombre}",
            }

    try:
        with transaction.atomic():
            sql, query_params, columns = _build_query_and_params(metrica, params)
            row = _execute_query(sql, query_params, columns)
    except ProgrammingError as exc:
        logger.exception("View not found: %s", metrica.vista)
        return {"status": "error", "error_code": "VIEW_NOT_FOUND", "message": str(exc)}

    if row is None:
        return {"status": "error", "error_code": "METRIC_DATA_NOT_FOUND", "message": "No data found for the given parameters."}

    result = {"status": "ok", metrica.medida_alias: row.get(metrica.medida_columna)}

    # Add dimension values
    for dim in metrica.dimensiones.all():
        if dim.nombre in params and dim.columna in row:
            result[dim.nombre] = row[dim.columna]

    # Add unit/currency if configured
    if metrica.unidad_columna and metrica.unidad_columna in row:
        result["unit"] = row[metrica.unidad_columna]
    if metrica.moneda_columna and metrica.moneda_columna in row:
        result["currency"] = row[metrica.moneda_columna]

    return result


def _build_query_and_params(metrica: Metrica, params: dict) -> tuple[str, list, list[str]]:
    """Build a parameterized SELECT from the metric definition."""
    # Collect columns to select
    select_cols = [metrica.medida_columna]
    for dim in metrica.dimensiones.all():
        if dim.columna not in select_cols:
            select_cols.append(dim.columna)
    if metrica.unidad_columna and metrica.unidad_columna not in select_cols:
        select_cols.append(metrica.unidad_columna)
    if metrica.moneda_columna and metrica.moneda_columna not in select_cols:
        select_cols.append(metrica.moneda_columna)

    # Use quoted identifiers for column names (they come from Dimension, not user input)
    col_list = ", ".join(f'"{c}"' for c in select_cols)
    sql = f'SELECT {col_list} FROM "{metrica.vista}"'

    where_parts: list[str] = []
    query_params: list = []

    # Fixed filter
    if metrica.filtro_fijo:
        where_parts.append(f"({metrica.filtro_fijo})")

    # Dynamic dimension filters
    for dim in metrica.dimensiones.all():
        if dim.nombre in params:
            val = params[dim.nombre]
            if dim.comparador == "ILIKE":
                where_parts.append(f'"{dim.columna}" ILIKE %s')
                query_params.append(f"%{val}%")
            else:
                where_parts.append(f'"{dim.columna}" = %s')
                query_params.append(val)

    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    # Ordering
    direction = "DESC" if metrica.orden_desc else "ASC"
    sql += f' ORDER BY "{metrica.orden_por}" {direction} LIMIT 1'

    return sql, query_params, select_cols


def _coerce_value(val):
    """Convert Decimal and other non-JSON-serializable types to native Python types."""
    if isinstance(val, Decimal):
        return float(val)
    return val


def _execute_query(sql: str, params: list, columns: list[str]) -> dict | None:
    """Execute a parameterized query and return the first row as a dict."""
    with connections["default"].cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return {col: _coerce_value(val) for col, val in zip(columns, row)}

"""Registry for custom metric handlers.

Most metrics use the generic lookup (generic_lookup.py). Register a handler
here only when a metric needs extra computation beyond "filter a view and
return one row".
"""

import logging

from django.db import connections

logger = logging.getLogger(__name__)

HANDLERS: dict[str, callable] = {}


def registrar(nombre: str):
    """Decorator to register a custom handler by name."""

    def wrapper(fn):
        HANDLERS[nombre] = fn
        return fn

    return wrapper


def _fetch_row(metrica, params: dict) -> dict | None:
    """Shared helper: fetch a single row from a metric's view using the
    same safe parameterized logic as generic_lookup."""
    from .generic_lookup import _build_query_and_params, _execute_query

    sql, query_params, columns = _build_query_and_params(metrica, params)
    return _execute_query(sql, query_params, columns)


@registrar("budget_vs_real_handler")
def budget_vs_real_handler(metrica, params: dict) -> dict:
    row = _fetch_row(metrica, params)
    if row is None:
        return {"status": "error", "error_code": "METRIC_DATA_NOT_FOUND", "message": "No data found."}

    real = row.get("real", 0) or 0
    budget = row.get("budget", 0) or 0
    difference = real - budget
    variation_pct = round(difference / budget * 100, 2) if budget else None

    return {
        "status": "ok",
        "real": real,
        "budget": budget,
        "difference": difference,
        "variation_pct": variation_pct,
    }

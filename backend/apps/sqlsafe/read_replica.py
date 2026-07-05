"""Readonly database connection utilities.

The 'readonly' database alias is configured in settings to use a separate
PostgreSQL role with SELECT-only grants, plus a statement_timeout. This module
provides a convenience wrapper for executing validated SQL against that
connection.
"""

import logging
from decimal import Decimal

from django.db import connections

logger = logging.getLogger(__name__)


def ejecutar_en_readonly(sql: str, params: list | None = None) -> list[dict]:
    """Execute a validated SQL query against the readonly connection.

    Returns a list of dicts (one per row). Raises on connection errors or
    statement_timeout.
    """
    with connections["readonly"].cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append({
                col: float(val) if isinstance(val, Decimal) else val
                for col, val in zip(columns, row)
            })
        return rows

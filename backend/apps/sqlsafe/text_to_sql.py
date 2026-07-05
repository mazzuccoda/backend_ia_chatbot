"""Text-to-SQL generation using an LLM with the semantic model as context."""

import json
import logging

import httpx
from django.conf import settings

from .models import Metrica

logger = logging.getLogger(__name__)


def _match_metricas(pregunta: str) -> list[Metrica]:
    """Find active metrics whose name or synonyms match the question (simple text match)."""
    pregunta_lower = pregunta.lower()
    metricas = Metrica.objects.filter(activa=True, permite_flexible=True).prefetch_related("dimensiones")
    matched = []
    for m in metricas:
        terms = [m.nombre.lower()] + [s.lower() for s in (m.sinonimos or [])]
        for term in terms:
            if term in pregunta_lower:
                matched.append(m)
                break
    return matched


def _build_prompt(pregunta: str, metricas: list[Metrica]) -> str:
    """Build the LLM prompt with only the relevant metric schemas."""
    schema_parts = []
    for m in metricas:
        dims = [
            f"  - {d.nombre} ({d.tipo}, col={d.columna}, required={d.requerido})"
            for d in m.dimensiones.all()
        ]
        schema_parts.append(
            f"Metric: {m.nombre}\n"
            f"  View: {m.vista}\n"
            f"  Fixed filter: {m.filtro_fijo or 'none'}\n"
            f"  Measure column: {m.medida_columna}\n"
            f"  Dimensions:\n" + "\n".join(dims)
        )

    schema_text = "\n\n".join(schema_parts)

    return (
        "You are a SQL expert. Given a user question and the available metric schemas below, "
        "generate a single PostgreSQL SELECT query that answers the question.\n\n"
        f"Available metrics:\n{schema_text}\n\n"
        f"User question: {pregunta}\n\n"
        "Respond ONLY with a JSON object (no markdown, no explanation):\n"
        '{"sql": "<the SQL query>", "metrica_usada": "<metric name>", "confianza": <0.0 to 1.0>}\n'
    )


def generar_sql(pregunta: str) -> dict:
    """Generate SQL from a natural language question.

    Returns a dict with keys: sql, metrica_usada, confianza.
    If no matching metrics or LLM is unavailable, returns {"confianza": 0.0}.
    """
    metricas = _match_metricas(pregunta)
    if not metricas:
        return {"confianza": 0.0}

    api_key = settings.FLEXIBLE_QUERY_LLM_API_KEY
    if not api_key:
        logger.warning("FLEXIBLE_QUERY_LLM_API_KEY not set — cannot generate SQL.")
        return {"confianza": 0.0}

    model = settings.FLEXIBLE_QUERY_LLM_MODEL
    provider = settings.FLEXIBLE_QUERY_LLM_PROVIDER

    # Build OpenAI-compatible request
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
    else:
        url = provider  # Custom endpoint URL

    prompt = _build_prompt(pregunta, metricas)

    try:
        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 500,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
        return {
            "sql": result.get("sql", ""),
            "metrica_usada": result.get("metrica_usada", ""),
            "confianza": float(result.get("confianza", 0.0)),
        }
    except Exception:
        logger.exception("Error calling LLM for text-to-SQL")
        return {"confianza": 0.0}

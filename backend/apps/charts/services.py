"""Chart generation service using matplotlib (Agg backend)."""

import logging
import os
import uuid

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_chart(
    *,
    chart_type: str,
    title: str,
    x: list,
    y: list,
    unit: str = "",
    format: str = "png",
) -> dict:
    """Generate a chart image and save to MEDIA_ROOT/charts/."""
    max_width = settings.CHART_MAX_WIDTH_PX
    dpi = settings.CHART_DEFAULT_DPI
    fig_width = min(max_width, 1080) / dpi
    fig_height = fig_width * 0.75

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    if chart_type == "bar":
        ax.bar(x, y, color="#4A90D9")
    elif chart_type == "horizontal_bar":
        ax.barh(x, y, color="#4A90D9")
    elif chart_type == "line":
        ax.plot(x, y, marker="o", color="#4A90D9")
    elif chart_type == "pie":
        ax.pie(y, labels=x, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
    else:
        plt.close(fig)
        return {"status": "error", "error_code": "INVALID_CHART_TYPE", "message": f"Unsupported chart type: {chart_type}"}

    ax.set_title(title)
    if unit and chart_type != "pie":
        ax.set_ylabel(unit)

    plt.tight_layout()

    charts_dir = os.path.join(settings.MEDIA_ROOT, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    filename = f"chart_{uuid.uuid4().hex[:12]}.{format}"
    filepath = os.path.join(charts_dir, filename)
    fig.savefig(filepath, format=format, bbox_inches="tight")
    plt.close(fig)

    chart_url = f"{settings.MEDIA_URL}charts/{filename}"
    chart_path = f"media/charts/{filename}"

    return {"status": "ok", "chart_url": chart_url, "chart_path": chart_path}

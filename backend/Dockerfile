# Stage 1: build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: production image
FROM python:3.12-slim

# System deps for psycopg and curl (healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /install /usr/local

# Non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app
COPY . /app/

RUN mkdir -p /app/media/charts /app/staticfiles && \
    chown -R appuser:appuser /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

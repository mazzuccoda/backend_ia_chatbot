#!/bin/bash
set -e

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Creating default API client..."
python manage.py create_default_apiclient

echo "==> Seeding initial metrics..."
python manage.py seed_metricas

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -

# Backend IA Chatbot — Analytics API

Backend Django + DRF que funciona como capa de herramientas analíticas para un
chatbot de WhatsApp orquestado por **n8n**.

## Arquitectura

```
WhatsApp ↔ Evolution API ↔ n8n (orquestador) ↔ Este Backend (tools analíticas)
                                                   ↕
                                              PostgreSQL
```

El backend expone dos caminos controlados:

1. **Tools deterministas** — definidas como datos (`Metrica` + `Dimension`) en
   Django Admin. Se agregan sin código ni redeploy.
2. **Fallback flexible** (`consulta_flexible`) — Text-to-SQL con LLM +
   validación AST (`sqlglot`) + ejecución contra conexión de solo lectura.

---

## Stack

- Python 3.12, Django 5.x, Django REST Framework
- PostgreSQL 16, Redis 7 (opcional)
- Docker + docker-compose (compatible con Portainer)
- Gunicorn, Whitenoise, drf-spectacular (OpenAPI)
- matplotlib, pandas, sqlglot, httpx

---

## Levantar en local con Docker Compose

```bash
# 1. Clonar el repo
git clone https://github.com/mazzuccoda/backend_ia_chatbot.git
cd backend_ia_chatbot

# 2. Crear el .env
cp .env.example .env
# Editar .env — como mínimo cambiar DJANGO_SECRET_KEY y N8N_API_KEY_SEED

# 3. Levantar
docker compose up --build -d

# 4. Crear superusuario para Django Admin
docker compose exec backend python manage.py createsuperuser
```

El backend estará en `http://localhost:8010`.

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Clave secreta de Django (obligatoria en producción) |
| `DJANGO_DEBUG` | `False` | Activar modo debug |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Módulo de settings |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | Hosts permitidos |
| `DATABASE_URL` | `postgres://analytics_user:analytics_password@postgres:5432/analytics_bot` | URL de conexión principal |
| `READONLY_DB_USER` | `analytics_readonly` | Usuario de solo lectura para consulta_flexible |
| `READONLY_DB_PASSWORD` | `change-me` | Contraseña del usuario readonly |
| `REDIS_URL` | (vacío) | URL de Redis; si no hay, usa cache en memoria |
| `N8N_API_KEY_SEED` | — | API key que se usa para crear el primer ApiClient automáticamente |
| `MEDIA_URL` | `/media/` | URL base para archivos media |
| `MEDIA_ROOT` | `/app/media` | Directorio de archivos media |
| `CHART_MAX_WIDTH_PX` | `1080` | Ancho máximo de gráficos en px |
| `CHART_DEFAULT_DPI` | `150` | DPI de gráficos |
| `IDEMPOTENCY_CACHE_TTL_SECONDS` | `86400` | TTL de idempotencia en segundos |
| `FLEXIBLE_QUERY_LLM_PROVIDER` | `openai` | Proveedor LLM (URL o "openai") |
| `FLEXIBLE_QUERY_LLM_MODEL` | `gpt-4o-mini` | Modelo LLM |
| `FLEXIBLE_QUERY_LLM_API_KEY` | — | API key del LLM |
| `FLEXIBLE_QUERY_MIN_CONFIDENCE` | `0.6` | Confianza mínima para ejecutar SQL |
| `FLEXIBLE_QUERY_TIMEOUT_SECONDS` | `8` | Timeout de ejecución de SQL flexible |

---

## Endpoints

### Healthcheck (sin auth)

```bash
curl http://localhost:8010/api/v1/health/
```

### Swagger / OpenAPI

- Schema: `http://localhost:8010/api/schema/`
- Swagger UI: `http://localhost:8010/api/docs/`

### Listar tools disponibles

```bash
curl -H "X-API-Key: TU_API_KEY" http://localhost:8010/api/v1/tools/
```

### Ejecutar tool determinista (ejemplo: tarifa_flete)

```bash
curl -X POST http://localhost:8010/api/v1/tools/tarifa_flete/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"origin": "Buenos Aires", "destination": "Mendoza"}'
```

### Ejecutar tool determinista (ejemplo: tarifa_almacenaje)

```bash
curl -X POST http://localhost:8010/api/v1/tools/tarifa_almacenaje/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"warehouse": "Deposito Central"}'
```

### Consulta flexible (text-to-SQL)

```bash
curl -X POST http://localhost:8010/api/v1/tools/consulta-flexible/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "cuánto cuesta el flete de Buenos Aires a Córdoba?", "user_id": "u1", "conversation_id": "c1"}'
```

### Generar gráfico

```bash
curl -X POST http://localhost:8010/api/v1/charts/generate/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"chart_type": "bar", "title": "Ventas", "x": ["Ene", "Feb", "Mar"], "y": [100, 200, 150], "unit": "USD"}'
```

### Memoria

```bash
# Guardar
curl -X POST http://localhost:8010/api/v1/memory/save/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1", "conversation_id": "c1", "key": "name", "value": "Daniel"}'

# Recuperar
curl -X POST http://localhost:8010/api/v1/memory/get/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1", "conversation_id": "c1"}'
```

### Idempotencia

Todos los endpoints bajo `/api/v1/tools/` aceptan el header `Idempotency-Key`:

```bash
curl -X POST http://localhost:8010/api/v1/tools/tarifa_flete/ \
  -H "X-API-Key: TU_API_KEY" \
  -H "Idempotency-Key: unique-request-id-123" \
  -H "Content-Type: application/json" \
  -d '{"origin": "Buenos Aires", "destination": "Mendoza"}'
```

---

## Configurar n8n — HTTP Request node

En n8n, configurar un nodo **HTTP Request** con:

- **Method**: POST
- **URL**: `http://backend:8000/api/v1/tools/tarifa_flete/`
  (usar el nombre del servicio Docker si están en la misma red)
- **Headers**:
  - `X-API-Key`: el valor de `N8N_API_KEY_SEED` del `.env`
  - `Content-Type`: `application/json`
- **Body** (JSON):
  ```json
  {
    "origin": "{{ $json.origin }}",
    "destination": "{{ $json.destination }}",
    "user_id": "{{ $json.user_id }}",
    "conversation_id": "{{ $json.conversation_id }}"
  }
  ```

---

## Django Admin

Acceder en `http://localhost:8010/admin/` con el superusuario creado.

Desde el Admin se puede:

- **Métricas** (`sqlsafe → Métricas`): crear, editar, habilitar/deshabilitar
  tools deterministas. Cada `Metrica` tiene sus `Dimension` como inline.
- **Vistas Permitidas** (`sqlsafe → Vistas Permitidas`): whitelist de vistas
  de DB que se pueden consultar. Solo superusuarios pueden modificarla.
- **API Clients** (`auth_api`): gestionar clientes de API con scopes.
- **Configuración** (`core`): key/value store para umbrales de negocio.
- **Memoria** / **Auditoría**: consultar registros.

### Agregar una tool nueva sin código

1. Ir a **Métricas → Añadir Métrica**
2. Completar: nombre, vista (debe estar en Vistas Permitidas), columnas de
   medida/unidad/moneda, filtro fijo si aplica.
3. Agregar Dimensiones inline (parámetros de la tool).
4. Guardar.
5. La tool aparece automáticamente en `GET /api/v1/tools/` y acepta requests
   en `POST /api/v1/tools/<nombre>/`.

---

## Rol de solo lectura para consulta_flexible

Ejecutar en PostgreSQL:

```sql
CREATE ROLE analytics_readonly LOGIN PASSWORD 'tu-password-seguro';
GRANT CONNECT ON DATABASE analytics_bot TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;
GRANT SELECT ON vw_tarifas, vw_budget_vs_real, vw_costos_transporte, vw_volumen, vw_kpi_logistica TO analytics_readonly;
```

Luego configurar `READONLY_DB_USER` y `READONLY_DB_PASSWORD` en el `.env`.

---

## Deploy con Portainer

1. En Portainer, ir a **Stacks → Add stack → Repository**
2. **Repository URL**: `https://github.com/mazzuccoda/backend_ia_chatbot.git`
3. **Branch**: `main`
4. **Compose path**: `docker-compose.yml`
5. En **Environment variables**, agregar todas las variables del `.env.example`
   con valores de producción.
6. Click en **Deploy the stack**.

---

## Limpieza de gráficos

```bash
# Borrar charts con más de 7 días
docker compose exec backend python manage.py cleanup_old_charts --days 7
```

Para automatizar, agregar un cron en el host:

```cron
0 3 * * * docker compose -f /path/to/docker-compose.yml exec -T backend python manage.py cleanup_old_charts --days 7
```

---

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

---

## Futuro (fuera de alcance en esta fase)

- Celery para tareas asincrónicas
- Embeddings / RAG (actualmente en n8n)
- Frontend separado (React/Vue)
- Login de usuario final

# Nexus Legal Integration v2.2

Middleware de integración entre ClickUp, Cloud SQL (PostgreSQL) y servicios externos (Filtros IA) con API para búsqueda fuzzy, sincronización de datos y procesamiento inteligente de leads.

## Arquitectura

```
ClickUp API/Webhooks → FastAPI (Cloud Run) → Cloud SQL PostgreSQL → API Consumers (MCP/Sheets)
                              ↓
                    Enqueuer (Cloud Tasks) → Filtros IA → Callback → ClickUp Update
```

**Componentes principales:**

- **FastAPI**: API REST con endpoints de webhook y búsqueda
- **Cloud SQL**: PostgreSQL con extensión `pg_trgm` para búsqueda fuzzy
- **Cloud Run**: Hosting serverless (scale-to-zero)
- **Secret Manager**: Gestión de credenciales
- **Enqueuer + Filtros IA**: Procesamiento inteligente de leads vía Cloud Tasks
- **Google Sheets**: Sincronización de logs y reportes

## Stack Tecnológico

- **Python 3.11+**
- **FastAPI** (framework web)
- **SQLAlchemy** (ORM)
- **PostgreSQL 15** con `pg_trgm`
- **Google Cloud Run** (hosting)
- **Alembic** (migraciones de DB)

## Estructura del Proyecto

```
clickupmendoza/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración (Pydantic Settings)
│   ├── database.py          # Conexión a DB
│   ├── models/              # Modelos SQLAlchemy
│   │   └── lead.py
│   ├── schemas/             # Schemas Pydantic (request/response)
│   │   ├── lead.py
│   │   └── webhook.py
│   ├── core/                # Lógica de parsing y normalización
│   │   ├── parser.py        # Extrae campos de task_content
│   │   ├── normalizer.py    # Normaliza nombres para búsqueda
│   │   └── text_utils.py    # Utilidades de texto
│   ├── repositories/        # Patrón Repository (acceso a datos)
│   │   └── lead_repository.py
│   ├── services/            # Lógica de negocio
│   │   ├── clickup_service.py
│   │   └── lead_service.py
│   └── api/                 # Endpoints FastAPI
│       ├── webhooks.py      # POST /webhooks/clickup
│       └── leads.py         # GET /leads/search, etc.
├── alembic/                 # Migraciones de base de datos
│   ├── env.py
│   └── versions/
├── scripts/
│   └── init_db.py           # Script de inicialización de DB
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
├── deploy.sh
└── .env.example
```

## Instalación Local

### 1. Requisitos previos

- Python 3.11+
- PostgreSQL 15+ (con extensión `pg_trgm`)
- Google Cloud SDK (para deployment)

### 2. Clonar repositorio

```bash
git clone <repo-url>
cd clickupmendoza
```

### 3. Configurar entorno

```bash
# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables críticas:**
- `CLICKUP_API_TOKEN`: Token de API de ClickUp
- `CLICKUP_WEBHOOK_SECRET`: Secret para validar webhooks
- `DATABASE_URL`: Connection string de PostgreSQL

### 5. Inicializar base de datos

```bash
# Opción 1: Script de inicialización (recomendado para primera vez)
python scripts/init_db.py

# Opción 2: Usar Alembic
alembic upgrade head
```

El script `init_db.py` hace:
1. Habilita extensión `pg_trgm`
2. Crea tabla `leads_cache`
3. Crea índice GIN para búsqueda fuzzy

### 6. Ejecutar localmente

```bash
# Modo desarrollo (con auto-reload)
uvicorn app.main:app --reload --port 8080

# Acceder a documentación interactiva
open http://localhost:8080/docs
```

## Deployment en Google Cloud Run

### 1. Configurar proyecto GCP

```bash
# Autenticarse
gcloud auth login

# Configurar proyecto
export GCP_PROJECT_ID="tu-proyecto-id"
export GCP_REGION="us-central1"

gcloud config set project $GCP_PROJECT_ID
```

### 2. Crear Cloud SQL instance

```bash
gcloud sql instances create nexus-legal-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$GCP_REGION

# Crear base de datos
gcloud sql databases create nexus_legal_db \
    --instance=nexus-legal-db

# Crear usuario
gcloud sql users create dbuser \
    --instance=nexus-legal-db \
    --password=SECURE_PASSWORD
```

### 3. Configurar Secret Manager

```bash
# Crear secrets
echo -n "pk_YOUR_CLICKUP_TOKEN" | gcloud secrets create CLICKUP_API_TOKEN --data-file=-
echo -n "your_webhook_secret" | gcloud secrets create CLICKUP_WEBHOOK_SECRET --data-file=-
echo -n "postgresql://user:pass@host/db" | gcloud secrets create DATABASE_URL --data-file=-
```

### 4. Deploy

```bash
# Opción 1: Script automatizado
./deploy.sh

# Opción 2: Manual con gcloud
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/nexus-legal-api

gcloud run deploy nexus-legal-api \
    --image gcr.io/$GCP_PROJECT_ID/nexus-legal-api \
    --region $GCP_REGION \
    --platform managed \
    --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest \
    --min-instances 0 \
    --max-instances 10
```

## API Endpoints

### Health Check

```
GET /
GET /health
```

### Webhooks

**POST /webhooks/clickup**

Recibe eventos de ClickUp (taskUpdated, taskCreated).

Headers requeridos:
- `X-Signature`: Firma del webhook

### Búsqueda de Leads

**GET /leads/search?q=nombre&limit=10**

Búsqueda fuzzy por nombre (usa pg_trgm similarity).

Parámetros:
- `q`: Texto a buscar (min 2 caracteres)
- `limit`: Máximo de resultados (default 10, max 50)

**GET /leads/{task_id}**

Obtiene un lead por ID de tarea de ClickUp.

**GET /leads/mycase/{mycase_id}**

Obtiene un lead por MyCase ID (8 dígitos).

**GET /leads/?skip=0&limit=100**

Lista todos los leads con paginación.

## Configurar Webhook en ClickUp

1. Ir a ClickUp → Settings → Integrations → Webhooks
2. Crear nuevo webhook:
   - **URL**: `https://YOUR-CLOUD-RUN-URL/webhooks/clickup`
   - **Events**: Task Updated, Task Created
   - **Secret**: (mismo que `CLICKUP_WEBHOOK_SECRET`)

## Lógica de Parsing

El sistema extrae información de dos fuentes:

### 1. Metadatos nativos de ClickUp
- `task_name`, `status`, `assignee`, fechas, etc.

### 2. Mining del campo `task_content` (descripción)

Usa regex para extraer:

**Campos de línea simple:**
```
Name: Juan Perez
Phone: (555) 123-4567
Email: juan@example.com
```

**Campos de bloque:**
```
Other result of interview (optional):
[Texto multilínea capturado hasta "Type of Interview"]
```

**Normalización de nombres:**

```python
"López García | 12345678" →
  nombre_clickup: "López García"
  id_mycase: "12345678"
  nombre_normalizado: "LOPEZ GARCIA"  # Para búsqueda fuzzy
```

**Validación de teléfonos:**
- Extrae solo dígitos
- Valida longitud (10-15)
- Descarta si no cumple

## Búsqueda Fuzzy (pg_trgm)

La búsqueda usa **trigramas** para encontrar nombres similares incluso con errores tipográficos:

```sql
SELECT * FROM leads_cache
WHERE nombre_normalizado % 'JUAN PEREZ'
ORDER BY similarity(nombre_normalizado, 'JUAN PEREZ') DESC
LIMIT 10;
```

**Requisitos:**
1. Extensión `pg_trgm` habilitada
2. Índice GIN en `nombre_normalizado`

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_nombre_normalizado_gin ON leads_cache USING gin (nombre_normalizado gin_trgm_ops);
```

## Mantenimiento

### Ver logs en Cloud Run

```bash
gcloud run logs read nexus-legal-api --region $GCP_REGION --limit 100
```

### Ejecutar migraciones

```bash
# Generar migración automática
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoreo

Cloud Run proporciona métricas automáticas:
- Latencia de requests
- Errores (4xx, 5xx)
- Uso de CPU/memoria
- Invocaciones

Acceder en: [Cloud Console → Cloud Run → Metrics](https://console.cloud.google.com/run)

## Seguridad

- **HTTPS/TLS**: Todo el tráfico es encriptado
- **Validación de webhooks**: Firma HMAC verificada
- **Secrets Manager**: Credenciales nunca en código
- **Cloud SQL**: Encriptación en reposo por default
- **IAM**: Control de acceso granular

## Nuevas Funcionalidades (v2.2) ✨

### Versión 2.2 (Enero 2026)
- [x] **Integración con Filtros IA (FIA)**: Envío automático de leads al microservicio de filtros inteligentes via Enqueuer
- [x] **Procesamiento en Background**: Tareas pesadas (dispatch, sheets) ejecutadas en segundo plano para respuesta rápida a ClickUp
- [x] **Protección contra Bucles**: Verificación de campo `AI Link` para evitar reprocesamiento
- [x] **Lista Optimizada**: Configuración para lista "CONSULTAS AGENDA" como fuente principal
- [x] **Callback URL**: Soporte para recibir respuestas del servicio de Filtros IA

### Versión 2.1
- [x] **Integración con Google Sheets**: Sincronización automática vía Service Account
- [x] **External Dispatch**: Notificación HTTP a servicios externos
- [x] **Trigger Condicional**: Acciones basadas en campo "Link Intake"
- [x] **Filtrado por Lista**: Webhooks específicos para lista configurada

Ver [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) para instrucciones detalladas.

## Roadmap (Próximas Mejoras)

- [ ] Job nocturno con Cloud Scheduler (safety net)
- [ ] Extracción de comentarios de ClickUp
- [ ] Exportación de datos (CSV, Excel)
- [ ] Dashboard de métricas (Looker Studio)
- [ ] Retry logic para dispatch fallido

## Soporte

Para issues o preguntas, contactar al equipo de desarrollo.

---

**Versión:** 2.2.0
**Última actualización:** 2026-01-23

## Documentación Adicional

- [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) - Guía de configuración de Google Sheets y External Dispatch
- [VARIABLES_DE_ENTORNO.md](VARIABLES_DE_ENTORNO.md) - Referencia completa de variables de entorno
- [RESUMEN_IMPLEMENTACION.md](RESUMEN_IMPLEMENTACION.md) - Resumen técnico de la implementación v2.1
- [CHANGELOG.md](CHANGELOG.md) - Registro de cambios por versión

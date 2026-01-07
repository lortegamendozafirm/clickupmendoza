# Arquitectura Técnica - Nexus Legal Integration v2.1

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐        ┌──────────────┐                           │
│  │ ClickUp API  │        │ CSVs Legacy  │                           │
│  │ (Webhooks)   │        │ (Bootstrap)  │                           │
│  └──────┬───────┘        └──────┬───────┘                           │
└─────────┼───────────────────────┼───────────────────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   NEXUS MIDDLEWARE (Cloud Run)                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Gateway                          │    │
│  │  • POST /webhooks/clickup    (Ingest)                       │    │
│  │  • GET  /leads/search        (Búsqueda fuzzy)               │    │
│  │  • GET  /leads/{id}          (Consulta individual)          │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │                                                    │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │                  Capa de Servicios                          │    │
│  │  ┌────────────────────┐  ┌──────────────────────┐           │    │
│  │  │ LeadService        │  │ ClickUpService       │           │    │
│  │  │ • transform_task() │  │ • get_task()         │           │    │
│  │  └────────────────────┘  │ • verify_webhook()   │           │    │
│  │                          └──────────────────────┘           │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │                                                    │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │                    Core Logic                               │    │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐      │    │
│  │  │ Parser     │  │ Normalizer   │  │ TextUtils       │      │    │
│  │  │ (Regex)    │  │ (Fuzzy prep) │  │ (Clean/Squish)  │      │    │
│  │  └────────────┘  └──────────────┘  └─────────────────┘      │    │
│  └─────────────┬───────────────────────────────────────────────┘    │
│                │                                                    │
│  ┌─────────────▼───────────────────────────────────────────────┐    │
│  │              Repository Layer (Data Access)                 │    │
│  │  ┌────────────────────────────────────────────┐             │    │
│  │  │ LeadRepository                             │             │    │
│  │  │ • upsert()                                 │             │    │
│  │  │ • search_by_name() (pg_trgm)               │             │    │
│  │  │ • get_by_task_id()                         │             │    │
│  │  └───────────────┬────────────────────────────┘             │    │
│  └──────────────────┼──────────────────────────────────────────┘    │
│                     │                                               │
│  ┌──────────────────▼─────────────────────────────────────────┐     │
│  │                SQLAlchemy ORM                              │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CLOUD SQL (PostgreSQL 15)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Tabla: leads_cache                                         │    │
│  │  • Columnas nativas de ClickUp                              │    │
│  │  • Columnas minadas (parsing de task_content)               │    │
│  │  • nombre_normalizado (para búsqueda fuzzy)                 │    │
│  │                                                             │    │
│  │  Extensiones:                                               │    │
│  │  • pg_trgm (trigram similarity)                             │    │
│  │                                                             │    │
│  │  Índices:                                                   │    │
│  │  • GIN en nombre_normalizado (búsqueda fuzzy)               │    │
│  │  • B-tree en task_id, phone_number, date_updated            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CONSUMIDORES                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────┐      │
│  │ MCP Clients  │     │ Google Sheets│     │ Operación CDMX/ │      │
│  │ (IA Agents)  │     │ (Reportes)   │     │ Cancún          │      │
│  └──────────────┘     └──────────────┘     └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

## Capas de la Aplicación

### 1. Capa de API (FastAPI)

**Responsabilidad:** Exposición de endpoints HTTP, validación de requests, autenticación.

**Archivos:**
- `app/main.py` - Aplicación principal, configuración CORS
- `app/api/webhooks.py` - Endpoint POST /webhooks/clickup
- `app/api/leads.py` - Endpoints de búsqueda y consulta

**Schemas (Pydantic):**
- `app/schemas/lead.py` - Validación de respuestas
- `app/schemas/webhook.py` - Validación de webhooks

### 2. Capa de Servicios (Business Logic)

**Responsabilidad:** Orquestación de lógica de negocio, transformación de datos.

**Archivos:**
- `app/services/lead_service.py`
  - `transform_clickup_task()`: Transforma tarea de ClickUp a formato DB
  - `_parse_custom_fields()`: Extrae custom fields
  - `_parse_clickup_date()`: Normaliza fechas

- `app/services/clickup_service.py`
  - `get_task()`: Obtiene tarea de ClickUp API
  - `get_tasks_updated_since()`: Safety net (job nocturno)
  - `verify_webhook_signature()`: Seguridad de webhooks

### 3. Capa Core (Parsing y Normalización)

**Responsabilidad:** Extracción de datos no estructurados, normalización para búsqueda.

**Archivos:**
- `app/core/parser.py`
  - `parse_task_content()`: Motor principal de parsing
  - `get_line()`: Extrae campos de una línea (Label: Value)
  - `get_block_until()`: Extrae bloques multilínea
  - `get_mycase_id()`: Extrae ID de MyCase (8 dígitos)

- `app/core/normalizer.py`
  - `normalize_task_name()`: Extrae nombre_clickup, id_mycase, nombre_normalizado

- `app/core/text_utils.py`
  - `normalize_name()`: ASCII, mayúsculas, sin acentos
  - `clean_phone()`: Validación de teléfonos (10-15 dígitos)
  - `remove_ordinal_suffix()`: Elimina 1st, 2nd, 3rd, 4th de fechas

**Lógica de Parsing (Ejemplos):**

```python
# Entrada (task_content):
"""
Name: Juan Pérez
Phone: (555) 123-4567
Email: juan@example.com

Other result of interview (optional):
El cliente califica para VAWA.
Evidencia documentada.

Type of Interview: Individual
"""

# Salida (parsed):
{
    "full_name_extracted": "Juan Pérez",
    "phone_raw": "(555) 123-4567",
    "phone_number": "5551234567",  # Validado: 10 dígitos
    "email_extracted": "juan@example.com",
    "interview_other": "El cliente califica para VAWA.\nEvidencia documentada.",
    "interview_type": "Individual"
}
```

**Normalización de Nombres:**

```python
# Entrada:
task_name = "López García | 12345678"

# Salida:
nombre_clickup = "López García"
id_mycase = "12345678"
nombre_normalizado = "LOPEZ GARCIA"  # Para búsqueda fuzzy
```

### 4. Capa de Repositorio (Data Access)

**Responsabilidad:** Acceso a base de datos, encapsulación de queries SQL.

**Archivos:**
- `app/repositories/lead_repository.py`
  - `upsert()`: Insert o Update (basado en task_id)
  - `search_by_name()`: Búsqueda fuzzy con pg_trgm
  - `get_by_task_id()`, `get_by_mycase_id()`: Consultas directas
  - `get_recent_updates()`: Para sync incremental

**Búsqueda Fuzzy (pg_trgm):**

```python
# Query interno:
SELECT * FROM leads_cache
WHERE nombre_normalizado % 'JUAN PEREZ'  -- Operador similarity
ORDER BY similarity(nombre_normalizado, 'JUAN PEREZ') DESC
LIMIT 10;

# Encuentra:
# - "JUAN PEREZ" (exacto)
# - "JUAN PERES" (typo)
# - "PEREZ JUAN" (orden invertido)
# - "JUAN A PEREZ" (variación)
```

### 5. Capa de Modelos (ORM)

**Responsabilidad:** Definición de schema de DB, mapeo ORM.

**Archivos:**
- `app/models/lead.py` - Modelo `LeadsCache` (SQLAlchemy)

**Columnas principales:**

| Categoría | Columnas |
|-----------|----------|
| **Identificadores** | `task_id` (PK), `id_mycase`, `mycase_link` |
| **Metadatos ClickUp** | `task_name`, `status`, `priority`, `assignee`, `date_created`, `date_updated` |
| **Normalización** | `nombre_clickup`, `nombre_normalizado` |
| **Mining** | `full_name_extracted`, `phone_number`, `email_extracted`, `location`, `interview_type`, `interview_result`, `interview_other`, `case_type` |
| **Contenido** | `task_content` (texto completo), `comment_count` |

### 6. Capa de Configuración

**Archivos:**
- `app/config.py` - Pydantic Settings (lee .env)
- `app/database.py` - SQLAlchemy engine, session factory

## Flujos de Datos

### Flujo 1: Webhook Ingest (Tiempo Real)

```
1. ClickUp webhook → POST /webhooks/clickup
2. Validar firma (x-signature)
3. Obtener tarea completa de ClickUp API
4. LeadService.transform_clickup_task()
   ├─ Normalizar task_name → nombre_normalizado
   ├─ Parsear task_content → campos minados
   └─ Limpiar teléfonos, fechas
5. LeadRepository.upsert()
   ├─ Si task_id existe → UPDATE
   └─ Si no existe → INSERT
6. Retornar {"status": "success", "synced_at": "..."}
```

### Flujo 2: Búsqueda Fuzzy (MCP/API)

```
1. Cliente → GET /leads/search?q=Juan+Perez
2. Normalizar query → "JUAN PEREZ"
3. LeadRepository.search_by_name()
   ├─ SQL: WHERE nombre_normalizado % 'JUAN PEREZ'
   └─ ORDER BY similarity DESC
4. Retornar top N resultados
```

### Flujo 3: Bootstrap Histórico (ETL)

```
1. Ejecutar: python scripts/load_historical_data.py *.csv
2. Para cada CSV:
   ├─ Leer con columnas como texto
   ├─ Normalizar nombres de columnas (snake_case)
   └─ Para cada fila:
       ├─ transform_csv_row_to_lead()
       ├─ Parsear task_content
       └─ Upsert en DB
3. Commit cada 100 registros
```

### Flujo 4: Safety Net Job (Nocturno)

```
1. Cloud Scheduler → Cloud Run (endpoint interno)
2. ClickUpService.get_tasks_updated_since(last_24h)
3. Para cada tarea:
   ├─ LeadService.transform_clickup_task()
   └─ LeadRepository.upsert()
4. Captura tareas perdidas por webhooks fallidos
```

## Patrones de Diseño Implementados

### 1. Repository Pattern
- **Dónde:** `app/repositories/lead_repository.py`
- **Por qué:** Encapsula acceso a datos, facilita testing, desacopla lógica de negocio de SQL.

### 2. Service Layer Pattern
- **Dónde:** `app/services/`
- **Por qué:** Orquesta lógica de negocio, coordina entre múltiples repositorios/APIs.

### 3. Dependency Injection
- **Dónde:** FastAPI `Depends(get_db)`
- **Por qué:** Gestión automática de sesiones de DB, facilita testing con mocks.

### 4. Factory Pattern (Implicit)
- **Dónde:** `SessionLocal()` (sessionmaker)
- **Por qué:** Crea sesiones de DB bajo demanda.

### 5. Strategy Pattern (Implicit)
- **Dónde:** `parse_task_content()` con fallbacks
- **Por qué:** Diferentes estrategias de parsing según contenido disponible.

## Decisiones Técnicas

### ¿Por qué FastAPI?
- Async nativo (importante para llamadas a ClickUp API)
- Validación automática con Pydantic
- Documentación interactiva (Swagger UI)
- Alto rendimiento

### ¿Por qué SQLAlchemy ORM?
- Abstracción de SQL
- Migraciones con Alembic
- Type safety con Python moderno
- Compatible con Cloud SQL

### ¿Por qué pg_trgm en lugar de Elasticsearch?
- Simplicidad: no requiere servicio adicional
- Costo: incluido en PostgreSQL
- Suficiente para ~100K registros
- Búsqueda fuzzy integrada en DB

### ¿Por qué Cloud Run en lugar de GKE?
- Scale-to-zero (ahorro de costos)
- No requiere gestión de clusters
- Integración nativa con Cloud SQL
- Suficiente para cargas variables

### ¿Por qué wide table en lugar de normalización?
- Simplifica queries (no JOINs)
- Búsqueda fuzzy más rápida
- Tolera campos NULL (datos sucios)
- Facilita ETL de CSVs

## Seguridad

### 1. Secrets Management
- Credenciales en Secret Manager (nunca en código)
- DB passwords rotables sin redeploy
- API keys separados por entorno

### 2. Network Security
- HTTPS/TLS obligatorio (Cloud Run default)
- Cloud SQL: solo accesible vía Unix socket
- IAM roles con principio de menor privilegio

### 3. Input Validation
- Pydantic schemas validan requests
- Webhook signature verification
- SQL injection prevention (ORM)

### 4. PII Protection
- `task_content` puede contener PII (casos VAWA)
- Encriptación en reposo (Cloud SQL default)
- Logs sanitizados (no loguear contenido)

## Escalabilidad

### Límites actuales
- **Cloud Run:** 10 instancias máx (configurable)
- **Cloud SQL:** db-f1-micro (desarrollo), upgradeable
- **Búsqueda fuzzy:** Óptima hasta ~500K registros

### Optimizaciones futuras
- [ ] Cache con Redis (nombre → task_id)
- [ ] Full-text search con índice GiST adicional
- [ ] Particionado de tabla por año
- [ ] Réplica de lectura para analytics

## Monitoreo y Observabilidad

### Logs
- Cloud Logging (automático en Cloud Run)
- Structured logging (JSON)
- Request tracing (correlation IDs)

### Métricas (Cloud Monitoring)
- Latencia de requests (p50, p95, p99)
- Tasa de errores (4xx, 5xx)
- Uso de CPU/memoria
- Conexiones a DB

### Alertas recomendadas
- Error rate > 5% (5 min)
- Latencia p95 > 2s
- DB connections > 80%
- Webhook signature failures

---

**Versión:** 2.1.0
**Última actualización:** 2026-01-05

# Ejemplos de Uso de la API

Colección de ejemplos prácticos para interactuar con Nexus Legal Integration API.

## Base URL

**Local:** `http://localhost:8080`
**Producción:** `https://YOUR-CLOUD-RUN-URL`

## Autenticación

Por ahora la API es pública. Para producción, considera agregar API keys o IAM authentication.

---

## Health Check

### GET /

Verifica que el servicio está corriendo.

```bash
curl http://localhost:8080/
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "Nexus Legal Integration",
  "version": "2.2.0",
  "environment": "development"
}
```

---

## Búsqueda de Leads

### GET /leads/search

Búsqueda fuzzy por nombre usando pg_trgm.

#### Ejemplo 1: Búsqueda básica

```bash
curl "http://localhost:8080/leads/search?q=Juan+Perez"
```

**Respuesta:**
```json
{
  "total": 3,
  "results": [
    {
      "task_id": "abc123",
      "task_name": "Juan Perez | 12345678",
      "nombre_clickup": "Juan Perez",
      "nombre_normalizado": "JUAN PEREZ",
      "status": "Active",
      "full_name_extracted": "Juan Alberto Perez",
      "phone_number": "5551234567",
      "email_extracted": "juan@example.com",
      "id_mycase": "12345678",
      "date_created": "2024-01-15T10:30:00Z",
      "date_updated": "2024-01-20T14:45:00Z",
      "synced_at": "2024-01-20T15:00:00Z"
    },
    {
      "task_id": "def456",
      "task_name": "Juan A Perez | 87654321",
      "nombre_clickup": "Juan A Perez",
      "nombre_normalizado": "JUAN A PEREZ",
      "status": "Completed",
      "full_name_extracted": "Juan Antonio Perez",
      "phone_number": "5559876543",
      "id_mycase": "87654321",
      "date_created": "2024-01-10T09:00:00Z",
      "date_updated": "2024-01-18T16:20:00Z",
      "synced_at": "2024-01-18T16:25:00Z"
    }
  ]
}
```

#### Ejemplo 2: Búsqueda con typo (fuzzy matching)

```bash
# Nota el typo: "Peres" en lugar de "Perez"
curl "http://localhost:8080/leads/search?q=Juan+Peres"
```

Encuentra "Juan Perez" gracias a pg_trgm similarity.

#### Ejemplo 3: Limitar resultados

```bash
curl "http://localhost:8080/leads/search?q=Maria&limit=5"
```

Retorna máximo 5 resultados.

#### Ejemplo 4: Con Python (requests)

```python
import requests

response = requests.get(
    "http://localhost:8080/leads/search",
    params={"q": "Juan Perez", "limit": 10}
)

data = response.json()
print(f"Encontrados: {data['total']}")

for lead in data['results']:
    print(f"- {lead['nombre_clickup']} ({lead['task_id']})")
```

---

## Consulta de Lead Individual

### GET /leads/{task_id}

Obtiene un lead por su task_id de ClickUp.

```bash
curl "http://localhost:8080/leads/abc123"
```

**Respuesta:**
```json
{
  "task_id": "abc123",
  "task_name": "Juan Perez | 12345678",
  "nombre_clickup": "Juan Perez",
  "nombre_normalizado": "JUAN PEREZ",
  "status": "Active",
  "assignee": "maria.lopez",
  "full_name_extracted": "Juan Alberto Perez",
  "phone_number": "5551234567",
  "email_extracted": "juan@example.com",
  "location": "Ciudad de México, CDMX",
  "interviewee": "Juan Alberto Perez",
  "interview_type": "Individual",
  "interview_result": "Done",
  "interview_other": "Cliente califica para VAWA. Evidencia documentada.",
  "case_type": "Immigration",
  "accident_last_2y": "no",
  "video_call": "yes",
  "id_mycase": "12345678",
  "mycase_link": "https://mycase.com/leads/12345678",
  "date_created": "2024-01-15T10:30:00Z",
  "date_updated": "2024-01-20T14:45:00Z",
  "synced_at": "2024-01-20T15:00:00Z"
}
```

**Error 404:**
```bash
curl "http://localhost:8080/leads/nonexistent"
```

```json
{
  "detail": "Lead nonexistent not found"
}
```

---

## Consulta por MyCase ID

### GET /leads/mycase/{mycase_id}

Obtiene un lead por su ID de MyCase (8 dígitos).

```bash
curl "http://localhost:8080/leads/mycase/12345678"
```

**Respuesta:** Mismo formato que GET /leads/{task_id}

---

## Listar Todos los Leads (Paginación)

### GET /leads/

Lista todos los leads con paginación.

#### Ejemplo 1: Primeros 100 registros

```bash
curl "http://localhost:8080/leads/"
```

#### Ejemplo 2: Página 2 (skip 100, limit 100)

```bash
curl "http://localhost:8080/leads/?skip=100&limit=100"
```

#### Ejemplo 3: Límite personalizado

```bash
curl "http://localhost:8080/leads/?skip=0&limit=50"
```

**Respuesta:** Array de leads (mismo schema que búsqueda)

```json
[
  {
    "task_id": "abc123",
    "task_name": "Juan Perez | 12345678",
    ...
  },
  {
    "task_id": "def456",
    "task_name": "Maria Garcia | 87654321",
    ...
  }
]
```

---

## Webhook de ClickUp

### POST /webhooks/clickup

**⚠️ Este endpoint es llamado por ClickUp, no manualmente.**

#### Configuración en ClickUp

1. Ir a ClickUp → Settings → Integrations → Webhooks
2. Crear webhook:
   - **Endpoint:** `https://YOUR-URL/webhooks/clickup`
   - **Events:** `taskUpdated`, `taskCreated`
   - **Secret:** (mismo que `CLICKUP_WEBHOOK_SECRET` en .env)

#### Payload de ejemplo (enviado por ClickUp)

```json
{
  "event": "taskUpdated",
  "task_id": "abc123",
  "history_items": [
    {
      "field": "status",
      "before": "In Progress",
      "after": "Completed"
    }
  ]
}
```

#### Respuesta del servidor

```json
{
  "status": "queued",
  "task_id": "abc123"
}
```

#### Testing manual (simulación)

```bash
curl -X POST "http://localhost:8080/webhooks/clickup" \
  -H "Content-Type: application/json" \
  -H "X-Signature: your_webhook_secret" \
  -d '{
    "event": "taskUpdated",
    "task_id": "abc123"
  }'
```

⚠️ Requiere que el task_id exista en ClickUp.

---

## Casos de Uso Prácticos

### 1. Buscar cliente por teléfono (via nombre)

Si el cliente dice "Soy Juan", pero no recuerdas su apellido:

```bash
curl "http://localhost:8080/leads/search?q=Juan&limit=20"
```

Filtrar en cliente/script los resultados por `phone_number`.

### 2. Verificar duplicados antes de crear lead

Antes de crear un nuevo lead en ClickUp:

```bash
curl "http://localhost:8080/leads/search?q=Maria+Garcia&limit=5"
```

Si `total > 0`, revisar si es duplicado.

### 3. Obtener todos los leads actualizados hoy

**Nota:** Requiere agregar endpoint `/leads/recent` (no implementado aún).

Alternativa: usar paginación y filtrar en cliente por `date_updated`.

### 4. Integración con MCP (Model Context Protocol)

```python
# Pseudocódigo de MCP Tool
def search_legal_leads(query: str) -> list:
    """Busca leads en Nexus Legal Integration"""
    response = requests.get(
        "https://nexus-api.run.app/leads/search",
        params={"q": query, "limit": 10}
    )
    return response.json()["results"]

# Uso en agente IA
agent.add_tool(search_legal_leads)

# El agente puede llamar:
# search_legal_leads("Juan Perez VAWA case")
```

---

## Documentación Interactiva

### Swagger UI (OpenAPI)

Abrir en navegador:
```
http://localhost:8080/docs
```

Permite:
- Ver todos los endpoints
- Probar requests directamente
- Ver schemas de request/response
- Descargar OpenAPI spec (JSON)

### ReDoc (Alternativa)

```
http://localhost:8080/redoc
```

Documentación más limpia y legible.

---

## Errores Comunes

### 400 Bad Request

```json
{
  "detail": [
    {
      "loc": ["query", "q"],
      "msg": "ensure this value has at least 2 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Causa:** Query de búsqueda demasiado corto (mínimo 2 caracteres).

### 401 Unauthorized (Webhook)

```json
{
  "detail": "Invalid webhook signature"
}
```

**Causa:** Header `X-Signature` no coincide con `CLICKUP_WEBHOOK_SECRET`.

### 404 Not Found

```json
{
  "detail": "Lead abc123 not found"
}
```

**Causa:** El task_id no existe en la base de datos.

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

**Causa:** Error de servidor. Revisar logs:

```bash
# Local
tail -f logs/app.log

# Cloud Run
gcloud run logs read nexus-legal-api --region us-central1
```

---

## Rate Limiting

**Actualmente no implementado.**

Recomendación para producción:
- Implementar con `slowapi` o `fastapi-limiter`
- Límite sugerido: 100 requests/min por IP

---

## Postman Collection

### Importar a Postman

Crear colección con estos endpoints:

```json
{
  "info": {
    "name": "Nexus Legal Integration API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/"
      }
    },
    {
      "name": "Search Leads",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/leads/search?q=Juan&limit=10",
          "query": [
            {"key": "q", "value": "Juan"},
            {"key": "limit", "value": "10"}
          ]
        }
      }
    },
    {
      "name": "Get Lead by Task ID",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/leads/{{task_id}}"
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:8080"}
  ]
}
```

---

## Próximos Endpoints (Roadmap)

- [ ] `POST /leads/batch` - Carga masiva
- [ ] `GET /leads/recent?since=2024-01-01` - Leads actualizados desde fecha
- [ ] `GET /tasks/{task_id}/comments` - Extracción de comentarios
- [ ] `POST /sync/sheets` - Trigger manual de sync a Google Sheets
- [ ] `GET /stats` - Estadísticas (total leads, por status, etc.)

---

**Versión:** 2.2.0
**Última actualización:** 2026-01-23

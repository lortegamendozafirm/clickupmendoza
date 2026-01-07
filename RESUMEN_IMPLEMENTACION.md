# Resumen de Implementación - Nexus Legal Integration v2.1

## Integración Google Sheets + External Dispatch

**Fecha:** 2026-01-06
**Versión:** 2.1
**Estado:** ✅ Completo

---

## Objetivos Cumplidos

✅ Autenticación Google Sheets vía Service Account
✅ Servicio genérico de escritura a Google Sheets
✅ Filtrado de webhooks por lista específica (CLICKUP_LIST_ID)
✅ Trigger condicional basado en campo "Link Intake"
✅ Dispatch HTTP externo configurable
✅ Sincronización automática a Google Sheets
✅ Script de registro de webhook
✅ Documentación completa

---

## Archivos Modificados

### 1. [app/config.py](app/config.py)
**Modificaciones:**
- Agregado soporte para credenciales de Google Service Account
- Nuevo campo: `google_sheets_credentials_json` (JSON string)
- Nuevo campo: `google_sheets_field_mapping` (mapeo de campos a columnas)
- Nuevo campo: `external_dispatch_enabled` (flag)
- Nuevo campo: `external_dispatch_url` (URL destino)
- Nuevo property: `google_credentials_dict` (parsea JSON de credenciales)
- Nuevo property: `sheets_field_mapping_dict` (parsea mapeo de campos)

**Características:**
- Soporta credenciales desde JSON string (Cloud Run/Secrets) o file path (local)
- Validación automática de JSON
- Backward compatible con configuración existente

---

### 2. [requirements.txt](requirements.txt)
**Modificaciones:**
- Actualizado `gspread` de 5.12.3 a 6.0.0
- Agregado `google-auth-oauthlib==1.2.0`
- Removido `oauth2client` (deprecado)

**Dependencias nuevas para Google Sheets:**
```txt
gspread==6.0.0
google-auth-oauthlib==1.2.0
```

---

### 3. [app/services/sheets_service.py](app/services/sheets_service.py) (NUEVO)
**Funcionalidad:**
- Clase `GoogleSheetsService` para interactuar con Google Sheets API
- Autenticación vía Service Account (JSON string o file path)
- Método `write_row()` dinámico con mapeo configurable
- Método `update_cell()` para actualizar celdas específicas
- Método `get_all_records()` para leer datos
- Manejo robusto de errores (sheet no encontrado, spreadsheet no encontrado, etc.)
- Logging detallado para debugging

**Ejemplo de uso:**
```python
from app.services.sheets_service import GoogleSheetsService

sheets_service = GoogleSheetsService()

data = {
    "task_id": "abc123",
    "task_name": "Juan Pérez",
    "link_intake": "https://intake.example.com/abc123"
}

success = sheets_service.write_row(data)
```

---

### 4. [app/api/webhooks.py](app/api/webhooks.py)
**Modificaciones principales:**
- Agregado filtrado por `CLICKUP_LIST_ID`
- Agregada lógica de trigger condicional (campo "Link Intake")
- Agregada función `_dispatch_to_external_service()` para HTTP dispatch
- Agregada función `_sync_to_google_sheets()` para sincronización
- Response ampliado con información de acciones ejecutadas

**Flujo actualizado:**
1. Validar firma del webhook
2. Parsear payload
3. **FILTRO:** Solo procesar si la tarea es de la lista configurada
4. Obtener tarea completa de ClickUp API
5. **TRIGGER:** Verificar si campo "Link Intake" tiene valor
6. Si trigger activo:
   - **Acción 1:** Enviar payload a URL externa (si está habilitado)
   - **Acción 2:** Escribir fila en Google Sheets (si está habilitado)
7. Guardar en base de datos (lógica existente)

**Response JSON:**
```json
{
  "status": "success",
  "event": "taskUpdated",
  "task_id": "abc123",
  "list_id": "list_123",
  "trigger_actions": true,
  "link_intake_value": "https://intake.example.com/abc123",
  "external_dispatch": true,
  "sheets_sync": true,
  "synced_at": "2026-01-06T12:00:00"
}
```

---

### 5. [scripts/register_webhook.py](scripts/register_webhook.py) (NUEVO)
**Funcionalidad:**
- Script interactivo para registrar webhooks en ClickUp
- Lee configuración desde `.env`
- Obtiene automáticamente el Team ID
- Lista webhooks existentes
- Registra webhook para lista específica
- Eventos: `taskCreated`, `taskUpdated`

**Uso:**
```bash
python scripts/register_webhook.py
```

**Requisitos:**
- `CLICKUP_API_TOKEN`
- `CLICKUP_LIST_ID`
- `CLICKUP_WEBHOOK_SECRET`

---

### 6. [.env.example](.env.example)
**Nuevas variables agregadas:**

```bash
# Google Sheets (Service Account)
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz
GOOGLE_SHEETS_SHEET_NAME=Leads DVS
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id": 1, "task_name": 2, ...}'

# External Dispatch
EXTERNAL_DISPATCH_ENABLED=true
EXTERNAL_DISPATCH_URL=https://external-service.com/api/webhook
```

---

## Archivos de Documentación Nuevos

### 7. [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) (NUEVO)
**Contenido:**
- Guía completa de configuración
- Paso a paso para crear Service Account
- Configuración de variables de entorno
- Explicación del mapeo de campos
- Lógica del trigger condicional
- Instrucciones de deployment
- Testing local
- Troubleshooting

### 8. [VARIABLES_DE_ENTORNO.md](VARIABLES_DE_ENTORNO.md) (NUEVO)
**Contenido:**
- Lista completa de variables de entorno
- Descripción detallada de cada variable
- Ejemplos de configuración
- Configuración en Cloud Run con Secret Manager
- Checklist de configuración
- Troubleshooting de variables

### 9. [RESUMEN_IMPLEMENTACION.md](RESUMEN_IMPLEMENTACION.md) (este archivo)
**Contenido:**
- Resumen ejecutivo de la implementación
- Lista de archivos modificados
- Características nuevas
- Instrucciones de uso

---

## Nuevas Variables de Entorno Requeridas

### Obligatorias para Google Sheets

```bash
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=tu_spreadsheet_id
GOOGLE_SHEETS_SHEET_NAME=Leads DVS

# Una de estas dos (prioridad a JSON):
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json

# Mapeo de campos
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id": 1, "task_name": 2, "status": 3, "link_intake": 4}'
```

### Obligatorias para External Dispatch

```bash
EXTERNAL_DISPATCH_ENABLED=true
EXTERNAL_DISPATCH_URL=https://tu-servicio.com/api/webhook
```

### Actualizada (ya existía)

```bash
CLICKUP_LIST_ID=12345678  # Ahora se usa para filtrar webhooks
```

---

## Arquitectura de la Integración

```
┌─────────────────────────────────────────────────────────────────┐
│                        ClickUp Webhook                          │
│                     (taskUpdated/Created)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │  Validar Firma      │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Filtrar por Lista  │◄─── CLICKUP_LIST_ID
                   │  (CLICKUP_LIST_ID)  │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Obtener Tarea      │
                   │  Completa (API)     │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Verificar Campo    │
                   │  "Link Intake"      │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    │ ¿Tiene valor?     │
                    └─────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 │ NO                      │ SÍ
                 ▼                         ▼
    ┌────────────────────┐    ┌───────────────────────┐
    │ Solo guardar en DB │    │  TRIGGER ACTIVADO     │
    └────────────────────┘    └───────────┬───────────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                              ▼                       ▼
                  ┌──────────────────────┐  ┌──────────────────────┐
                  │  External Dispatch   │  │  Google Sheets Sync  │
                  │  (HTTP POST)         │  │  (Append Row)        │
                  └──────────────────────┘  └──────────────────────┘
                              │                       │
                              └───────────┬───────────┘
                                          ▼
                                ┌─────────────────────┐
                                │  Guardar en DB      │
                                │  (existente)        │
                                └─────────────────────┘
```

---

## Lógica del Trigger Condicional

### Condiciones para Activar Acciones

Las acciones (External Dispatch + Google Sheets) se ejecutan cuando:

1. ✅ El evento es `taskUpdated` o `taskCreated`
2. ✅ La tarea pertenece a la lista `CLICKUP_LIST_ID`
3. ✅ El campo personalizado "Link Intake" tiene un valor (no vacío)

### Campos del Trigger

**Campo monitoreado:** `Link Intake` (Custom Field de ClickUp)

**Valor esperado:** Cualquier string no vacío (típicamente una URL)

**Ejemplo:**
```json
{
  "custom_fields": [
    {
      "name": "Link Intake",
      "value": "https://intake.example.com/abc123"
    }
  ]
}
```

---

## Payload del External Dispatch

Cuando se dispara el trigger, se envía este JSON al servicio externo:

```json
{
  "task_id": "abc123",
  "task_name": "Juan Pérez - Consulta Legal",
  "link_intake": "https://intake.example.com/abc123",
  "status": "in progress",
  "list_id": "list_123",
  "url": "https://app.clickup.com/t/abc123",
  "date_created": "1704470400000",
  "date_updated": "1704556800000"
}
```

**Headers:**
```
Content-Type: application/json
```

**Método:** POST

**Timeout:** 10 segundos

---

## Mapeo Dinámico a Google Sheets

### Configuración del Mapeo

El mapeo se define en la variable de entorno `GOOGLE_SHEETS_FIELD_MAPPING`:

```json
{
  "task_id": 1,
  "task_name": 2,
  "status": 3,
  "link_intake": 4,
  "url": 5,
  "date_created": 6,
  "date_updated": 7
}
```

### Campos Disponibles

**Campos estándar de tarea:**
- `task_id`: ID de la tarea
- `task_name`: Nombre de la tarea
- `status`: Estado actual
- `url`: URL de la tarea en ClickUp
- `date_created`: Timestamp de creación
- `date_updated`: Timestamp de última actualización

**Custom Fields:**
- Se agregan automáticamente al diccionario
- Nombres convertidos a snake_case
- Ejemplo: "Link Intake" → `link_intake`
- Ejemplo: "Phone Number" → `phone_number`

### Estructura del Google Sheet

Asegúrate de que tu hoja tenga encabezados en la primera fila que correspondan con el mapeo:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| Task ID | Task Name | Status | Link Intake | URL | Date Created | Date Updated |

---

## Pasos para Deployment

### 1. Configurar Service Account de Google

```bash
# Crear Service Account en Google Cloud Console
# Descargar credenciales JSON
# Compartir el spreadsheet con el email del service account
```

### 2. Configurar Variables de Entorno

```bash
# Copiar .env.example a .env
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Registrar Webhook en ClickUp

```bash
python scripts/register_webhook.py
```

### 5. Ejecutar Localmente (Opcional)

```bash
uvicorn app.main:app --reload --port 8080
```

### 6. Deploy a Cloud Run

```bash
# Crear secrets en Secret Manager
gcloud secrets create GOOGLE_SHEETS_CREDENTIALS_JSON --data-file=service-account.json

# Deploy
gcloud run deploy nexus-legal-api \
  --image gcr.io/$PROJECT_ID/nexus-legal-api \
  --set-secrets GOOGLE_SHEETS_CREDENTIALS_JSON=GOOGLE_SHEETS_CREDENTIALS_JSON:latest \
  --set-env-vars GOOGLE_SHEETS_ENABLED=true,CLICKUP_LIST_ID=12345678
```

---

## Testing

### Test 1: Autenticación con Google Sheets

```python
from app.services.sheets_service import GoogleSheetsService

service = GoogleSheetsService()
data = {"task_id": "test123", "task_name": "Test"}
success = service.write_row(data)
print(f"Success: {success}")
```

### Test 2: Webhook Completo

```bash
curl -X POST http://localhost:8080/webhooks/clickup \
  -H "Content-Type: application/json" \
  -H "X-Signature: tu_signature" \
  -d '{
    "event": "taskUpdated",
    "task_id": "abc123"
  }'
```

### Test 3: External Dispatch

Verifica que tu servicio externo reciba el payload correctamente.

---

## Monitoreo

### Logs a Monitorear

```
✓ Successfully authenticated with Google Sheets (JSON)
✓ Task abc123: 'Link Intake' field has value. Triggering actions.
✓ Successfully dispatched task abc123 to external service: 200
✓ Successfully synced task abc123 to Google Sheets
```

### Errores Comunes

```
❌ Google Sheets client not authenticated
❌ Worksheet 'X' not found in spreadsheet
❌ HTTP error dispatching task to external service
```

### Ver Logs en Cloud Run

```bash
gcloud run logs read nexus-legal-api --region us-central1 --limit 100
```

---

## Mantenimiento

### Actualizar Field Mapping

Si necesitas cambiar el mapeo de columnas:

1. Actualizar la variable `GOOGLE_SHEETS_FIELD_MAPPING` en `.env`
2. Reiniciar la aplicación
3. No es necesario redeployar (si usas Secret Manager, actualizar el secret)

### Rotar Credenciales de Service Account

1. Crear nuevas credenciales en Google Cloud Console
2. Actualizar `GOOGLE_SHEETS_CREDENTIALS_JSON`
3. Revocar credenciales antiguas

### Cambiar Lista Monitoreada

1. Actualizar `CLICKUP_LIST_ID` en `.env`
2. Re-registrar webhook con `scripts/register_webhook.py`
3. Reiniciar aplicación

---

## Seguridad

### Consideraciones

✅ Webhooks validados con firma HMAC
✅ HTTPS obligatorio en Cloud Run
✅ Credenciales en Secret Manager (producción)
✅ Service Account con mínimos permisos necesarios
✅ Timeout en HTTP requests externos (10s)
✅ Logs no exponen credenciales

### Recomendaciones

- Rota las credenciales regularmente
- No commits el archivo `.env` a Git
- Usa Secret Manager en producción
- Monitorea logs para intentos de acceso no autorizado
- Limita el scope del Service Account de Google

---

## Próximos Pasos (Opcionales)

- [ ] Agregar retry logic para External Dispatch fallido
- [ ] Implementar queue (Cloud Tasks) para procesos asíncronos
- [ ] Agregar métricas (contador de triggers, success rate)
- [ ] Dashboard de Looker Studio conectado a Google Sheets
- [ ] Agregar más campos personalizados al mapeo
- [ ] Implementar batch updates para Google Sheets (mejor performance)

---

## Contacto y Soporte

Para issues, preguntas o mejoras, contactar al equipo de desarrollo.

**Versión del documento:** 1.0
**Fecha:** 2026-01-06
**Autor:** Claude Code (Anthropic)

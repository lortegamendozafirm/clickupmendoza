# Variables de Entorno - Nexus Legal Integration v2.1

## Nuevas Variables Requeridas

Esta es la lista completa de variables de entorno necesarias para las nuevas funcionalidades de integración con Google Sheets y External Dispatch.

---

## Variables Obligatorias Existentes

```bash
# ClickUp API
CLICKUP_API_TOKEN=pk_YOUR_API_TOKEN
CLICKUP_WEBHOOK_SECRET=your_webhook_secret
CLICKUP_LIST_ID=12345678  # ID de la lista a monitorear

# Database
DATABASE_URL=postgresql://user:pass@host/db
```

---

## Nuevas Variables - Google Sheets

### Habilitar Google Sheets

```bash
GOOGLE_SHEETS_ENABLED=true
```

### Identificación del Spreadsheet

```bash
# ID del spreadsheet (de la URL)
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz_tu_spreadsheet_id

# Nombre de la hoja/pestaña
GOOGLE_SHEETS_SHEET_NAME=Leads DVS
```

### Credenciales de Service Account

**Opción 1: JSON String (Recomendado para Cloud Run)**

```bash
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"tu-proyecto","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"service-account@proyecto.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
```

**Opción 2: Path a Archivo (Desarrollo Local)**

```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json
```

### Mapeo de Campos a Columnas

Define qué campo va en qué columna del Google Sheet:

```bash
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id": 1, "task_name": 2, "status": 3, "link_intake": 4, "url": 5, "date_created": 6, "date_updated": 7}'
```

**Campos disponibles:**
- Estándar: `task_id`, `task_name`, `status`, `url`, `date_created`, `date_updated`
- Custom Fields: Se convierten a snake_case
  - "Link Intake" → `link_intake`
  - "Phone Number" → `phone_number`
  - etc.

---

## Nuevas Variables - External Dispatch

### Habilitar External Dispatch

```bash
EXTERNAL_DISPATCH_ENABLED=true
```

### URL del Servicio Externo

```bash
EXTERNAL_DISPATCH_URL=https://tu-servicio-externo.com/api/webhook
```

El sistema enviará un HTTP POST con JSON a esta URL cuando se dispare el trigger.

**Payload ejemplo:**
```json
{
  "task_id": "abc123",
  "task_name": "Juan Pérez - Consulta",
  "link_intake": "https://intake.example.com/abc123",
  "status": "in progress",
  "list_id": "list_123",
  "url": "https://app.clickup.com/t/abc123",
  "date_created": "1704470400000",
  "date_updated": "1704556800000"
}
```

---

## Ejemplo Completo de .env

```bash
# ============================================================================
# Nexus Legal Integration v2.1 - Configuración Completa
# ============================================================================

# ----------------------------------------------------------------------------
# ClickUp API
# ----------------------------------------------------------------------------
CLICKUP_API_TOKEN=pk_YOUR_CLICKUP_API_TOKEN
CLICKUP_WEBHOOK_SECRET=your_webhook_secret_here
CLICKUP_TEAM_ID=your_team_id
CLICKUP_LIST_ID=12345678  # IMPORTANTE: Solo esta lista se procesará

# ----------------------------------------------------------------------------
# Database (PostgreSQL)
# ----------------------------------------------------------------------------
DATABASE_URL=postgresql://user:password@host:5432/nexus_legal_db?sslmode=require

# ----------------------------------------------------------------------------
# Google Sheets Integration
# ----------------------------------------------------------------------------
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz_tu_spreadsheet_id
GOOGLE_SHEETS_SHEET_NAME=Leads DVS

# Credenciales (elegir una opción)
# Opción 1: JSON string (para Cloud Run)
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'

# Opción 2: Path a archivo (para local)
# GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json

# Mapeo de campos a columnas
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id": 1, "task_name": 2, "status": 3, "link_intake": 4, "url": 5, "date_created": 6}'

# ----------------------------------------------------------------------------
# External Dispatch
# ----------------------------------------------------------------------------
EXTERNAL_DISPATCH_ENABLED=true
EXTERNAL_DISPATCH_URL=https://tu-servicio-externo.com/api/webhook

# ----------------------------------------------------------------------------
# Application
# ----------------------------------------------------------------------------
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=*

# ----------------------------------------------------------------------------
# Security (Opcional)
# ----------------------------------------------------------------------------
ENCRYPTION_KEY=your_32_byte_hex_key
```

---

## Configuración en Cloud Run (Secret Manager)

Para producción, es recomendado usar Secret Manager:

### Crear Secrets

```bash
# ClickUp
echo -n "pk_YOUR_TOKEN" | gcloud secrets create CLICKUP_API_TOKEN --data-file=-
echo -n "webhook_secret" | gcloud secrets create CLICKUP_WEBHOOK_SECRET --data-file=-

# Database
echo -n "postgresql://..." | gcloud secrets create DATABASE_URL --data-file=-

# Google Sheets - Service Account JSON
cat service-account.json | gcloud secrets create GOOGLE_SHEETS_CREDENTIALS_JSON --data-file=-

# Google Sheets - Field Mapping
echo -n '{"task_id":1,...}' | gcloud secrets create GOOGLE_SHEETS_FIELD_MAPPING --data-file=-

# External Dispatch
echo -n "https://external-service.com/api" | gcloud secrets create EXTERNAL_DISPATCH_URL --data-file=-
```

### Deploy con Secrets

```bash
gcloud run deploy nexus-legal-api \
  --image gcr.io/$PROJECT_ID/nexus-legal-api \
  --region us-central1 \
  --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest,\
CLICKUP_WEBHOOK_SECRET=CLICKUP_WEBHOOK_SECRET:latest,\
DATABASE_URL=DATABASE_URL:latest,\
GOOGLE_SHEETS_CREDENTIALS_JSON=GOOGLE_SHEETS_CREDENTIALS_JSON:latest,\
GOOGLE_SHEETS_FIELD_MAPPING=GOOGLE_SHEETS_FIELD_MAPPING:latest,\
EXTERNAL_DISPATCH_URL=EXTERNAL_DISPATCH_URL:latest \
  --set-env-vars GOOGLE_SHEETS_ENABLED=true,\
EXTERNAL_DISPATCH_ENABLED=true,\
CLICKUP_LIST_ID=12345678,\
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz,\
GOOGLE_SHEETS_SHEET_NAME="Leads DVS",\
APP_ENV=production
```

---

## Validación de Variables

Puedes validar que todas las variables estén configuradas correctamente ejecutando:

```python
from app.config import settings

# Verificar ClickUp
print(f"ClickUp List ID: {settings.clickup_list_id}")

# Verificar Google Sheets
print(f"Google Sheets Enabled: {settings.google_sheets_enabled}")
print(f"Spreadsheet ID: {settings.google_sheets_spreadsheet_id}")
print(f"Has Credentials: {bool(settings.google_credentials_dict or settings.google_sheets_credentials_path)}")
print(f"Field Mapping: {settings.sheets_field_mapping_dict}")

# Verificar External Dispatch
print(f"External Dispatch Enabled: {settings.external_dispatch_enabled}")
print(f"External URL: {settings.external_dispatch_url}")
```

---

## Prioridad de Configuración

La configuración sigue este orden de prioridad:

1. **Variables de entorno del sistema** (mayor prioridad)
2. **Archivo .env** en el directorio raíz
3. **Valores por defecto** en `app/config.py` (menor prioridad)

Para credenciales de Google:
1. `GOOGLE_SHEETS_CREDENTIALS_JSON` (prioridad)
2. `GOOGLE_SHEETS_CREDENTIALS_PATH` (fallback)

---

## Checklist de Configuración

Antes de deployment, verifica:

- [ ] `CLICKUP_API_TOKEN` configurado
- [ ] `CLICKUP_WEBHOOK_SECRET` configurado
- [ ] `CLICKUP_LIST_ID` configurado (ID de la lista a monitorear)
- [ ] `DATABASE_URL` configurado
- [ ] `GOOGLE_SHEETS_ENABLED=true` si quieres usar Sheets
- [ ] `GOOGLE_SHEETS_SPREADSHEET_ID` configurado
- [ ] `GOOGLE_SHEETS_CREDENTIALS_JSON` o `GOOGLE_SHEETS_CREDENTIALS_PATH` configurado
- [ ] `GOOGLE_SHEETS_FIELD_MAPPING` configurado con mapeo correcto
- [ ] Service Account tiene acceso al spreadsheet (compartido como Editor)
- [ ] `EXTERNAL_DISPATCH_ENABLED=true` si quieres dispatch externo
- [ ] `EXTERNAL_DISPATCH_URL` apunta al servicio correcto
- [ ] Webhook registrado en ClickUp usando `scripts/register_webhook.py`

---

## Troubleshooting

### Error: "Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON"

El JSON debe ser válido. Verifica:
- Que las comillas estén escapadas correctamente
- Que no haya saltos de línea en el string (excepto dentro de `private_key`)
- Usa comillas simples para envolver el JSON completo

### Error: "Invalid JSON in GOOGLE_SHEETS_FIELD_MAPPING"

El mapeo debe ser un objeto JSON válido:
```json
{"campo": numero_columna}
```

### Service Account no tiene acceso

1. Verifica que el email del service account esté en el spreadsheet compartido
2. Verifica que tenga permisos de "Editor"
3. El email está en el campo `client_email` del JSON de credenciales

---

## Referencias

- [Google Sheets API](https://developers.google.com/sheets/api)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [ClickUp API](https://clickup.com/api)
- [ClickUp Webhooks](https://clickup.com/api/clickupdocs/Webhooks)

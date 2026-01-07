# Referencia Rápida - Nexus Legal Integration v2.1

Guía de consulta rápida para las operaciones más comunes.

---

## Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar .env

```bash
cp .env.example .env
nano .env  # Editar con tus credenciales
```

### 3. Registrar Webhook

```bash
python scripts/register_webhook.py
```

### 4. Ejecutar

```bash
uvicorn app.main:app --reload --port 8080
```

---

## Variables de Entorno Esenciales

```bash
# ClickUp
CLICKUP_API_TOKEN=pk_YOUR_TOKEN
CLICKUP_WEBHOOK_SECRET=your_secret
CLICKUP_LIST_ID=12345678

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Google Sheets
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id":1,"task_name":2,...}'

# External Dispatch
EXTERNAL_DISPATCH_ENABLED=true
EXTERNAL_DISPATCH_URL=https://external-service.com/api/webhook
```

---

## Endpoints Principales

### Webhook de ClickUp

```
POST /webhooks/clickup
```

Headers:
- `X-Signature`: Firma del webhook de ClickUp
- `Content-Type`: application/json

### Búsqueda de Leads

```
GET /leads/search?q=nombre&limit=10
```

### Health Check

```
GET /health
```

---

## Configurar Google Service Account

### 1. Crear Service Account

1. [Google Cloud Console](https://console.cloud.google.com/) → IAM & Admin → Service Accounts
2. Create Service Account
3. Download JSON key

### 2. Compartir Spreadsheet

1. Abre el JSON y copia el `client_email`
2. Comparte tu Google Sheet con ese email
3. Asigna permisos de "Editor"

### 3. Configurar Variable

**Opción A (Cloud Run):**
```bash
cat service-account.json | gcloud secrets create GOOGLE_SHEETS_CREDENTIALS_JSON --data-file=-
```

**Opción B (Local):**
```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json
```

---

## Mapeo de Campos

Define qué dato va en qué columna del Google Sheet:

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

Campos disponibles:
- Estándar: `task_id`, `task_name`, `status`, `url`, `date_created`, `date_updated`
- Custom Fields: `link_intake`, `phone`, `email`, etc. (en snake_case)

---

## Lógica del Trigger

Las acciones se disparan cuando:

1. ✅ Evento es `taskUpdated` o `taskCreated`
2. ✅ Tarea pertenece a `CLICKUP_LIST_ID`
3. ✅ Campo "Link Intake" tiene valor

Acciones ejecutadas:
- **External Dispatch**: HTTP POST a URL configurada
- **Google Sheets**: Append row con datos de la tarea

---

## Comandos Útiles

### Ver Logs (Local)

```bash
tail -f app.log
```

### Ver Logs (Cloud Run)

```bash
gcloud run logs read nexus-legal-api --region us-central1 --limit 100
```

### Test de Autenticación Google Sheets

```python
from app.services.sheets_service import GoogleSheetsService

service = GoogleSheetsService()
data = {"task_id": "test", "task_name": "Test Lead"}
success = service.write_row(data)
print(f"Success: {success}")
```

### Simular Webhook

```bash
curl -X POST http://localhost:8080/webhooks/clickup \
  -H "Content-Type: application/json" \
  -H "X-Signature: your_signature" \
  -d '{"event":"taskUpdated","task_id":"abc123"}'
```

---

## Deployment a Cloud Run

### Deploy Rápido

```bash
./deploy.sh
```

### Deploy Manual

```bash
# Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/nexus-legal-api

# Deploy
gcloud run deploy nexus-legal-api \
  --image gcr.io/$PROJECT_ID/nexus-legal-api \
  --region us-central1 \
  --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest,\
GOOGLE_SHEETS_CREDENTIALS_JSON=GOOGLE_SHEETS_CREDENTIALS_JSON:latest \
  --set-env-vars GOOGLE_SHEETS_ENABLED=true,CLICKUP_LIST_ID=12345678
```

---

## Troubleshooting

### Webhook no se dispara

```bash
# Verificar webhook en ClickUp
# Settings → Integrations → Webhooks

# Verificar logs
gcloud run logs read nexus-legal-api --limit 50
```

### Google Sheets no escribe

```bash
# Verificar autenticación
python -c "from app.services.sheets_service import GoogleSheetsService; GoogleSheetsService()"

# Verificar que service account tenga acceso al spreadsheet
# Verificar GOOGLE_SHEETS_FIELD_MAPPING sea JSON válido
```

### External Dispatch falla

```bash
# Verificar URL es accesible
curl -X POST $EXTERNAL_DISPATCH_URL \
  -H "Content-Type: application/json" \
  -d '{"task_id":"test"}'

# Verificar logs para error específico
```

---

## Estructura de Archivos Clave

```
clickupmendoza/
├── app/
│   ├── config.py                 # Configuración
│   ├── api/webhooks.py           # Webhook endpoint
│   └── services/
│       └── sheets_service.py     # Servicio Google Sheets
├── scripts/
│   └── register_webhook.py       # Registrar webhook
├── .env                          # Variables de entorno (NO commitear)
├── requirements.txt              # Dependencias
└── README.md                     # Documentación principal
```

---

## Logs Importantes

### Éxito

```
✓ Successfully authenticated with Google Sheets
✓ Task abc123: 'Link Intake' field has value. Triggering actions.
✓ Successfully dispatched task abc123 to external service: 200
✓ Successfully synced task abc123 to Google Sheets
```

### Errores

```
❌ Google Sheets client not authenticated
❌ Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON
❌ Worksheet 'X' not found in spreadsheet
❌ HTTP error dispatching task to external service
```

---

## Checklist Pre-Deployment

- [ ] Variables de entorno configuradas
- [ ] Service Account creado y JSON descargado
- [ ] Spreadsheet compartido con service account
- [ ] Field mapping configurado correctamente
- [ ] Webhook registrado en ClickUp
- [ ] Tests ejecutados localmente
- [ ] Secrets creados en Secret Manager (producción)
- [ ] Cloud Run service deployado
- [ ] Logs monitoreados después del deploy

---

## Links Útiles

- [Documentación completa](./README.md)
- [Guía de integración](./INTEGRATION_SETUP.md)
- [Variables de entorno](./VARIABLES_DE_ENTORNO.md)
- [Changelog](./CHANGELOG.md)
- [ClickUp API Docs](https://clickup.com/api)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

## Comandos de Mantenimiento

### Actualizar Dependencias

```bash
pip install --upgrade -r requirements.txt
```

### Rotar Credenciales

```bash
# Generar nuevas credenciales en Google Cloud Console
# Actualizar secret
cat new-service-account.json | gcloud secrets versions add GOOGLE_SHEETS_CREDENTIALS_JSON --data-file=-
```

### Cambiar Lista Monitoreada

```bash
# Actualizar .env
CLICKUP_LIST_ID=new_list_id

# Re-registrar webhook
python scripts/register_webhook.py

# Reiniciar servicio
gcloud run services update nexus-legal-api --region us-central1
```

---

**Versión:** 2.1.0
**Última actualización:** 2026-01-06

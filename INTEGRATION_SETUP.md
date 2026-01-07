# Guía de Configuración - Integración Google Sheets y External Dispatch

Documentación para las nuevas funcionalidades agregadas a **Nexus Legal Integration v2.1**.

## Resumen de Nuevas Funcionalidades

1. **Autenticación Google Sheets con Service Account**
2. **Servicio genérico de escritura en Google Sheets**
3. **Filtrado de webhooks por lista específica**
4. **Trigger condicional basado en el campo "Link Intake"**
5. **Dispatch HTTP externo cuando se cumple la condición**
6. **Sincronización automática a Google Sheets**

---

## 1. Configuración de Google Service Account

### Paso 1: Crear Service Account en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto o crea uno nuevo
3. Navega a **IAM & Admin → Service Accounts**
4. Click en **Create Service Account**:
   - **Name**: `nexus-legal-sheets-service`
   - **Description**: Service account para integración con Google Sheets
5. Click **Create and Continue**
6. No es necesario agregar roles adicionales
7. Click **Done**

### Paso 2: Generar Credenciales JSON

1. En la lista de Service Accounts, encuentra la cuenta recién creada
2. Click en los 3 puntos → **Manage Keys**
3. Click **Add Key → Create New Key**
4. Selecciona **JSON** y descarga el archivo
5. Guarda el archivo de forma segura

### Paso 3: Dar Acceso al Spreadsheet

1. Abre el archivo JSON descargado y copia el email del service account (campo `client_email`)
2. Abre tu Google Spreadsheet
3. Click en **Share** (Compartir)
4. Pega el email del service account
5. Asigna permisos de **Editor**
6. Click **Send**

---

## 2. Configuración de Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

### Google Sheets

```bash
# Habilitar integración con Google Sheets
GOOGLE_SHEETS_ENABLED=true

# ID del Spreadsheet (obténlo de la URL)
# Ejemplo: https://docs.google.com/spreadsheets/d/1ABC123xyz.../edit
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz_tu_spreadsheet_id_aqui

# Nombre de la hoja dentro del spreadsheet
GOOGLE_SHEETS_SHEET_NAME=Leads DVS

# Opción 1: Para desarrollo local - Path al archivo JSON
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/service-account.json

# Opción 2: Para Cloud Run/producción - JSON string completo
# Recomendado: Crear secret en Secret Manager con el contenido del JSON
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key":"..."}'

# Mapeo de campos (qué dato va en qué columna)
# Ajusta según tu estructura de Google Sheets
GOOGLE_SHEETS_FIELD_MAPPING='{"task_id": 1, "task_name": 2, "status": 3, "link_intake": 4, "url": 5, "date_created": 6}'
```

### External Dispatch

```bash
# Habilitar envío a servicio externo
EXTERNAL_DISPATCH_ENABLED=true

# URL del servicio externo que recibirá los datos
EXTERNAL_DISPATCH_URL=https://tu-servicio-externo.com/api/webhook
```

### ClickUp

```bash
# ID de la lista de ClickUp a monitorear
# Solo se procesarán webhooks de esta lista
CLICKUP_LIST_ID=tu_list_id_aqui
```

---

## 3. Mapeo de Campos de Google Sheets

El mapeo de campos define qué datos de ClickUp van a qué columna en Google Sheets.

### Formato del Mapeo

```json
{
  "campo_de_tarea": numero_de_columna
}
```

### Campos Disponibles

Campos estándar de la tarea:
- `task_id`: ID de la tarea en ClickUp
- `task_name`: Nombre de la tarea
- `status`: Estado actual de la tarea
- `url`: URL de la tarea en ClickUp
- `date_created`: Fecha de creación
- `date_updated`: Fecha de última actualización

Campos personalizados (custom fields):
- Los custom fields se convierten automáticamente a formato snake_case
- Ejemplo: "Link Intake" → `link_intake`
- Ejemplo: "Phone Number" → `phone_number`

### Ejemplo de Mapeo Completo

```json
{
  "task_id": 1,
  "task_name": 2,
  "status": 3,
  "link_intake": 4,
  "phone": 5,
  "email": 6,
  "url": 7,
  "date_created": 8,
  "date_updated": 9
}
```

### Estructura Esperada del Google Sheet

Asegúrate de que tu hoja tenga encabezados en la primera fila:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| Task ID | Task Name | Status | Link Intake | Phone | Email | URL | Date Created | Date Updated |

---

## 4. Lógica de Trigger Condicional

### Cuándo se Disparan las Acciones

Las acciones (external dispatch + sheets sync) se disparan cuando:

1. El webhook viene de un evento `taskUpdated` o `taskCreated`
2. La tarea pertenece a la lista especificada en `CLICKUP_LIST_ID`
3. El campo personalizado "Link Intake" tiene un valor (no está vacío)

### Acciones Ejecutadas

Cuando se cumplen las condiciones:

**Acción 1: External Dispatch**
- Se envía un HTTP POST a la URL configurada en `EXTERNAL_DISPATCH_URL`
- Payload JSON con datos básicos de la tarea

**Acción 2: Google Sheets Sync**
- Se agrega una fila nueva al final del Google Sheet
- Los datos se mapean según `GOOGLE_SHEETS_FIELD_MAPPING`

### Payload del External Dispatch

Ejemplo del JSON enviado:

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

---

## 5. Registrar Webhook en ClickUp

Usa el script proporcionado para registrar el webhook:

```bash
python scripts/register_webhook.py
```

El script te pedirá:
1. La URL de tu endpoint (ej: `https://tu-api.run.app/webhooks/clickup`)
2. Confirmación si ya hay webhooks existentes

### Requisitos del Script

Asegúrate de tener configuradas estas variables en `.env`:
- `CLICKUP_API_TOKEN`
- `CLICKUP_LIST_ID`
- `CLICKUP_WEBHOOK_SECRET`

### Verificar el Webhook

Después de registrar:

1. Ve a ClickUp → Settings → Integrations → Webhooks
2. Verifica que el webhook esté activo
3. Verifica que los eventos sean: `taskCreated`, `taskUpdated`
4. Verifica que esté asociado a tu lista específica

---

## 6. Deployment en Cloud Run

### Configurar Secrets

Para producción, usa Google Secret Manager:

```bash
# Service Account JSON
echo '{"type":"service_account",...}' | gcloud secrets create GOOGLE_SHEETS_CREDENTIALS_JSON --data-file=-

# External Dispatch URL
echo -n "https://external-service.com/api/webhook" | gcloud secrets create EXTERNAL_DISPATCH_URL --data-file=-

# Field Mapping
echo -n '{"task_id":1,"task_name":2,...}' | gcloud secrets create GOOGLE_SHEETS_FIELD_MAPPING --data-file=-
```

### Deploy con Secrets

```bash
gcloud run deploy nexus-legal-api \
  --image gcr.io/$GCP_PROJECT_ID/nexus-legal-api \
  --region $GCP_REGION \
  --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest,\
CLICKUP_WEBHOOK_SECRET=CLICKUP_WEBHOOK_SECRET:latest,\
DATABASE_URL=DATABASE_URL:latest,\
GOOGLE_SHEETS_CREDENTIALS_JSON=GOOGLE_SHEETS_CREDENTIALS_JSON:latest,\
EXTERNAL_DISPATCH_URL=EXTERNAL_DISPATCH_URL:latest,\
GOOGLE_SHEETS_FIELD_MAPPING=GOOGLE_SHEETS_FIELD_MAPPING:latest \
  --set-env-vars GOOGLE_SHEETS_ENABLED=true,\
EXTERNAL_DISPATCH_ENABLED=true,\
CLICKUP_LIST_ID=tu_list_id,\
GOOGLE_SHEETS_SPREADSHEET_ID=tu_spreadsheet_id,\
GOOGLE_SHEETS_SHEET_NAME="Leads DVS"
```

---

## 7. Testing Local

### Probar Autenticación con Google Sheets

```python
from app.services.sheets_service import GoogleSheetsService

# Inicializar servicio
sheets_service = GoogleSheetsService()

# Probar escritura
data = {
    "task_id": "test123",
    "task_name": "Test Lead",
    "status": "open",
    "link_intake": "https://example.com/intake",
}

success = sheets_service.write_row(data)
print(f"Write successful: {success}")
```

### Simular Webhook

Usa curl o Postman para enviar un webhook de prueba:

```bash
curl -X POST http://localhost:8080/webhooks/clickup \
  -H "Content-Type: application/json" \
  -H "X-Signature: tu_signature_aqui" \
  -d '{
    "event": "taskUpdated",
    "task_id": "abc123"
  }'
```

---

## 8. Monitoreo y Logs

### Verificar Logs en Cloud Run

```bash
gcloud run logs read nexus-legal-api --region $GCP_REGION --limit 100
```

### Logs Clave

Busca estos mensajes en los logs:

```
✓ Autenticación exitosa con Google Sheets
✓ Task abc123: 'Link Intake' field has value. Triggering actions.
✓ Successfully dispatched task abc123 to external service: 200
✓ Successfully synced task abc123 to Google Sheets
```

### Errores Comunes

**Error: "Google Sheets client not authenticated"**
- Verifica que `GOOGLE_SHEETS_CREDENTIALS_JSON` o `GOOGLE_SHEETS_CREDENTIALS_PATH` estén configurados
- Verifica que el JSON sea válido

**Error: "Worksheet 'X' not found"**
- Verifica el nombre de la hoja en `GOOGLE_SHEETS_SHEET_NAME`
- Los nombres son case-sensitive

**Error: "Spreadsheet not found"**
- Verifica el `GOOGLE_SHEETS_SPREADSHEET_ID`
- Verifica que el service account tenga acceso al spreadsheet

---

## 9. Troubleshooting

### El webhook no se dispara

1. Verifica que el webhook esté registrado en ClickUp
2. Verifica que los eventos sean los correctos (`taskUpdated`, `taskCreated`)
3. Verifica que la tarea pertenezca a la lista configurada en `CLICKUP_LIST_ID`

### Las acciones no se ejecutan

1. Verifica que el campo "Link Intake" tenga un valor
2. Verifica que `GOOGLE_SHEETS_ENABLED=true` y `EXTERNAL_DISPATCH_ENABLED=true`
3. Revisa los logs para errores específicos

### No se escribe en Google Sheets

1. Verifica que el service account tenga permisos de Editor en el spreadsheet
2. Verifica que `GOOGLE_SHEETS_FIELD_MAPPING` sea un JSON válido
3. Verifica que el nombre de la hoja coincida exactamente

### External dispatch falla

1. Verifica que `EXTERNAL_DISPATCH_URL` sea accesible
2. Verifica que el servicio externo acepte JSON
3. Verifica que el timeout sea suficiente (default: 10s)

---

## 10. Estructura de Archivos Modificados

```
clickupmendoza/
├── app/
│   ├── config.py                      # ✨ Modificado: Nuevas variables de config
│   ├── api/
│   │   └── webhooks.py                # ✨ Modificado: Lógica de trigger y acciones
│   └── services/
│       └── sheets_service.py          # 🆕 Nuevo: Servicio de Google Sheets
├── scripts/
│   └── register_webhook.py            # 🆕 Nuevo: Script de registro de webhook
├── requirements.txt                   # ✨ Modificado: Dependencias actualizadas
├── .env.example                       # ✨ Modificado: Nuevas variables de entorno
└── INTEGRATION_SETUP.md               # 🆕 Nuevo: Esta guía
```

---

## Soporte

Para issues o preguntas sobre la integración, revisar los logs de la aplicación o contactar al equipo de desarrollo.

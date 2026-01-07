# Changelog - Nexus Legal Integration

Todos los cambios notables a este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.1.0] - 2026-01-06

### Agregado

#### Integración con Google Sheets
- Nuevo servicio `GoogleSheetsService` para interactuar con Google Sheets API
- Autenticación con Service Account (soporta JSON string y file path)
- Función `write_row()` dinámica con mapeo configurable de campos a columnas
- Función `update_cell()` para actualizar celdas específicas
- Función `get_all_records()` para leer datos del sheet
- Variables de entorno para configuración de Google Sheets:
  - `GOOGLE_SHEETS_ENABLED`
  - `GOOGLE_SHEETS_SPREADSHEET_ID`
  - `GOOGLE_SHEETS_SHEET_NAME`
  - `GOOGLE_SHEETS_CREDENTIALS_JSON` (prioridad para Cloud Run)
  - `GOOGLE_SHEETS_CREDENTIALS_PATH` (fallback para local)
  - `GOOGLE_SHEETS_FIELD_MAPPING`

#### External Dispatch
- Sistema de dispatch HTTP externo para notificar servicios de terceros
- Envío automático de payload JSON cuando se dispara el trigger
- Variables de entorno:
  - `EXTERNAL_DISPATCH_ENABLED`
  - `EXTERNAL_DISPATCH_URL`
- Timeout configurable (default: 10s)
- Retry logic con manejo de errores HTTP

#### Webhook Enhancement
- Filtrado de webhooks por lista específica (`CLICKUP_LIST_ID`)
- Trigger condicional basado en campo personalizado "Link Intake"
- Lógica de acciones duales:
  1. External Dispatch (HTTP POST)
  2. Google Sheets Sync (append row)
- Response mejorado con información detallada de acciones ejecutadas

#### Scripts
- `scripts/register_webhook.py`: Script interactivo para registrar webhooks en ClickUp
  - Obtiene automáticamente el Team ID
  - Lista webhooks existentes
  - Registra webhook específico para lista configurada
  - Validación de variables de entorno

#### Documentación
- `INTEGRATION_SETUP.md`: Guía completa de configuración y uso
- `VARIABLES_DE_ENTORNO.md`: Referencia de todas las variables de entorno
- `RESUMEN_IMPLEMENTACION.md`: Resumen técnico de la implementación
- `CHANGELOG.md`: Este archivo

### Modificado

#### Configuración
- `app/config.py`:
  - Agregado soporte para credenciales de Google Service Account
  - Nuevos campos de configuración para Google Sheets
  - Nuevos campos de configuración para External Dispatch
  - Property `google_credentials_dict` para parsear JSON de credenciales
  - Property `sheets_field_mapping_dict` para parsear mapeo de campos
  - Validación automática de JSON en configuración

#### Webhooks
- `app/api/webhooks.py`:
  - Agregado filtrado por `CLICKUP_LIST_ID`
  - Agregada detección de campo "Link Intake" en custom fields
  - Agregada función helper `_dispatch_to_external_service()`
  - Agregada función helper `_sync_to_google_sheets()`
  - Response ampliado con información de:
    - `trigger_actions`: Si se dispararon las acciones
    - `link_intake_value`: Valor del campo Link Intake
    - `external_dispatch`: Resultado del dispatch externo
    - `sheets_sync`: Resultado de la sincronización a Sheets
  - Logging mejorado para debugging

#### Dependencias
- `requirements.txt`:
  - Actualizado `gspread` de 5.12.3 a 6.0.0
  - Agregado `google-auth-oauthlib==1.2.0`
  - Removido `oauth2client` (deprecado)

#### Configuración de Ejemplo
- `.env.example`:
  - Agregadas todas las nuevas variables de entorno
  - Documentación inline de opciones de configuración
  - Ejemplos de configuración para Google Sheets
  - Ejemplos de configuración para External Dispatch

### Seguridad

- Autenticación con Google Service Account usando mejores prácticas
- Soporte para Secret Manager de GCP en producción
- Validación de firma de webhook (sin cambios)
- Timeout en requests externos para evitar bloqueos
- Logging sin exposición de credenciales

### Rendimiento

- Operaciones de Google Sheets son asíncronas y no bloquean el webhook
- Timeout configurado en 10s para external dispatch
- Manejo de errores que no afecta el flujo principal de guardado en DB

---

## [2.0.0] - 2026-01-05

### Agregado

#### Base de Datos
- Modelo `Lead` con SQLAlchemy
- Repository pattern para acceso a datos
- Soporte para búsqueda fuzzy con pg_trgm
- Índice GIN para búsqueda por similitud de nombres

#### API Endpoints
- `POST /webhooks/clickup`: Recibir webhooks de ClickUp
- `GET /leads/search`: Búsqueda fuzzy de leads por nombre
- `GET /leads/{task_id}`: Obtener lead por ID de tarea
- `GET /leads/mycase/{mycase_id}`: Obtener lead por MyCase ID
- `GET /leads/`: Listar todos los leads con paginación
- `GET /health`: Health check endpoint

#### Core Functionality
- Parser de task_content con regex
- Normalización de nombres para búsqueda
- Validación de teléfonos
- Extracción de MyCase ID desde nombre de tarea
- Transformación de datos de ClickUp a formato DB

#### Servicios
- `ClickUpService`: Interacción con ClickUp API
- `LeadService`: Lógica de negocio para leads
- `LeadRepository`: Acceso a datos con SQLAlchemy

#### Infrastructure
- Dockerfile para containerización
- Cloud Build configuration
- Deploy script para Cloud Run
- Alembic para migraciones de DB
- Script de inicialización de DB

#### Documentación
- README.md completo
- API_EXAMPLES.md con ejemplos de uso
- ARCHITECTURE.md con detalles técnicos
- QUICKSTART.md para inicio rápido
- INDEX.md como índice de documentación

### Configuración

- Pydantic Settings para configuración
- Soporte para .env file
- Variables de entorno para:
  - ClickUp API
  - PostgreSQL/Cloud SQL
  - Google Cloud
  - CORS
  - Logging

### Testing

- Script de carga histórica de datos
- Health check endpoints
- Documentación interactiva con FastAPI/Swagger

---

## [1.0.0] - 2025-12-XX

### Inicial

- Setup inicial del proyecto
- Estructura básica de FastAPI
- Conexión a ClickUp API
- Configuración básica

---

## Tipos de Cambios

- **Agregado**: Para nuevas funcionalidades
- **Modificado**: Para cambios en funcionalidades existentes
- **Deprecado**: Para funcionalidades que serán removidas
- **Removido**: Para funcionalidades removidas
- **Corregido**: Para corrección de bugs
- **Seguridad**: Para cambios relacionados con seguridad

---

## Links

- [Repositorio](https://github.com/tu-org/nexus-legal-integration)
- [Issues](https://github.com/tu-org/nexus-legal-integration/issues)
- [Documentación](./README.md)

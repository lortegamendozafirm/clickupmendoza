# Guía Rápida de Inicio

Esta guía te llevará desde cero hasta tener el servicio corriendo en menos de 10 minutos.

## 🚀 Quick Start Local (Desarrollo)

### 1. Pre-requisitos

```bash
# Verificar Python
python3.11 --version  # Debe ser 3.11+

# Verificar PostgreSQL (debe estar corriendo)
psql --version  # Debe ser 15+
```

### 2. Instalación

```bash
# Clonar/entrar al proyecto
cd clickupmendoza

# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
make install
# O: pip install -r requirements.txt
```

### 3. Configurar Base de Datos

```bash
# Crear base de datos en PostgreSQL
createdb nexus_legal_db

# O con psql:
psql -U postgres -c "CREATE DATABASE nexus_legal_db;"

# Habilitar extensión pg_trgm
psql -U postgres -d nexus_legal_db -c "CREATE EXTENSION pg_trgm;"
```

# Crear base de datos
sudo -u postgres createdb nexus_legal_db

# Habilitar extensión (OJO: esto requiere contraseña en .env después)
sudo -u postgres psql -d nexus_legal_db -c "CREATE EXTENSION pg_trgm;"


### 4. Configurar Variables de Entorno

El archivo `.env` ya está creado. Edita las credenciales:

```bash
nano .env
```

**Mínimo requerido:**
```env
CLICKUP_API_TOKEN=pk_YOUR_TOKEN
CLICKUP_WEBHOOK_SECRET=any_secret_here
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=nexus_legal_db
DATABASE_USER=nexus_user
DATABASE_PASSWORD=nexus_password
```

### 5. Inicializar DB

```bash
make init-db
# O: python scripts/init_db.py
```

Esto crea:
- Tabla `leads_cache`
- Extensión `pg_trgm`
- Índice GIN para búsqueda fuzzy

### 6. Ejecutar Servidor

```bash
make dev
# O: uvicorn app.main:app --reload --port 8080
```

### 7. Probar API

Abrir en el navegador:
- **Docs interactivos:** http://localhost:8080/docs
- **Health check:** http://localhost:8080/

**Probar búsqueda:**
```bash
curl "http://localhost:8080/leads/search?q=Juan"
```

## 📦 Cargar Datos Históricos (CSVs)

Si tienes archivos CSV de ClickUp:

```bash
python scripts/load_historical_data.py /path/to/*.csv
```

Ejemplo:
```bash
python scripts/load_historical_data.py \
    /home/ortega/Descargas/DVS2025.csv \
    /home/ortega/Descargas/DVS2024_1.csv \
    /home/ortega/Descargas/DVS2024_2.csv
```

## 🌐 Deployment a Google Cloud Run

### 1. Pre-requisitos GCP

```bash
# Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Autenticarse
gcloud auth login

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID
```

### 2. Crear Cloud SQL

```bash
# Crear instancia PostgreSQL
gcloud sql instances create nexus-legal-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1

# Crear base de datos
gcloud sql databases create nexus_legal_db \
    --instance=nexus-legal-db

# Crear usuario
gcloud sql users create dbuser \
    --instance=nexus-legal-db \
    --password=SECURE_PASSWORD_HERE

# Obtener connection string
gcloud sql instances describe nexus-legal-db \
    --format="value(connectionName)"
# Resultado: project:region:instance-name
```

### 3. Configurar Secrets

```bash
# CLICKUP_API_TOKEN
echo -n "pk_YOUR_TOKEN" | \
    gcloud secrets create CLICKUP_API_TOKEN --data-file=-

# CLICKUP_WEBHOOK_SECRET
echo -n "your_secret" | \
    gcloud secrets create CLICKUP_WEBHOOK_SECRET --data-file=-

# DATABASE_URL
echo -n "postgresql://dbuser:PASSWORD@/nexus_legal_db?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
    gcloud secrets create DATABASE_URL --data-file=-

# Grant access a Cloud Run
gcloud secrets add-iam-policy-binding CLICKUP_API_TOKEN \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Repetir para otros secrets...
```

### 4. Deploy

**Opción A: Script automatizado**

```bash
# Editar variables en deploy.sh
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Ejecutar
./deploy.sh
```

**Opción B: Manual**

```bash
# Build + deploy en un comando
gcloud run deploy nexus-legal-api \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars APP_ENV=production \
    --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest,DATABASE_URL=DATABASE_URL:latest \
    --add-cloudsql-instances PROJECT:REGION:INSTANCE \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi
```

### 5. Inicializar DB en Cloud SQL

```bash
# Conectarse a Cloud SQL
gcloud sql connect nexus-legal-db --user=dbuser

# Ejecutar SQL:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q

# O ejecutar script de init (requiere Cloud SQL Proxy)
# python scripts/init_db.py
```

### 6. Configurar Webhook en ClickUp

1. Ir a ClickUp → Settings → Integrations → Webhooks
2. Crear nuevo webhook:
   - **URL:** `https://YOUR-CLOUD-RUN-URL/webhooks/clickup`
   - **Events:** `taskUpdated`, `taskCreated`
   - **Secret:** Mismo valor que `CLICKUP_WEBHOOK_SECRET`

### 7. Probar

```bash
# Obtener URL del servicio
gcloud run services describe nexus-legal-api \
    --region us-central1 \
    --format="value(status.url)"

# Probar health check
curl https://YOUR-URL/health

# Probar búsqueda
curl "https://YOUR-URL/leads/search?q=Juan&limit=5"
```

## 📊 Comandos Útiles

```bash
# Ver logs
make logs
# O: gcloud run logs read nexus-legal-api --region us-central1

# Crear migración
make migrate-create MSG="agregar campo X"

# Aplicar migraciones
make migrate-up

# Formatear código
make format

# Limpiar archivos temporales
make clean

# Ver ayuda del Makefile
make help
```

## 🐛 Troubleshooting

### Error: "Extension pg_trgm not found"

```sql
-- Conectarse a la DB y ejecutar:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Error: "Database connection failed"

Verificar:
1. PostgreSQL está corriendo: `pg_isready`
2. Credenciales en `.env` son correctas
3. Base de datos existe: `psql -l`

### Error: "Module not found"

```bash
# Asegurarse de estar en el entorno virtual
source .venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Cloud Run: "Service Unavailable"

```bash
# Ver logs
gcloud run logs read nexus-legal-api --region us-central1 --limit 50

# Verificar secretos
gcloud secrets versions access latest --secret=DATABASE_URL
```

## 📚 Próximos Pasos

1. **Leer el [README.md](README.md)** para entender la arquitectura
2. **Explorar la API:** http://localhost:8080/docs
3. **Cargar datos históricos** con el script ETL
4. **Configurar webhook** de ClickUp
5. **Monitorear logs** en Cloud Run

## 🆘 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.

---

**Versión:** 2.1.0
**Última actualización:** 2026-01-05

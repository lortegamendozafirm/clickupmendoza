# 📚 Índice de Documentación - Nexus Legal Integration

Guía de navegación rápida por toda la documentación del proyecto.

---

## 🚀 Para Empezar

### 1. [PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt)
**Tiempo de lectura: 2 minutos**

Resumen visual de una página con:
- Stack tecnológico
- Estructura del proyecto
- Flujos principales
- Quick start
- Checklist de deployment

**👉 Empieza aquí si:** Quieres una vista general rápida del proyecto.

---

### 2. [QUICKSTART.md](QUICKSTART.md)
**Tiempo de lectura: 5-10 minutos**

Guía paso a paso para:
- Instalación local (< 10 min)
- Configuración de base de datos
- Deployment a Google Cloud Run
- Cargar datos históricos
- Troubleshooting común

**👉 Empieza aquí si:** Quieres tener el servicio corriendo YA.

---

## 📖 Documentación Principal

### 3. [README.md](README.md)
**Tiempo de lectura: 15-20 minutos**

Documentación completa del proyecto:
- Arquitectura overview
- Estructura de archivos
- Instalación detallada
- Deployment paso a paso
- Lógica de parsing y normalización
- Búsqueda fuzzy (pg_trgm)
- Mantenimiento y monitoreo
- Roadmap

**👉 Lee esto si:** Quieres entender TODO el proyecto en detalle.

---

## 🏗️ Arquitectura y Diseño

### 4. [ARCHITECTURE.md](ARCHITECTURE.md)
**Tiempo de lectura: 20-30 minutos**

Documentación técnica profunda:
- Diagrama de arquitectura (ASCII art)
- Capas de la aplicación (API, Services, Core, Repositories, Models)
- Flujos de datos detallados
- Patrones de diseño implementados
- Decisiones técnicas y trade-offs
- Seguridad
- Escalabilidad
- Monitoreo

**👉 Lee esto si:** Eres desarrollador y necesitas entender la arquitectura interna.

---

## 🔌 Uso de la API

### 5. [API_EXAMPLES.md](API_EXAMPLES.md)
**Tiempo de lectura: 10-15 minutos**

Colección de ejemplos prácticos:
- Health check
- Búsqueda fuzzy de leads
- Consulta individual (por task_id, mycase_id)
- Paginación
- Webhooks de ClickUp
- Casos de uso prácticos
- Integración con MCP
- Errores comunes
- Postman collection

**👉 Lee esto si:** Necesitas consumir la API o integrarla con otros sistemas.

---

## 📝 Guías Específicas

### 6. [.env.example](.env.example)
Variables de entorno requeridas con documentación inline.

**👉 Usa esto para:** Configurar tu entorno local o producción.

---

### 7. [Makefile](Makefile)
Comandos comunes de desarrollo:
```bash
make help          # Ver todos los comandos
make dev           # Servidor local
make init-db       # Inicializar DB
make deploy        # Desplegar a Cloud Run
```

**👉 Usa esto para:** Automatizar tareas comunes.

---

### 8. [deploy.sh](deploy.sh)
Script automatizado de deployment a Google Cloud Run.

**👉 Ejecuta esto para:** Desplegar el servicio a producción.

---

## 🗂️ Código Fuente

### Por Capa

#### 📡 API Layer
- [app/main.py](app/main.py) - Aplicación FastAPI principal
- [app/api/webhooks.py](app/api/webhooks.py) - POST /webhooks/clickup
- [app/api/leads.py](app/api/leads.py) - Endpoints de búsqueda

#### 💼 Services Layer
- [app/services/lead_service.py](app/services/lead_service.py) - Transformaciones de leads
- [app/services/clickup_service.py](app/services/clickup_service.py) - Cliente API ClickUp

#### 🧠 Core Layer (Parsing)
- [app/core/parser.py](app/core/parser.py) - Motor de parsing (regex)
- [app/core/normalizer.py](app/core/normalizer.py) - Normalización de nombres
- [app/core/text_utils.py](app/core/text_utils.py) - Utilidades de texto

#### 🗄️ Data Layer
- [app/repositories/lead_repository.py](app/repositories/lead_repository.py) - CRUD + búsqueda fuzzy
- [app/models/lead.py](app/models/lead.py) - Modelo ORM LeadsCache
- [app/database.py](app/database.py) - Configuración SQLAlchemy

#### 📋 Schemas
- [app/schemas/lead.py](app/schemas/lead.py) - Validación de respuestas
- [app/schemas/webhook.py](app/schemas/webhook.py) - Validación de webhooks

#### ⚙️ Config
- [app/config.py](app/config.py) - Pydantic Settings

---

## 🛠️ Scripts Auxiliares

### 9. [scripts/init_db.py](scripts/init_db.py)
Inicialización de base de datos:
- Crea tablas
- Habilita extensión pg_trgm
- Crea índices GIN

**👉 Ejecuta esto:** Después de crear la DB por primera vez.

---

### 10. [scripts/load_historical_data.py](scripts/load_historical_data.py)
ETL para cargar datos históricos desde CSVs:
- Lee múltiples CSVs
- Normaliza columnas
- Parsea task_content
- Upsert masivo en DB

**👉 Ejecuta esto:** Para migrar datos legacy de ClickUp.

---

## 🗃️ Migraciones de Base de Datos

### 11. Alembic
- [alembic.ini](alembic.ini) - Configuración de Alembic
- [alembic/env.py](alembic/env.py) - Environment de migraciones
- [alembic/versions/](alembic/versions/) - Migraciones

**Comandos:**
```bash
alembic revision --autogenerate -m "descripción"
alembic upgrade head
alembic downgrade -1
```

---

## 🐳 Infraestructura

### 12. [Dockerfile](Dockerfile)
Imagen Docker multi-stage para Cloud Run.

### 13. [cloudbuild.yaml](cloudbuild.yaml)
Pipeline CI/CD de Google Cloud Build.

### 14. [.dockerignore](.dockerignore)
Archivos excluidos del build de Docker.

---

## 📊 Estadísticas del Proyecto

```
Archivos Python:         23 archivos
Líneas de código:        ~1,300 líneas
Archivos de config:      7 archivos
Documentación:           5 archivos markdown
Scripts:                 2 scripts
Total de archivos:       ~40 archivos
```

---

## 🎯 Flujo de Lectura Recomendado

### Para Desarrolladores Nuevos:
1. [PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt) - Vista general (2 min)
2. [QUICKSTART.md](QUICKSTART.md) - Ejecutar localmente (10 min)
3. [README.md](README.md) - Entender el proyecto (20 min)
4. [ARCHITECTURE.md](ARCHITECTURE.md) - Diseño técnico (30 min)
5. Explorar código fuente por capas

### Para Usuarios de la API:
1. [QUICKSTART.md](QUICKSTART.md) - Setup rápido
2. [API_EXAMPLES.md](API_EXAMPLES.md) - Ejemplos de uso
3. http://localhost:8080/docs - Swagger UI interactivo

### Para DevOps/SRE:
1. [QUICKSTART.md](QUICKSTART.md) - Deployment GCP
2. [deploy.sh](deploy.sh) - Script de deployment
3. [cloudbuild.yaml](cloudbuild.yaml) - Pipeline CI/CD
4. [ARCHITECTURE.md](ARCHITECTURE.md) - Seguridad y escalabilidad

---

## 🔍 Búsqueda Rápida

### ¿Cómo hacer X?

| Tarea | Dónde buscar |
|-------|--------------|
| Instalar localmente | [QUICKSTART.md](QUICKSTART.md) → Local |
| Desplegar a Cloud Run | [QUICKSTART.md](QUICKSTART.md) → Cloud Run |
| Configurar webhook | [QUICKSTART.md](QUICKSTART.md) → Step 6 |
| Usar la API | [API_EXAMPLES.md](API_EXAMPLES.md) |
| Entender parsing | [ARCHITECTURE.md](ARCHITECTURE.md) → Core Layer |
| Cargar CSVs | [scripts/load_historical_data.py](scripts/load_historical_data.py) |
| Crear migración DB | [README.md](README.md) → Mantenimiento |
| Ver logs | [README.md](README.md) → Monitoreo |

---

## 💡 Tips de Navegación

### VS Code
Instalar extensión "Markdown All in One" para:
- Navegación por TOC
- Preview lado a lado
- Links clickeables

### Terminal
```bash
# Ver documentación específica
cat QUICKSTART.md | less

# Buscar en toda la documentación
grep -r "pg_trgm" *.md

# Abrir documentación en navegador
python -m markdown README.md > README.html && open README.html
```

---

## 🆘 ¿Perdido?

Si no encuentras lo que buscas:

1. **Busca en este índice** usando Ctrl+F
2. **Revisa [PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt)** para orientarte
3. **Consulta [README.md](README.md)** - probablemente esté ahí
4. **Explora el código** - está bien documentado con docstrings
5. **Contacta al equipo** de desarrollo

---

**Última actualización:** 2026-01-05
**Versión:** 2.1.0

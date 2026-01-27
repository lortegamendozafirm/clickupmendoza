# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import webhooks, leads, callbacks, webhook_assignments

# ============================================================================
# Lifespan Event Handler (Reemplaza a on_event)
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Código que se ejecuta al iniciar
    print("🚀 Nexus Legal Integration API iniciada")
    print(f"📍 Entorno: {settings.app_env}")
    print(f"🗄️  Base de datos: {settings.database_host}")
    
    yield # Aquí es donde la aplicación corre
    
    # Shutdown: Código que se ejecuta al detener
    print("👋 Nexus Legal Integration API detenida")

# ============================================================================
# Crear aplicación FastAPI
# ============================================================================
app = FastAPI(
    title="Nexus Legal Integration API",
    description="Middleware de integración ClickUp → Cloud SQL + API (MCP/Search)",
    version="2.2.1", # Incrementamos versión por la nueva lista
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan # Registramos el lifespan aquí
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Routes
# ============================================================================
# Lista original: CONSULTAS AGENDA
app.include_router(webhooks.router) 
app.include_router(leads.router)

# Nueva lista: CASE ASSIGNMENT
app.include_router(webhook_assignments.router)

# Callbacks e IA
app.include_router(callbacks.router, prefix="/callbacks", tags=["Callbacks"])

# ============================================================================
# Health Check
# ============================================================================
@app.get("/", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Nexus Legal Integration",
        "version": "2.2.1",
        "environment": settings.app_env
    }

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
# app/main.py
"""
FastAPI Application - Nexus Legal Integration
Punto de entrada principal de la aplicación.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import webhooks, leads, callbacks

# Crear aplicación FastAPI
app = FastAPI(
    title="Nexus Legal Integration API",
    description="Middleware de integración ClickUp → Cloud SQL + API (MCP/Search)",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS Configuration
# ============================================================================
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
app.include_router(webhooks.router)
app.include_router(leads.router)
app.include_router(callbacks.router, prefix="/callbacks", tags=["Callbacks"])

# ============================================================================
# Health Check
# ============================================================================
@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Nexus Legal Integration",
        "version": "2.1.0",
        "environment": settings.app_env
    }


@app.get("/health", tags=["health"])
def health():
    """Health check for Cloud Run"""
    return {"status": "ok"}


# ============================================================================
# Startup/Shutdown Events
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Ejecutado al iniciar la aplicación"""
    print("🚀 Nexus Legal Integration API iniciada")
    print(f"📍 Entorno: {settings.app_env}")
    print(f"🗄️  Base de datos: {settings.database_host}")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecutado al detener la aplicación"""
    print("👋 Nexus Legal Integration API detenida")

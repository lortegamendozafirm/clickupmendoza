#!/usr/bin/env python3
"""
Script de inicialización de base de datos.

Ejecuta:
1. Creación de tablas (Base.metadata.create_all)
2. Habilita extensión pg_trgm (para búsqueda fuzzy)
3. Crea índice GIN en nombre_normalizado

Uso:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models import Base


def init_database():
    """Inicializa la base de datos con tablas e índices"""

    print("🗄️  Inicializando base de datos...")
    print(f"📍 Host: {settings.database_host}")
    print(f"📍 Database: {settings.database_name}")
    print()

    # Crear engine
    engine = create_engine(settings.database_dsn)

    # 1. Crear extensión pg_trgm (requerida para búsqueda fuzzy)
    print("[1/3] Habilitando extensión pg_trgm...")
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.commit()
            print("✅ Extensión pg_trgm habilitada")
        except Exception as e:
            print(f"⚠️  Error habilitando pg_trgm: {e}")
            print("    (Puede que ya esté habilitada o que no tengas permisos)")

    # 2. Crear todas las tablas
    print("\n[2/3] Creando tablas...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        sys.exit(1)

    # 3. Crear índice GIN para búsqueda trigram
    print("\n[3/3] Creando índice GIN para búsqueda fuzzy...")
    with engine.connect() as conn:
        try:
            # Verificar si el índice ya existe
            result = conn.execute(text("""
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'idx_nombre_normalizado_gin';
            """))

            if result.fetchone():
                print("ℹ️  Índice GIN ya existe, omitiendo...")
            else:
                # Crear índice GIN con operador pg_trgm
                conn.execute(text("""
                    CREATE INDEX idx_nombre_normalizado_gin
                    ON leads_cache
                    USING gin (nombre_normalizado gin_trgm_ops);
                """))
                conn.commit()
                print("✅ Índice GIN creado exitosamente")

        except Exception as e:
            print(f"❌ Error creando índice GIN: {e}")
            print("    La búsqueda fuzzy podría ser lenta sin este índice")

    print("\n🎉 Base de datos inicializada correctamente!")
    print("\nPróximos pasos:")
    print("1. Usar Alembic para migraciones futuras: alembic revision --autogenerate -m 'descripción'")
    print("2. Aplicar migraciones: alembic upgrade head")
    print("3. Iniciar la aplicación: uvicorn app.main:app --reload")


if __name__ == "__main__":
    init_database()

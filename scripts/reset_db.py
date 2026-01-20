# reset_db.py
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.database_dsn)
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS leads_cache;"))
    conn.commit()
    print("🗑️ Tabla leads_cache eliminada.")
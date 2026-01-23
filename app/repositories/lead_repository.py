"""
Repository para operaciones CRUD sobre leads_cache.
Incluye búsqueda fuzzy con pg_trgm.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime, timezone  # Importamos timezone para evitar el warning

from app.models.lead import LeadsCache
from app.core.text_utils import normalize_name


class LeadRepository:
    """
    Repository para la tabla leads_cache.
    Encapsula todas las operaciones de acceso a datos.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_task_id(self, task_id: str) -> Optional[LeadsCache]:
        """Obtiene un lead por task_id"""
        return self.db.query(LeadsCache).filter(LeadsCache.task_id == task_id).first()

    def get_by_mycase_id(self, mycase_id: str) -> Optional[LeadsCache]:
        """Obtiene un lead por id_mycase"""
        return self.db.query(LeadsCache).filter(LeadsCache.id_mycase == mycase_id).first()

    
    def upsert(self, data: dict) -> LeadsCache:
        """
        Inserta o actualiza un registro manejando concurrencia.
        Usa session.merge() y try/except para evitar choques.
        """
        task_id = data.get("task_id")
        if not task_id:
            raise ValueError("Task ID is required for upsert")

        # 1. Limpieza de seguridad (mycase_id vs id_mycase)
        if "mycase_id" in data:
            # Si no trae id_mycase explícito, usamos el que viene como mycase_id
            if not data.get("id_mycase"):
                data["id_mycase"] = data.pop("mycase_id")
            else:
                # Si ya tiene id_mycase, solo borramos la clave basura
                data.pop("mycase_id")

        # 2. Manejo de fecha UTC (Tu corrección estaba bien, la mantenemos)
        if "synced_at" not in data:
            data["synced_at"] = datetime.now(timezone.utc)

        try:
            # Creamos una instancia temporal con los datos
            lead_instance = LeadsCache(**data)
            
            # MERGE: SQLAlchemy se encarga de ver si está en sesión o DB.
            # Si existe PK, actualiza. Si no, prepara insert.
            merged_lead = self.db.merge(lead_instance)
            
            # Intentamos guardar
            self.db.commit()
            
            # Refrescamos para tener los datos finales (IDs, fechas autogeneradas)
            # Ojo: refresh sobre 'merged_lead', no sobre 'lead_instance'
            return merged_lead

        except Exception as e:
            self.db.rollback()
            # Si falló (probablemente por carrera), intentamos recuperarnos suavemente
            # devolviendo lo que ya existe en la DB sin explotar.
            print(f"⚠️ Aviso en upsert (Recuperado de Race Condition): {e}")
            
            existing = self.get_by_task_id(task_id)
            if existing:
                return existing
            
            # Si falló y no existe... entonces es un error real, lo relanzamos.
            raise e

    def search_by_name(self, query: str, limit: int = 10) -> List[LeadsCache]:
        """
        Búsqueda fuzzy por nombre usando pg_trgm similarity.
        """
        normalized_query = normalize_name(query)

        if not normalized_query:
            return []

        results = (
            self.db.query(LeadsCache)
            .filter(text("nombre_normalizado % :query"))
            .params(query=normalized_query)
            .order_by(text("similarity(nombre_normalizado, :query) DESC"))
            .limit(limit)
            .all()
        )

        return results

    def get_recent_updates(self, since: datetime, limit: int = 100) -> List[LeadsCache]:
        """
        Obtiene leads actualizados después de una fecha.
        """
        return (
            self.db.query(LeadsCache)
            .filter(LeadsCache.date_updated > since)
            .order_by(LeadsCache.date_updated.desc())
            .limit(limit)
            .all()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[LeadsCache]:
        """
        Obtiene todos los leads con paginación.
        """
        return (
            self.db.query(LeadsCache)
            .order_by(LeadsCache.date_updated.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        """Cuenta total de registros"""
        return self.db.query(func.count(LeadsCache.task_id)).scalar()
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
        Inserta o actualiza un registro (UPSERT).

        Args:
            data: Diccionario con los campos del lead

        Returns:
            Lead insertado/actualizado
        """
        task_id = data.get("task_id")
        if not task_id:
            raise ValueError("task_id es requerido para upsert")

        # 1. Definimos la hora actual UTC una sola vez (Python 3.11 way)
        # datetime.utcnow() está deprecado, usamos datetime.now(timezone.utc)
        current_time = datetime.now(timezone.utc)

        # Buscar si existe
        existing = self.get_by_task_id(task_id)

        if existing:
            # UPDATE
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            # Corrección: Asignamos el valor directo, NO una lambda
            existing.synced_at = current_time
            lead = existing
        else:
            # INSERT
            # Corrección: Asignamos el valor directo al diccionario antes de crear el objeto
            data["synced_at"] = current_time
            lead = LeadsCache(**data)
            self.db.add(lead)

        self.db.commit()
        self.db.refresh(lead)
        return lead

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
"""
Repository para operaciones CRUD sobre leads_cache.
Incluye búsqueda fuzzy con pg_trgm.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime

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

        # Buscar si existe
        existing = self.get_by_task_id(task_id)

        if existing:
            # UPDATE
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.synced_at = datetime.utcnow()
            lead = existing
        else:
            # INSERT
            data["synced_at"] = datetime.utcnow()
            lead = LeadsCache(**data)
            self.db.add(lead)

        self.db.commit()
        self.db.refresh(lead)
        return lead

    def search_by_name(self, query: str, limit: int = 10) -> List[LeadsCache]:
        """
        Búsqueda fuzzy por nombre usando pg_trgm similarity.

        Usa el operador % (similarity) y la función similarity() de pg_trgm.
        Requiere que la extensión pg_trgm esté habilitada y el índice GIN creado.

        Args:
            query: Texto a buscar
            limit: Número máximo de resultados

        Returns:
            Lista de leads ordenados por similitud (mayor a menor)
        """
        # Normalizar query con la misma función que usamos para los datos
        normalized_query = normalize_name(query)

        if not normalized_query:
            return []

        # Consulta con pg_trgm similarity
        # % es el operador de similitud (requiere threshold, default 0.3)
        # similarity() devuelve el score (0.0 a 1.0)
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
        Útil para sync incremental.

        Args:
            since: Fecha de corte (date_updated > since)
            limit: Máximo de registros

        Returns:
            Lista de leads actualizados recientemente
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

        Args:
            skip: Offset
            limit: Límite de registros

        Returns:
            Lista de leads
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

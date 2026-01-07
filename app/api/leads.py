"""
Endpoints para búsqueda y consulta de leads
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadResponse, LeadSearchResponse

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/search", response_model=LeadSearchResponse)
def search_leads(
    q: str = Query(..., min_length=2, description="Nombre a buscar (mínimo 2 caracteres)"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    db: Session = Depends(get_db)
):
    """
    Búsqueda fuzzy de leads por nombre.

    Usa pg_trgm similarity para búsqueda tolerante a errores.

    Query parameters:
    - q: Texto a buscar (mínimo 2 caracteres)
    - limit: Máximo de resultados (default 10, max 50)

    Returns:
    - total: Número de resultados encontrados
    - results: Lista de leads ordenados por similitud
    """
    repo = LeadRepository(db)
    results = repo.search_by_name(q, limit=limit)

    return {
        "total": len(results),
        "results": results
    }


@router.get("/{task_id}", response_model=LeadResponse)
def get_lead(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un lead por task_id.

    Path parameters:
    - task_id: ID de la tarea de ClickUp

    Returns:
    - Lead completo

    Raises:
    - 404 si no existe
    """
    repo = LeadRepository(db)
    lead = repo.get_by_task_id(task_id)

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {task_id} not found")

    return lead


@router.get("/mycase/{mycase_id}", response_model=LeadResponse)
def get_lead_by_mycase(
    mycase_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un lead por MyCase ID.

    Path parameters:
    - mycase_id: ID de MyCase (8 dígitos)

    Returns:
    - Lead completo

    Raises:
    - 404 si no existe
    """
    repo = LeadRepository(db)
    lead = repo.get_by_mycase_id(mycase_id)

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with MyCase ID {mycase_id} not found")

    return lead


@router.get("/", response_model=List[LeadResponse])
def list_leads(
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los leads con paginación.

    Query parameters:
    - skip: Offset (default 0)
    - limit: Límite de registros (default 100, max 500)

    Returns:
    - Lista de leads ordenados por fecha de actualización (más recientes primero)
    """
    repo = LeadRepository(db)
    leads = repo.get_all(skip=skip, limit=limit)

    return leads

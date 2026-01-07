"""
Schemas Pydantic para respuestas de API
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeadResponse(BaseModel):
    """Schema de respuesta para un lead individual"""

    task_id: str
    task_name: Optional[str] = None
    nombre_clickup: Optional[str] = None
    nombre_normalizado: Optional[str] = None

    status: Optional[str] = None
    assignee: Optional[str] = None

    full_name_extracted: Optional[str] = None
    phone_number: Optional[str] = None
    email_extracted: Optional[str] = None
    location: Optional[str] = None

    id_mycase: Optional[str] = None
    mycase_link: Optional[str] = None

    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None

    interview_type: Optional[str] = None
    interview_result: Optional[str] = None

    synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Permite crear desde ORM objects


class LeadSearchResponse(BaseModel):
    """Schema de respuesta para búsqueda"""

    total: int
    results: list[LeadResponse]

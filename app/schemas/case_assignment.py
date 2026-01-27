# app/schemas/case_assignment.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Esquema para lo que recibimos de ClickUp (Webhook)
class CaseAssignmentWebhook(BaseModel):
    task_id: str
    event: str
    webhook_id: str
    # Puedes agregar más campos si necesitas validar la firma aquí

# Esquema Base para tu Base de Datos (Dominio)
class CaseAssignmentBase(BaseModel):
    task_id: str
    id_cliente: Optional[str] = None
    task_name: Optional[str] = None
    status: Optional[str] = None
    abogado_asignado: Optional[str] = None
    # ... puedes agregar el resto de campos del conjunto C aquí

class CaseAssignmentCreate(CaseAssignmentBase):
    pass

# Esquema para las respuestas de tu API (Output)
class CaseAssignmentResponse(CaseAssignmentBase):
    synced_at: datetime
    
    class Config:
        from_attributes = True # Permite leer objetos de SQLAlchemy directamente
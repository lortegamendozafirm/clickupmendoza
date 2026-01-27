# app/api/webhook_assignments.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.assignment_service import AssignmentService
from app.services.clickup_service import ClickUpService
from app.repositories.assignment_repository import AssignmentRepository
from app.schemas.case_assignment import CaseAssignmentWebhook, CaseAssignmentResponse

router = APIRouter(prefix="/webhooks", tags=["assignments"])

@router.post("/assignments", response_model=None)
async def handle_assignment_webhook(
    request: Request,
    payload: CaseAssignmentWebhook,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Webhook para la lista Case Assignment.
    Valida la entrada, consulta ClickUp API y sincroniza la DB local.
    """
    # 1. Validar la firma antes de cualquier otra cosa
    body = await request.body()
    body_text = body.decode("utf-8")
    
    clickup_service = ClickUpService()

    is_valid = clickup_service.verify_webhook_signature(
        body_text, 
        x_signature or "", 
        secret=settings.clickup_webhook_secret_assignments
    )
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # 2. Si la firma es válida, procedemos con la lógica
    task_id = payload.task_id
    task_data = await clickup_service.get_task(task_id)
    
    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found in ClickUp")

    # 2. Transformar los datos usando el Service (Lógica de Negocio)
    # El Service se encarga de aplicar el MAPEO_IDS y formar el JSONB
    formatted_data = AssignmentService.transform_task(task_data)

    # 3. Guardar en DB (Repositorio)
    repo = AssignmentRepository(db)
    repo.upsert(formatted_data)

    return {"status": "success", "task_id": task_id, "event": payload.event}
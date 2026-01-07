"""
Endpoints para webhooks de ClickUp
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import logging

from app.database import get_db
from app.services.clickup_service import ClickUpService
from app.services.lead_service import LeadService
from app.services.sheets_service import GoogleSheetsService
from app.repositories.lead_repository import LeadRepository
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/clickup")
async def clickup_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Webhook de ClickUp para eventos de tareas.

    ClickUp enviará POST cuando ocurra un evento (taskUpdated, etc.)

    Security:
    - Valida firma (x-signature header) contra CLICKUP_WEBHOOK_SECRET

    Flow:
    1. Validar firma
    2. Parsear payload
    3. Filtrar por lista específica (CLICKUP_LIST_ID)
    4. Obtener task completa de ClickUp API (el webhook solo trae cambios)
    5. Verificar condición: campo "Link Intake" tiene valor o cambió
    6. Si condición se cumple:
       - Enviar payload a URL externa (external dispatch)
       - Escribir fila en Google Sheets
    7. Transformar + normalizar
    8. Upsert en DB
    """
    # Leer body raw para validación de firma
    body = await request.body()
    body_text = body.decode("utf-8")

    # Validar firma (seguridad)
    clickup_service = ClickUpService()
    if not clickup_service.verify_webhook_signature(body_text, x_signature or ""):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parsear payload JSON
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    event = payload.get("event")
    task_id = payload.get("task_id")

    if not task_id:
        raise HTTPException(status_code=400, detail="Missing task_id in webhook payload")

    # Solo procesar eventos de actualización/creación
    if event not in ["taskUpdated", "taskCreated"]:
        return {"status": "ignored", "event": event}

    # Obtener tarea completa de ClickUp API
    # (el webhook solo trae cambios incrementales, necesitamos todo)
    task_data = await clickup_service.get_task(task_id)

    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found in ClickUp")

    # FILTRO: Solo procesar tareas de la lista específica
    task_list_id = task_data.get("list", {}).get("id")
    if settings.clickup_list_id and task_list_id != settings.clickup_list_id:
        logger.info(f"Task {task_id} is from list {task_list_id}, not {settings.clickup_list_id}. Ignoring.")
        return {
            "status": "ignored",
            "reason": "not_in_target_list",
            "task_list_id": task_list_id
        }

    # TRIGGER CONDICIONAL: Verificar si el campo "Link Intake" tiene valor
    link_intake_value = None
    custom_fields = task_data.get("custom_fields", [])

    for field in custom_fields:
        if field.get("name") == "Link Intake":
            link_intake_value = field.get("value")
            break

    # Si el campo "Link Intake" tiene valor, disparar acciones
    trigger_actions = False
    if link_intake_value:
        trigger_actions = True
        logger.info(f"Task {task_id}: 'Link Intake' field has value '{link_intake_value}'. Triggering actions.")

    # ACCIÓN 1: External Dispatch (HTTP POST)
    external_dispatch_success = False
    if trigger_actions and settings.external_dispatch_enabled and settings.external_dispatch_url:
        external_dispatch_success = await _dispatch_to_external_service(task_id, task_data, link_intake_value)

    # ACCIÓN 2: Google Sheets Sync
    sheets_sync_success = False
    if trigger_actions and settings.google_sheets_enabled:
        sheets_sync_success = await _sync_to_google_sheets(task_data)

    # Transformar a formato de DB
    lead_data = LeadService.transform_clickup_task(task_data)

    # Upsert en DB
    repo = LeadRepository(db)
    lead = repo.upsert(lead_data)

    return {
        "status": "success",
        "event": event,
        "task_id": task_id,
        "list_id": task_list_id,
        "trigger_actions": trigger_actions,
        "link_intake_value": link_intake_value,
        "external_dispatch": external_dispatch_success,
        "sheets_sync": sheets_sync_success,
        "synced_at": lead.synced_at.isoformat()
    }


async def _dispatch_to_external_service(task_id: str, task_data: dict, link_intake_value: str) -> bool:
    """
    Envía un payload JSON genérico a una URL externa vía HTTP POST.

    Args:
        task_id: ID de la tarea de ClickUp
        task_data: Datos completos de la tarea
        link_intake_value: Valor del campo "Link Intake"

    Returns:
        True si el dispatch fue exitoso, False en caso contrario
    """
    try:
        # Construir payload básico
        payload = {
            "task_id": task_id,
            "task_name": task_data.get("name"),
            "link_intake": link_intake_value,
            "status": task_data.get("status", {}).get("status"),
            "list_id": task_data.get("list", {}).get("id"),
            "url": task_data.get("url"),
            "date_created": task_data.get("date_created"),
            "date_updated": task_data.get("date_updated"),
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.external_dispatch_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.info(f"Successfully dispatched task {task_id} to external service: {response.status_code}")
        return True

    except httpx.HTTPError as e:
        logger.error(f"HTTP error dispatching task {task_id} to external service: {e}")
        return False
    except Exception as e:
        logger.error(f"Error dispatching task {task_id} to external service: {e}")
        return False


async def _sync_to_google_sheets(task_data: dict) -> bool:
    """
    Escribe una fila en Google Sheets con los datos de la tarea.

    Args:
        task_data: Datos completos de la tarea de ClickUp

    Returns:
        True si la escritura fue exitosa, False en caso contrario
    """
    try:
        sheets_service = GoogleSheetsService()

        # Extraer campos relevantes de la tarea
        # Estos campos se mapearán según el field_mapping configurado en .env
        data = {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "status": task_data.get("status", {}).get("status"),
            "url": task_data.get("url"),
            "date_created": task_data.get("date_created"),
            "date_updated": task_data.get("date_updated"),
        }

        # Agregar custom fields al diccionario
        for field in task_data.get("custom_fields", []):
            field_name = field.get("name", "").lower().replace(" ", "_")
            field_value = field.get("value")
            if field_value:
                data[field_name] = field_value

        # Escribir fila usando el mapeo configurado
        success = sheets_service.write_row(data)

        if success:
            logger.info(f"Successfully synced task {task_data.get('id')} to Google Sheets")
        else:
            logger.warning(f"Failed to sync task {task_data.get('id')} to Google Sheets")

        return success

    except Exception as e:
        logger.error(f"Error syncing task to Google Sheets: {e}")
        return False

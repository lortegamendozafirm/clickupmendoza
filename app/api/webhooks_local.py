"""
Endpoints para webhooks de ClickUp - OPTIMIZADO CON BACKGROUND TASKS
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import logging
import json # Importante para los logs del JSON

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Webhook optimizado: Responde rápido y procesa en segundo plano.
    """
    # 1. Validación de Firma y Payload (Rápido)
    body = await request.body()
    body_text = body.decode("utf-8")

    clickup_service = ClickUpService()
    if not clickup_service.verify_webhook_signature(body_text, x_signature or ""):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    event = payload.get("event")
    task_id = payload.get("task_id")

    if not task_id:
        raise HTTPException(status_code=400, detail="Missing task_id")

    # Solo procesar updates/creates
    if event not in ["taskUpdated", "taskCreated"]:
        return {"status": "ignored", "event": event}

    # 2. Obtener datos básicos de la tarea (Esto es rápido)
    task_data = await clickup_service.get_task(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Filtro de lista
    task_list_id = task_data.get("list", {}).get("id")
    if settings.clickup_list_id and task_list_id != settings.clickup_list_id:
        return {"status": "ignored", "reason": "wrong_list"}

    # 3. Lógica del Trigger
    link_intake_value = None
    custom_fields = task_data.get("custom_fields", [])

    for field in custom_fields:
        if field.get("name") == settings.clickup_trigger_condicional:
            link_intake_value = field.get("value")
            break

    # --- PROTECCIÓN CONTRA BUCLES ---
    # Verificar si el campo "Link AI Filtro" (el resultado) YA tiene valor.
    # Si ya tiene valor, no volvemos a procesar para evitar bucles infinitos.
    ai_link_exists = False
    for field in custom_fields:
        if field.get("id") == settings.clickup_field_id_ai_link: # Usamos el ID del config
            if field.get("value"): 
                ai_link_exists = True
                break
    
    if ai_link_exists:
         logger.info(f"Task {task_id} ya tiene Link AI generado. Ignorando para evitar bucle.")
         return {"status": "ignored", "reason": "already_processed"}

    # 4. Encolar tareas en Background (Fire and Forget)
    if link_intake_value:
        logger.info(f"⚡ Encolando procesamiento background para Task {task_id}")
        
        # Encolamos el Dispatch a Filtros
        if settings.external_dispatch_enabled and settings.external_dispatch_url:
            background_tasks.add_task(
                _dispatch_to_external_service, 
                task_id, 
                task_data, 
                link_intake_value
            )
        
        # Encolamos Sheets Sync
        if settings.google_sheets_enabled:
            background_tasks.add_task(
                _sync_to_google_sheets, 
                task_data
            )

    # 5. Guardar en DB Local (Rápido)
    lead_data = LeadService.transform_clickup_task(task_data)
    repo = LeadRepository(db)
    lead = repo.upsert(lead_data)

    # RESPONDER A CLICKUP INMEDIATAMENTE
    return {"status": "queued", "task_id": task_id}


async def _dispatch_to_external_service(task_id: str, task_data: dict, link_intake_value: str) -> bool:
    """
    Envía a Filtros con LOGS DETALLADOS.
    Esta función ahora corre en background, así que puede tardar lo que quiera.
    """
    logger.info(f"🚀 [Background] Iniciando Dispatch a Filtros para Task {task_id}")
    
    try:
        # Construir URL de Callback
        # Asegúrate que settings.external_dispatch_callback_base_url NO tenga slash al final
        base_url = settings.external_dispatch_callback_base_url.rstrip("/")
        callback_url = f"{base_url}/callbacks/filtros"
        
        # Construir payload
        payload = {
            "task_id": task_id,
            "client_name": task_data.get("name"),
            "intake_url": link_intake_value,
            "nexus_callback_url": callback_url,
            "metadata": {
                "clickup_status": task_data.get("status", {}).get("status"),
                "clickup_url": task_data.get("url")
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": settings.filtros_api_key
        }

        # --- LOG DEL PAYLOAD ---
        logger.info(f"📦 [Background] PAYLOAD A ENVIAR A {settings.external_dispatch_url}:\n{json.dumps(payload, indent=2)}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                settings.external_dispatch_url,
                json=payload,
                headers=headers
            )
            
            logger.info(f"📨 [Background] Filtros respondió: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"❌ Error Body: {response.text}")
                
            response.raise_for_status()

        logger.info(f"✅ [Background] Dispatch exitoso para {task_id}")
        return True

    except Exception as e:
        logger.error(f"❌ [Background] Error en dispatch: {e}")
        return False


async def _sync_to_google_sheets(task_data: dict) -> bool:
    """
    Sincronización a Sheets (Ahora en background)
    """
    try:
        sheets_service = GoogleSheetsService()
        
        data = {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "status": task_data.get("status", {}).get("status"),
            "url": task_data.get("url"),
            "date_created": task_data.get("date_created"),
            "date_updated": task_data.get("date_updated"),
        }

        for field in task_data.get("custom_fields", []):
            field_name = field.get("name", "").lower().replace(" ", "_")
            field_value = field.get("value")
            if field_value:
                data[field_name] = field_value
                
        logger.info(f"📝 [Background] Escribiendo en Sheets para {task_data.get('id')}")
        success = sheets_service.write_row(data)
        return success

    except Exception as e:
        logger.error(f"Error syncing task to Google Sheets: {e}")
        return False
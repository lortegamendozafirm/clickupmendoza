# app/api/callbacks.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.filtros import FiltrosCallbackPayload
from app.services.clickup_service import ClickUpService
from app.config import settings

router = APIRouter()

@router.post("/filtros", status_code=status.HTTP_200_OK)
async def handle_filtros_callback(payload: FiltrosCallbackPayload):
    """
    Recibe el resultado del análisis de Filtros AI y actualiza ClickUp.
    """
    print(f"📥 Callback recibido para Task {payload.task_id} - Status: {payload.status}")

    # 1. Validar que el proceso fue exitoso
    if payload.status != "success":
        print(f"⚠️ El proceso en Filtros falló: {payload.error}")
        # Retornamos 200 para que Filtros sepa que recibimos el mensaje, 
        # aunque no actualicemos ClickUp (o podrías actualizar un campo de error).
        return {"received": True, "action": "ignored_due_to_error"}

    if not payload.artifacts or not payload.artifacts.doc_url:
        print("⚠️ Payload incompleto: No hay URL del documento")
        return {"received": True, "action": "ignored_no_url"}

    # 2. Inicializar servicio
    clickup_service = ClickUpService()
    
    # 3. Actualizar ClickUp
    # Usamos el ID del campo configurado en settings
    success = await clickup_service.set_custom_field_value(
        task_id=payload.task_id,
        field_id=settings.clickup_field_id_ai_link,
        value=payload.artifacts.doc_url
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error actualizando ClickUp"
        )

    print(f"✅ ClickUp actualizado correctamente: Task {payload.task_id} -> {payload.artifacts.doc_url}")
    return {"received": True, "action": "clickup_updated"}
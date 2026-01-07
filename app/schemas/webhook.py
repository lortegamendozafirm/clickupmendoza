"""
Schemas para webhooks de ClickUp
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class WebhookPayload(BaseModel):
    """
    Payload de webhook de ClickUp.
    Estructura simplificada (ClickUp envía muchos campos).
    """

    event: str  # "taskUpdated", "taskCreated", etc.
    task_id: str
    webhook_id: Optional[str] = None
    history_items: Optional[list] = None

    # El resto del payload (task data completo)
    # Lo capturamos como dict genérico
    class Config:
        extra = "allow"  # Permitir campos adicionales

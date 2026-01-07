"""
Servicio para interactuar con la API de ClickUp.
Obtiene tareas, comentarios, etc.
"""
import hmac
import hashlib
import httpx
from typing import Optional, Dict, List
from datetime import datetime
from app.config import settings


class ClickUpService:
    """Cliente para la API de ClickUp"""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self):
        self.api_token = settings.clickup_api_token
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Obtiene una tarea de ClickUp por ID.

        Args:
            task_id: ID de la tarea

        Returns:
            Diccionario con los datos de la tarea o None si error
        """
        url = f"{self.BASE_URL}/task/{task_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error obteniendo tarea {task_id}: {e}")
                return None

    async def get_tasks_updated_since(
        self, list_id: str, date_updated_gt: datetime, limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene tareas actualizadas después de una fecha (safety net job).

        Args:
            list_id: ID de la lista de ClickUp
            date_updated_gt: Fecha de corte (timestamp Unix en ms)
            limit: Máximo de tareas

        Returns:
            Lista de tareas
        """
        url = f"{self.BASE_URL}/list/{list_id}/task"

        # Convertir datetime a Unix timestamp en milisegundos
        timestamp_ms = int(date_updated_gt.timestamp() * 1000)

        params = {
            "date_updated_gt": timestamp_ms,
            "include_closed": True,
            "page": 0
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                tasks = data.get("tasks", [])
                return tasks[:limit]
            except httpx.HTTPError as e:
                print(f"Error obteniendo tareas actualizadas: {e}")
                return []

    async def get_task_comments(self, task_id: str) -> List[Dict]:
        """
        Obtiene comentarios de una tarea.

        Args:
            task_id: ID de la tarea

        Returns:
            Lista de comentarios
        """
        url = f"{self.BASE_URL}/task/{task_id}/comment"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return data.get("comments", [])
            except httpx.HTTPError as e:
                print(f"Error obteniendo comentarios de {task_id}: {e}")
                return []

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verifica la firma HMAC-SHA256 del webhook de ClickUp.
        """
        if not signature or not settings.clickup_webhook_secret:
            return False

        try:
            # 1. Convertir el secreto y el payload a bytes
            secret_bytes = settings.clickup_webhook_secret.encode('utf-8')
            payload_bytes = payload.encode('utf-8')

            # 2. Calcular el hash esperado usando HMAC-SHA256
            expected_hash = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()

            # 3. Comparar de forma segura (previene ataques de tiempo)
            return hmac.compare_digest(signature, expected_hash)
            
        except Exception as e:
            print(f"❌ Error validando firma: {e}")
            return False

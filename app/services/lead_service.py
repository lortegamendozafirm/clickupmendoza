"""
Servicio de lógica de negocio para Leads.
Orquesta parsing, normalización y almacenamiento.
"""

from typing import Dict, Optional
from datetime import datetime
from dateutil import parser as date_parser

from app.core.parser import parse_task_content
from app.core.normalizer import normalize_task_name
from app.core.text_utils import remove_ordinal_suffix


class LeadService:
    """
    Servicio que transforma datos de ClickUp en un lead estructurado.
    Combina parsing, normalización y preparación de datos.
    """

    @staticmethod
    def transform_clickup_task(task_data: Dict) -> Dict:
        """
        Transforma un objeto de tarea de ClickUp en un diccionario
        listo para insertar en leads_cache.
        """
        result = {}

        # ====================================================================
        # IDENTIFICADORES
        # ====================================================================
        result["task_id"] = task_data.get("id")
        result["task_name"] = task_data.get("name", "")

        # Normalizar task_name -> nombre_clickup, id_mycase, nombre_normalizado
        nombre_clickup, id_mycase_from_name, nombre_normalizado = normalize_task_name(
            result["task_name"]
        )
        result["nombre_clickup"] = nombre_clickup
        result["nombre_normalizado"] = nombre_normalizado

        # ====================================================================
        # METADATOS CLICKUP
        # ====================================================================
        result["status"] = task_data.get("status", {}).get("status")
        result["priority"] = task_data.get("priority", {}).get("priority") if task_data.get("priority") else None

        creator = task_data.get("creator", {})
        result["created_by"] = creator.get("username") if creator else None

        assignees = task_data.get("assignees", [])
        if assignees:
            assignee_names = [a.get("username", "") for a in assignees]
            result["assignee"] = ", ".join(assignee_names)
        else:
            result["assignee"] = None

        # ====================================================================
        # FECHAS
        # ====================================================================
        result["date_created"] = LeadService._parse_clickup_date(task_data.get("date_created"))
        result["date_updated"] = LeadService._parse_clickup_date(task_data.get("date_updated"))
        result["due_date"] = LeadService._parse_clickup_date(task_data.get("due_date"))
        
        # Agregamos fecha de cierre si existe (importante para tu modelo)
        result["date_closed"] = LeadService._parse_clickup_date(task_data.get("date_closed"))

        # ====================================================================
        # CAMPOS DE NEGOCIO (custom fields)
        # ====================================================================
        custom_fields = task_data.get("custom_fields", [])
        result.update(LeadService._parse_custom_fields(custom_fields))

        # ====================================================================
        # CONTENIDO Y PARSING (AQUÍ ESTABA EL ERROR)
        # ====================================================================
        task_content = task_data.get("description", "") or task_data.get("text_content", "")
        result["task_content"] = task_content if task_content else None

        extracted_mycase_id = None

        if task_content:
            parsed = parse_task_content(task_content)
            
            # --- CORRECCIÓN CRÍTICA ---
            # Extraemos 'mycase_id' y lo eliminamos del diccionario 'parsed'
            # para que no contamine el diccionario 'result' con una clave inválida.
            if "mycase_id" in parsed:
                extracted_mycase_id = parsed.pop("mycase_id")
            
            # Ahora es seguro hacer update con el resto de campos (email, phone, etc.)
            result.update(parsed)

        # Lógica de prioridad para id_mycase
        if not id_mycase_from_name and extracted_mycase_id:
            result["id_mycase"] = extracted_mycase_id
        else:
            result["id_mycase"] = id_mycase_from_name

        # Comentarios
        result["comment_count"] = len(task_data.get("comments", []))
        
        # --- LIMPIEZA FINAL DE SEGURIDAD ---
        # Aseguramos que bajo ninguna circunstancia 'mycase_id' llegue a la DB
        result.pop("mycase_id", None)

        return result

    @staticmethod
    def _parse_clickup_date(date_value) -> Optional[datetime]:
        """
        Parsea fechas de ClickUp.

        ClickUp puede enviar:
        - Unix timestamp en milisegundos (string o int)
        - Fecha en formato ISO
        - Fecha con ordinales (May 21st 2024)

        Args:
            date_value: Valor de fecha (string, int, None)

        Returns:
            datetime object o None
        """
        if not date_value:
            return None

        try:
            # Si es timestamp Unix (en milisegundos)
            if isinstance(date_value, (int, float)):
                return datetime.fromtimestamp(int(date_value) / 1000)

            if isinstance(date_value, str):
                # Intentar parsear como timestamp
                if date_value.isdigit():
                    return datetime.fromtimestamp(int(date_value) / 1000)

                # Eliminar ordinales (1st, 2nd, 3rd, 4th)
                cleaned = remove_ordinal_suffix(date_value)

                # Parsear con dateutil (soporta múltiples formatos)
                return date_parser.parse(cleaned)

        except (ValueError, OverflowError) as e:
            print(f"Error parseando fecha {date_value}: {e}")
            return None

        return None

    @staticmethod
    def _parse_custom_fields(custom_fields: list) -> Dict:
        """
        Extrae custom fields de ClickUp.

        Mapea nombres de custom fields a columnas de la DB.

        Args:
            custom_fields: Lista de custom fields de ClickUp

        Returns:
            Diccionario con campos parseados
        """
        result = {}

        # Mapeo de nombres de custom fields a columnas
        field_mapping = {
            "Pipeline de Viabilidad": "pipeline_de_viabilidad",
            "Fecha Consulta Original": "fecha_consulta_original",
            "TIS Open": "tis_open",
        }

        for field in custom_fields:
            field_name = field.get("name")
            field_value = field.get("value")

            if field_name in field_mapping:
                column_name = field_mapping[field_name]

                # Parsear según tipo
                field_type = field.get("type")

                if field_type == "date":
                    result[column_name] = LeadService._parse_clickup_date(field_value)
                elif field_type == "checkbox":
                    result[column_name] = field_value is True
                else:
                    result[column_name] = field_value

        return result

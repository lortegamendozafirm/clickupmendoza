# app/services/assignment_service.py
from typing import Dict, Any
from app.services.lead_service import LeadService

class AssignmentService:
    ID_MAP = {
        "298c4ec5-05e3-432e-82da-cc973c44be54": "abogado_asignado",
        "a1c9d406-838f-48c6-b92c-a25992494b62": "proyecto",
        "a42586d8-4725-401e-82cb-55a753496769": "label_type",
        "f4d84c6d-8993-4282-8e68-3f2b96ea71e6": "case_review_status",
        "41889f31-5122-4400-8808-33ded3812d37": "open_case_type",
        "6301c50f-5047-4276-98d3-526d5c6b43ea": "rapsheet_status",
        "15182f5c-d7f8-4c6a-8184-f2c045ef1d21": "link_audio_cr",
        "2c04aa55-b609-4500-9281-0249f20ba594": "link_google_meet",
        "7e08a457-b45c-45f3-bff7-fbb6f1b7eb47": "link_decl_spanish",
        "6ac492a9-047d-4ba9-b7ae-f04c10994b0c": "cover_letter_link",
        "0b8868ab-d3ad-4c3b-b89e-209cb3c31836": "p_plus_filed_copy",
        "388a98e2-bf68-4160-b035-c960f77cb8f9": "cr_done_date",
        "c34dc8d7-fcd1-408a-94d6-35072c6c7fdf": "date_status_signed",
        "b1a419d5-6ba2-4d14-826f-530c1378442f": "fecha_asignacion",
        "a4087fc1-3e54-4f65-acc0-1c2fbcc6fc37": "open_case_date",
        "11aa750a-c424-4059-8945-e501dc132ee2": "deadline_statute",
        "7fbaba79-f396-4131-8737-c9990d717677": "packet_ready_cr",
        "a2e28dca-9b21-4704-b999-e5a1fd557866": "caso_resometer",
        "7609ea7c-eea0-4944-a6fa-22cedde72b14": "id_cliente",
        "a4362bff-2ce5-43a8-a344-a6895186a08c": "mycase_link",
        "2b1227a6-691e-4818-bf30-4acea5ca1b4e": "antiguos_attorney"
    }

    @staticmethod
    def transform_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma el JSON de ClickUp al formato de nuestra DB."""
        
        # 1. Campos de Sistema
        result = {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "status": task_data.get("status", {}).get("status"),
            "list_name": task_data.get("list", {}).get("name"),
            "folder_name": task_data.get("folder", {}).get("name"),
            "space_name": task_data.get("space", {}).get("name"),
            "priority": task_data.get("priority", {}).get("priority") if task_data.get("priority") else None,
            "date_created": LeadService._parse_clickup_date(task_data.get("date_created")),
            "date_updated": LeadService._parse_clickup_date(task_data.get("date_updated")),
            "date_closed": LeadService._parse_clickup_date(task_data.get("date_closed")),
            "date_done": LeadService._parse_clickup_date(task_data.get("date_done")),
            "due_date": LeadService._parse_clickup_date(task_data.get("due_date")),
            "task_content": task_data.get("description") or task_data.get("text_content"),
            "raw_data": task_data
        }

        # 2. Procesar Custom Fields por ID
        creator = task_data.get("creator", {})
        result["created_by"] = creator.get("username") if creator else None

        # Procesar Asignados (Unir múltiples nombres en un string)
        assignees = task_data.get("assignees", [])
        if assignees:
            result["assignee"] = ", ".join([a.get("username", "") for a in assignees])
            
        custom_fields = task_data.get("custom_fields", [])
        for field in custom_fields:
            f_id = field.get("id")
            if f_id in AssignmentService.ID_MAP:
                col_name = AssignmentService.ID_MAP[f_id]
                val = field.get("value")
                
                # Lógica de casteo según tipo de ClickUp
                f_type = field.get("type")
                if f_type == "date" and val:
                    result[col_name] = LeadService._parse_clickup_date(val)
                elif f_type == "checkbox":
                    result[col_name] = val is True or val == "true"
                else:
                    result[col_name] = val

        return result
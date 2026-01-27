# scripts/import_case_assignments.py
import sys
import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models.case_assignment import CaseAssignment
from app.repositories.assignment_repository import AssignmentRepository
from app.services.lead_service import LeadService # Reutilizamos el parseador de fechas

def clean_row(row):
    """Mapea los nombres sucios del CSV a los nombres del modelo CaseAssignment"""
    return {
        "task_id": row.get("Task ID"),
        "task_name": row.get("Task Name"),
        "status": row.get("Status"),
        "priority": row.get("Priority"),
        "assignee": row.get("Assignee"),
        "id_cliente": row.get("ID Cliente (short text)"),
        "mycase_link": row.get("My Case Link (short text)"),
        "date_created": LeadService._parse_clickup_date(row.get("Date Created")),
        "date_updated": LeadService._parse_clickup_date(row.get("Date Updated")),
        "date_closed": LeadService._parse_clickup_date(row.get("Date Closed")),
        "due_date": LeadService._parse_clickup_date(row.get("Due Date")),
        "abogado_asignado": row.get("🧑‍⚖️ Abogado Asignado (drop down)"),
        "proyecto": row.get("🗂️ Proyecto (drop down)"),
        "label_type": row.get("🔖 Label Type (drop down)"),
        "case_review_status": row.get("Case Review Status (drop down)"),
        "open_case_type": row.get("Open Case type (drop down)"),
        "rapsheet_status": row.get("Rapsheet (drop down)"),
        "link_audio_cr": row.get("Link Audio CR (url)"),
        "link_google_meet": row.get("Link Google Meet (short text)"),
        "link_decl_spanish": row.get("Link to DECL Spanish (url)"),
        "cover_letter_link": row.get("📄 Cover Letter Link (short text)"),
        "p_plus_filed_copy": row.get("📑 P+ FILED COPY (url)"),
        "cr_done_date": LeadService._parse_clickup_date(row.get("CR Done Date (date)")),
        "date_status_signed": LeadService._parse_clickup_date(row.get("Date Status SIGNED (date)")),
        "fecha_asignacion": LeadService._parse_clickup_date(row.get("Fecha de Asignación (date)")),
        "open_case_date": LeadService._parse_clickup_date(row.get("Open Case Date (date)")),
        "deadline_statute": LeadService._parse_clickup_date(row.get("⏳ DEADLINE (date)")),
        "packet_ready_cr": row.get("Packet ready for CR (checkbox)") == "true",
        "caso_resometer": row.get("Caso para Resometer (checkbox)") == "true",
        "task_content": row.get("Task Content"),
        "latest_comment": row.get("Latest Comment"),
        "raw_data": row # Guardamos la fila completa como respaldo
    }

def run_import(csv_path):
    engine = create_engine(settings.database_dsn)
    Session = sessionmaker(bind=engine)
    db = Session()
    repo = AssignmentRepository(db)
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            data = clean_row(row)
            if data["task_id"]:
                repo.upsert(data)
            if i % 100 == 0:
                print(f"Procesados {i} registros...")
    print("✅ Importación finalizada.")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    run_import(path)
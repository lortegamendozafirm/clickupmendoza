#!/usr/bin/env python3
import sys
import csv
import re
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuración de rutas
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models.case_assignment import CaseAssignment
from app.services.lead_service import LeadService # Reutilizamos el parse_clickup_date

# Aumentar límite de CSV
csv.field_size_limit(sys.maxsize)

# ============================================================================
# MAPA DE LA VERDAD PARA CASE ASSIGNMENT
# ============================================================================
CSV_TO_DB_MAP = {
    'task_id': 'task_id',
    'task_name': 'task_name',
    'status': 'status',
    'priority': 'priority',
    'assignee': 'assignee',
    'id_cliente_short_text': 'id_cliente',
    'my_case_link_short_text': 'mycase_link',
    
    # Fechas de Sistema
    'date_created': 'date_created',
    'date_updated': 'date_updated',
    'date_closed': 'date_closed',
    'date_done': 'date_done',
    'due_date': 'due_date',
    
    # Campos de Negocio (Custom Fields)
    'abogado_asignado_drop_down': 'abogado_asignado',
    'proyecto_drop_down': 'proyecto',
    'label_type_drop_down': 'label_type',
    'case_review_status_drop_down': 'case_review_status',
    'open_case_type_drop_down': 'open_case_type',
    'rapsheet_drop_down': 'rapsheet_status',
    
    # Links y Docs
    'link_audio_cr_url': 'link_audio_cr',
    'link_google_meet_short_text': 'link_google_meet',
    'link_to_decl_spanish_url': 'link_decl_spanish',
    'cover_letter_link_short_text': 'cover_letter_link',
    'p_filed_copy_url': 'p_plus_filed_copy',
    
    # Fechas de Proceso
    'cr_done_date_date': 'cr_done_date',
    'date_status_signed_date': 'date_status_signed',
    'fecha_de_asignacion_date': 'fecha_asignacion',
    'open_case_date_date': 'open_case_date',
    'deadline_date': 'deadline_statute',
    
    # Checkboxes / Fórmulas
    'packet_ready_for_cr_checkbox': 'packet_ready_cr',
    'caso_para_resometer_checkbox': 'caso_resometer',
    'cr_done_signed_formula': 'cr_done_equals_signed',
    'signed_in_7_days_formula': 'signed_in_7_days',

    # Contenido
    'task_content': 'task_content',
    'latest_comment': 'latest_comment'
}

def clean_header(header: str) -> str:
    if not header: return ""
    h = header.replace('(', ' ').replace(')', '').lower()
    h = re.sub(r'[\s\.]+', '_', h)
    h = re.sub(r'[^a-z0-9_]', '', h).strip('_')
    return h

def process_row(row_dict: dict, header_map: dict) -> dict:
    data = {}
    for csv_header, db_field in header_map.items():
        val = row_dict.get(csv_header, "").strip()
        if not val: continue
            
        # Tratamiento especial según el campo
        if 'date' in db_field or 'deadline' in db_field or 'created' in db_field or 'updated' in db_field:
            data[db_field] = LeadService._parse_clickup_date(val)
        elif db_field in ['packet_ready_cr', 'caso_resometer', 'cr_done_equals_signed', 'signed_in_7_days']:
            data[db_field] = val.lower() in ['true', '1', 'yes', 'si']
        else:
            data[db_field] = val

    data['synced_at'] = datetime.now(timezone.utc)
    return data

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/import_case_assignments.py <archivo.csv>")
        sys.exit(1)

    engine = create_engine(settings.database_dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    file_path = sys.argv[1]
    print(f"🔄 Importando {file_path} a case_assignments...")

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Mapear qué columnas del CSV existen en nuestro mapa
        file_header_map = {h: CSV_TO_DB_MAP[clean_header(h)] for h in reader.fieldnames if clean_header(h) in CSV_TO_DB_MAP}
        
        for i, row in enumerate(reader):
            try:
                clean_data = process_row(row, file_header_map)
                if not clean_data.get('task_id'): continue
                
                obj = CaseAssignment(**clean_data)
                session.merge(obj) # merge hace el upsert
                
                if i % 100 == 0:
                    session.commit()
                    print(f"   ⏳ Procesados {i} registros...", end='\r')
            except Exception as e:
                print(f"\n❌ Error en fila {i}: {e}")
        
        session.commit()
    print(f"\n✅ Importación completada.")

if __name__ == "__main__":
    main()
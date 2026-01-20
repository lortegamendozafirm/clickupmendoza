#!/usr/bin/env python3
"""
Script maestro de importación de históricos (CSV -> PostgreSQL).
CORREGIDO: Soluciona el TypeError 'mycase_id' vs 'id_mycase'.
"""

import sys
import csv
import re
import traceback
from pathlib import Path
from datetime import datetime, timezone
from dateutil import parser as date_parser

# Aumentar el límite de tamaño de campo
csv.field_size_limit(sys.maxsize)

# --- CONFIGURACIÓN DE RUTAS ---
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.lead import LeadsCache
from app.core.parser import parse_task_content

# ============================================================================
# 1. EL MAPA DE LA VERDAD
# ============================================================================
CSV_TO_DB_MAP = {
    # Identificadores
    'task_id': 'task_id',
    'task_id_short_text': 'task_id',
    'task_name': 'task_name',
    'status': 'status',
    
    # Metadatos
    'date_created': 'date_created',
    'date_updated': 'date_updated',
    'due_date': 'due_date',
    'created_by': 'created_by',
    'assignee': 'assignee',
    'priority': 'priority',
    
    # Contenido
    'task_content': 'task_content',
    'latest_comment': 'latest_comment',
    
    # Campos Específicos
    'aviso_de_consulta_drop_down': 'consult_notice',
    'type_of_interview_drop_down': 'interview_type',
    'result_of_interview_drop_down': 'interview_result',
    'my_case_link_short_text': 'mycase_link',
    'my_case_id_short_text': 'id_mycase',
    'open_case_type_drop_down': 'case_type',
    'x_open_case_type_drop_down': 'case_type',
    'fue_videollamada_drop_down': 'video_call',
    'video_llamada_drop_down': 'video_call',
    'record_criminal_drop_down': 'record_criminal',
    'tiene_cortes_migratorias_pendientes_eoir_drop_down': 'eoir_pending',
    'telefono_del_referido_short_text': 'referral_phone_number',
    'nombre_del_referido_short_text': 'referral_full_name',
    'pipeline_de_viabilidad_drop_down': 'pipeline_de_viabilidad',
    'fecha_consulta_original_date': 'fecha_consulta_original',
    'accidente_drop_down': 'accident_last_2y',
    
    # Campos Texto
    'phone_short_text': 'phone_raw',
    'first_name_short_text': 'full_name_extracted',
    'e_mail_email': 'email_extracted',
    'address_location': 'location',
    
    # Calculados
    'nombre_clickup': 'nombre_clickup',
    'id_mycase': 'id_mycase',
    'nombre_normalizado': 'nombre_normalizado',
    'phone_digits': 'phone_number',
}

# ============================================================================
# 2. UTILIDADES
# ============================================================================

def clean_header(header: str) -> str:
    if not header: return ""
    h = header.replace('(', ' ').replace(')', '').lower()
    h = re.sub(r'[\s\.]+', '_', h)
    h = re.sub(r'[^a-z0-9_]', '', h).strip('_')
    return h

def parse_messy_date(date_str: str) -> datetime:
    if not date_str or not isinstance(date_str, str) or not date_str.strip(): return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    try:
        clean = re.sub(r'(?<=\d)(st|nd|rd|th)', '', date_str)
        dt = date_parser.parse(clean)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def normalize_boolean(val: str) -> str:
    if not val: return None
    v = val.lower().strip()
    if v in ['si', 'yes', 'true', '1']: return 'yes'
    if v in ['no', 'false', '0']: return 'no'
    return v

def normalize_task_name_for_search(name: str):
    if not name: return "", ""
    parts = name.split('|')
    clean_name = parts[0].strip()
    normalized = clean_name.upper()
    import unicodedata
    normalized = ''.join(c for c in unicodedata.normalize('NFD', normalized) if unicodedata.category(c) != 'Mn')
    normalized = re.sub(r'[^A-Z0-9\s]', '', normalized)
    return clean_name, normalized

# ============================================================================
# 3. LÓGICA PRINCIPAL
# ============================================================================

def process_row(row_dict: dict, header_map: dict) -> dict:
    lead_data = {}
    
    # 1. Extraer task_content
    content_key = next((k for k, v in header_map.items() if v == 'task_content'), None)
    content_text = row_dict.get(content_key, "") if content_key else ""
    if content_text: content_text = str(content_text)
        
    parsed_data = parse_task_content(content_text)
    
    # 2. Iterar sobre las columnas mapeadas
    for csv_header, db_field in header_map.items():
        val = row_dict.get(csv_header, "")
        if val is None: continue
        val = str(val).strip()
        if not val: continue
            
        if db_field == 'task_content':
            lead_data[db_field] = val
        elif db_field in ['date_created', 'date_updated', 'due_date', 'fecha_consulta_original']:
            lead_data[db_field] = parse_messy_date(val)
        elif db_field in ['video_call', 'accident_last_2y', 'tis_open']:
             if db_field == 'tis_open':
                 lead_data[db_field] = val.lower() in ['true', '1', 'yes']
             else:
                 lead_data[db_field] = normalize_boolean(val)
        else:
            lead_data[db_field] = val

    # 3. Fallback: Rellenar con datos parseados
    for key, val in parsed_data.items():
        if val and (key not in lead_data or not lead_data[key]):
            lead_data[key] = val

    # === CORRECCIÓN FINAL: Arreglar nombres de claves incompatibles ===
    # El parser devuelve 'mycase_id', pero el modelo espera 'id_mycase'
    if 'mycase_id' in lead_data:
        # Si no tenemos ID todavía, usamos el extraído
        if not lead_data.get('id_mycase'):
            lead_data['id_mycase'] = lead_data['mycase_id']
        # ¡IMPORTANTE! Eliminar la clave incorrecta para que no falle el modelo
        del lead_data['mycase_id']
    # ================================================================

    # 4. Normalizaciones finales
    if 'task_name' in lead_data:
        clean, norm = normalize_task_name_for_search(lead_data['task_name'])
        lead_data['nombre_clickup'] = clean
        lead_data['nombre_normalizado'] = norm

    lead_data['synced_at'] = datetime.now(timezone.utc)
    return lead_data

def process_file(file_path: str, session):
    print(f"🔄 Procesando archivo: {file_path}")
    
    count_updated = 0
    count_skipped = 0
    errors_shown = 0
    batch = []
    
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        file_header_map = {}
        
        for h in reader.fieldnames:
            clean = clean_header(h)
            if clean in CSV_TO_DB_MAP:
                file_header_map[h] = CSV_TO_DB_MAP[clean]
        
        print(f"   📋 {len(file_header_map)} columnas mapeadas.")
        
        for i, row in enumerate(reader):
            task_id = None
            if row.get('task_id'): task_id = row.get('task_id')
            elif row.get('Task ID'): task_id = row.get('Task ID')
            else:
                for h, db_field in file_header_map.items():
                    if db_field == 'task_id' and row.get(h):
                        task_id = row.get(h)
                        break
            
            if not task_id:
                count_skipped += 1
                continue
            
            row['task_id'] = task_id

            try:
                lead_dict = process_row(row, file_header_map)
                lead_dict['task_id'] = task_id
                
                lead_obj = LeadsCache(**lead_dict)
                batch.append(lead_obj)
                
            except Exception as e:
                count_skipped += 1
                if errors_shown < 5:
                    print(f"\n❌ Error en fila {i} (ID: {task_id}): {e}")
                    errors_shown += 1
                continue
            
            if len(batch) >= 200:
                for item in batch: session.merge(item)
                session.commit()
                count_updated += len(batch)
                batch = []
                print(f"   ⏳ Procesados {count_updated} | Saltados {count_skipped}...", end='\r')

        if batch:
            for item in batch: session.merge(item)
            session.commit()
            count_updated += len(batch)

    print(f"\n✅ Finalizado: {file_path}")
    print(f"   Total Insertados/Upd: {count_updated}")
    print(f"   Total Saltados:       {count_skipped}")
    print("-" * 40)

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python -m scripts.import_history <archivo1.csv> ...")
        sys.exit(1)

    print("🔌 Conectando a la base de datos...")
    engine = create_engine(settings.database_dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        for file_path in sys.argv[1:]:
            path = Path(file_path)
            if path.exists():
                process_file(path, session)
            else:
                print(f"⚠️  Archivo no encontrado: {path}")
    except Exception as e:
        print(f"\n❌ Error Crítico: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para cargar datos LIMPIOS desde un Excel (.xlsx) a la base de datos.

Este script asume que el Excel ya ha sido procesado y limpiado previamente en R/Python,
por lo que realiza una inserción directa mapeando columnas al modelo SQLAlchemy.

Uso:
    python scripts/load_clean_excel.py /ruta/al/archivo_limpio.xlsx
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import math
import re
from dateutil import parser as date_parser

# Agregar directorio raíz al path para importar módulos de la app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import LeadsCache  # Asegúrate que este modelo tenga los nuevos campos (phone, email, etc.)

def is_nan(value: Any) -> bool:
    """Verifica si un valor es NaN (Not a Number) o None de forma segura."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    # Pandas a veces usa NaT para fechas nulas
    if pd.isna(value):
        return True
    return False

def parse_date_robust(value: Any) -> Any:
    """
    Intenta convertir cualquier valor a un objeto datetime de Python.
    Maneja:
    - Pandas Timestamp / NaT
    - Strings con formato ISO
    - Strings con formato humano en inglés ("Friday, April 4th 2025")
    """
    if is_nan(value):
        return None
        
    # Caso 1: Ya es un objeto datetime o Timestamp
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.to_pydatetime() if isinstance(value, pd.Timestamp) else value
        
    # Caso 2: Es una cadena de texto
    if isinstance(value, str):
        try:
            # Limpieza específica para ClickUp: eliminar sufijos ordinales (1st, 2nd, 3rd, 4th)
            # Regex: busca un dígito seguido de st, nd, rd, th y lo elimina
            clean_str = re.sub(r'(?<=\d)(st|nd|rd|th)', '', value)
            
            # Usar dateutil para parsear el string limpio
            return date_parser.parse(clean_str)
        except Exception as e:
            print(f"⚠️  No se pudo parsear la fecha: '{value}' -> Error: {e}")
            return None
            
    return None

def clean_value(value: Any) -> Any:
    """Limpia valores NaN convirtiéndolos a None para SQL."""
    if is_nan(value):
        return None
    return value

def transform_row_to_lead(row: pd.Series) -> Dict[str, Any]:
    """
    Mapea una fila del DataFrame de Pandas al diccionario del modelo LeadsCache.
    
    Usa los nombres de columnas exactos del summary(dvs_clean).
    """
    result = {}

    # ====================================================================
    # 1. IDENTIFICADORES Y CAMPOS CORE
    # ====================================================================
    result["task_id"] = clean_value(row.get("task_id"))
    
    # Validación crítica: Sin task_id no podemos insertar
    if not result["task_id"]:
        return None

    result["task_name"] = clean_value(row.get("task_name"))
    
    # Identificadores derivados (ya vienen limpios del Excel)
    result["nombre_clickup"] = clean_value(row.get("nombre_clickup"))
    result["nombre_normalizado"] = clean_value(row.get("nombre_normalizado"))
    
    # ID MyCase: Tu summary muestra 'id_mycase' y 'mycase_id'. 
    # Priorizamos 'id_mycase' que parece ser el limpio, o usamos el otro como fallback.
    result["id_mycase"] = clean_value(row.get("id_mycase")) or clean_value(row.get("mycase_id"))

    # ====================================================================
    # 2. METADATOS CLICKUP
    # ====================================================================
    result["status"] = clean_value(row.get("status"))
    result["priority"] = clean_value(row.get("priority"))
    result["created_by"] = clean_value(row.get("created_by"))
    result["assignee"] = clean_value(row.get("assignee"))
    result["task_type"] = clean_value(row.get("task_type"))
    result["space_name"] = clean_value(row.get("space"))
    result["folder_name"] = clean_value(row.get("folder"))
    result["list_name"] = clean_value(row.get("list"))

    # Métricas numéricas
    result["comment_count"] = int(row.get("comment_count", 0)) if not is_nan(row.get("comment_count")) else 0

    # ====================================================================
    # 3. FECHAS (Pandas ya las maneja como Timestamp, convertir a Python datetime)
    # ====================================================================
    def to_py_datetime(val):
        if is_nan(val): return None
        return val.to_pydatetime() if isinstance(val, pd.Timestamp) else val

    result["date_created"] = parse_date_robust(row.get("date_created"))
    result["date_updated"] = parse_date_robust(row.get("date_updated"))
    result["due_date"] = parse_date_robust(row.get("due_date"))
    
    # Aquí es donde fallaba: fecha_consulta_original venía como texto "Friday..."
    result["fecha_consulta_original"] = parse_date_robust(row.get("fecha_consulta_original_date"))
    # Si viene como string en el Excel, intentar parsear, si ya es fecha, dejarla.
    # (Asumiendo que Pandas infirió el tipo object o datetime)

    # ====================================================================
    # 4. LÓGICA DE NEGOCIO Y CAMPOS MINADOS
    # ====================================================================
    result["pipeline_de_viabilidad"] = clean_value(row.get("pipeline_de_viabilidad_drop_down"))
    
    # Booleanos (Excel puede traer "TRUE", 1, True)
    tis_open_val = row.get("tis_open")
    if not is_nan(tis_open_val):
        result["tis_open"] = str(tis_open_val).lower() in ["true", "1", "yes"]
    else:
        result["tis_open"] = None

    # Campos de contacto extraídos
    result["full_name_extracted"] = clean_value(row.get("full_name"))
    result["phone_number"] = clean_value(row.get("phone_number")) # El limpio
    result["email_extracted"] = clean_value(row.get("email"))
    result["location"] = clean_value(row.get("location"))

    # Campos legales / Entrevista
    result["interview_type"] = clean_value(row.get("interview_type"))
    result["interview_result"] = clean_value(row.get("interview_result"))
    result["case_type"] = clean_value(row.get("case_type"))
    result["consult_notice"] = clean_value(row.get("consult_notice"))
    result["mycase_link"] = clean_value(row.get("mycase_link"))

    # === AGREGAR ESTAS LÍNEAS QUE FALTABAN ===
    result["video_call"] = clean_value(row.get("video_call"))
    result["accident_last_2y"] = clean_value(row.get("accident_last_2y"))
    result["record_criminal"] = clean_value(row.get("record_criminal"))
    result["joint_residences"] = clean_value(row.get("joint_residences"))
    result["eoir_pending"] = clean_value(row.get("eoir_pending"))
    result["tvisa_min_wage"] = clean_value(row.get("tvisa_min_wage"))
    
    # Referidos (si los tienes en el Excel)
    result["referral_full_name"] = clean_value(row.get("referral_full_name"))
    result["referral_phone_number"] = clean_value(row.get("referral_phone_number"))
    # ==========================================

    # Contenido
    result["task_content"] = clean_value(row.get("task_content"))
    result["latest_comment"] = clean_value(row.get("latest_comment"))

    # Metadata de sincronización
    result["synced_at"] = datetime.utcnow()

    return result

def load_excel_file(file_path: str):
    """Carga datos desde un archivo Excel usando Pandas."""

    print(f"📦 Cargando archivo Excel: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ Error: El archivo {file_path} no existe.")
        sys.exit(1)

    # 1. Leer Excel con Pandas
    try:
        print("   ⏳ Leyendo archivo (esto puede tardar unos segundos)...")
        # Leemos todo como object para evitar conversiones automáticas erróneas, 
        # excepto las fechas que sabemos que son fechas.
        df = pd.read_excel(file_path)
        
        # Convertir columnas de fecha explícitamente si Pandas no lo hizo
        date_cols = ['date_created', 'date_updated', 'due_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        print(f"   ✅ Archivo leído: {len(df)} filas encontradas.")
        print(f"   ℹ️  Columnas en Excel: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Error crítico leyendo el Excel: {e}")
        sys.exit(1)

    # 2. Configurar DB
    engine = create_engine(settings.database_dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_processed = 0
    total_inserted = 0
    total_updated = 0
    total_errors = 0

    print("\n🚀 Iniciando carga a Base de Datos...")

    try:
        # Iterar sobre el DataFrame
        for index, row in df.iterrows():
            try:
                # Transformar
                lead_data = transform_row_to_lead(row)

                if not lead_data:
                    # Fila vacía o sin task_id
                    total_errors += 1
                    continue

                task_id = lead_data["task_id"]

                # Upsert lógico: Buscar si existe
                existing = session.query(LeadsCache).filter_by(task_id=task_id).first()

                if existing:
                    # UPDATE
                    for key, value in lead_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    total_updated += 1
                else:
                    # INSERT
                    # Asegurarse de no pasar claves que no existen en el modelo
                    # (Filtrar keys que no están en el modelo si es necesario, 
                    # pero asumimos que transform_row_to_lead es correcto)
                    lead = LeadsCache(**lead_data)
                    session.add(lead)
                    total_inserted += 1

                total_processed += 1

                # Commit por lotes (batch)
                if total_processed % 500 == 0:
                    session.commit()
                    print(f"   └─ Procesados: {total_processed} ({total_updated} upd, {total_inserted} ins)")

            except Exception as e:
                print(f"   ⚠️  Error en fila {index + 2} (Task ID: {row.get('task_id', 'Unknown')}): {e}")
                total_errors += 1
                session.rollback() # Rollback solo de esta transacción fallida si es necesario
                continue

        # Commit final
        session.commit()
        
        print("\n" + "=" * 60)
        print("🎉 CARGA COMPLETADA")
        print(f"   Total filas procesadas: {total_processed}")
        print(f"   Insertados: {total_inserted}")
        print(f"   Actualizados: {total_updated}")
        print(f"   Errores/Omitidos: {total_errors}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error crítico en base de datos: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    if len(sys.argv) < 2:
        print("❌ Error: Debes especificar el archivo Excel.")
        print("Uso: python scripts/load_clean_excel.py <archivo.xlsx>")
        sys.exit(1)

    file_path = sys.argv[1]
    load_excel_file(file_path)

if __name__ == "__main__":
    main()
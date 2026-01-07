#!/usr/bin/env python3
"""
Script para cargar datos históricos desde CSVs a la base de datos.

Replica la lógica del script de R para procesar archivos CSV de ClickUp.

Uso:
    python scripts/load_historical_data.py file1.csv file2.csv ...
    python scripts/load_historical_data.py /home/ortega/Descargas/*.csv
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import re

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import LeadsCache
from app.core.parser import parse_task_content
from app.core.normalizer import normalize_task_name
from app.core.text_utils import remove_ordinal_suffix
from dateutil import parser as date_parser


def normalize_column_name(name: str) -> str:
    """
    Normaliza nombres de columnas de CSV.

    Replica la lógica de R:
    - trimws()
    - gsub("  ", " ", ...)
    - make.names()
    """
    # Trim
    name = name.strip()

    # Colapsar espacios múltiples
    name = re.sub(r'\s+', ' ', name)

    # Convertir a snake_case (make.names en R)
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')

    return name


def parse_csv_date(date_str: str) -> datetime:
    """
    Parsea fechas del CSV (con ordinales).

    Replica: normalizar_fechas_dvs() de R
    """
    if not date_str or date_str.strip() == "":
        return None

    try:
        # Eliminar ordinales (1st, 2nd, etc.)
        cleaned = remove_ordinal_suffix(date_str)

        # Parsear con dateutil
        return date_parser.parse(cleaned)
    except Exception as e:
        print(f"⚠️  Error parseando fecha '{date_str}': {e}")
        return None


def read_csv_as_text(file_path: str) -> List[Dict]:
    """
    Lee CSV con todas las columnas como texto.

    Replica: read_csv(col_types = cols(.default = col_character()))
    """
    rows = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Normalizar nombres de columnas
        fieldnames_normalized = [normalize_column_name(name) for name in reader.fieldnames]
        reader.fieldnames = fieldnames_normalized

        for row in reader:
            rows.append(row)

    return rows


def transform_csv_row_to_lead(row: Dict) -> Dict:
    """
    Transforma una fila de CSV en un diccionario para LeadsCache.

    Args:
        row: Fila del CSV (dict con columnas normalizadas)

    Returns:
        Diccionario listo para insertar en DB
    """
    result = {}

    # ====================================================================
    # IDENTIFICADORES
    # ====================================================================
    result["task_id"] = row.get("task_id")
    result["task_name"] = row.get("task_name", "")

    # Normalizar task_name
    nombre_clickup, id_mycase_from_name, nombre_normalizado = normalize_task_name(
        result["task_name"]
    )
    result["nombre_clickup"] = nombre_clickup
    result["nombre_normalizado"] = nombre_normalizado

    # ====================================================================
    # METADATOS CLICKUP
    # ====================================================================
    result["status"] = row.get("status")
    result["priority"] = row.get("priority")
    result["created_by"] = row.get("created_by")
    result["assignee"] = row.get("assignees")

    # Fechas
    result["date_created"] = parse_csv_date(row.get("date_created"))
    result["date_updated"] = parse_csv_date(row.get("date_updated"))
    result["due_date"] = parse_csv_date(row.get("due_date"))

    # ====================================================================
    # CAMPOS DE NEGOCIO (si existen en CSV)
    # ====================================================================
    result["pipeline_de_viabilidad"] = row.get("pipeline_de_viabilidad")

    fecha_consulta = row.get("fecha_consulta_original")
    if fecha_consulta:
        result["fecha_consulta_original"] = parse_csv_date(fecha_consulta)

    tis_open = row.get("tis_open")
    if tis_open:
        result["tis_open"] = tis_open.lower() in ["true", "1", "yes"]

    # ====================================================================
    # CONTENIDO Y PARSING
    # ====================================================================
    task_content = row.get("task_content") or row.get("description") or row.get("text_content")

    # Normalizar contenido vacío (del R script)
    if task_content and task_content.strip() in ["\n", "\n\n \n\n", "/\n", "/\n\n"]:
        task_content = None

    result["task_content"] = task_content

    # Parse task_content
    if task_content:
        parsed = parse_task_content(task_content)
        result.update(parsed)

        # ID MyCase: preferir del contenido, sino del nombre
        if not id_mycase_from_name and parsed.get("mycase_id"):
            result["id_mycase"] = parsed["mycase_id"]
        else:
            result["id_mycase"] = id_mycase_from_name
    else:
        result["id_mycase"] = id_mycase_from_name

    # Comment count
    comment_count = row.get("comment_count")
    if comment_count and comment_count.isdigit():
        result["comment_count"] = int(comment_count)

    result["synced_at"] = datetime.utcnow()

    return result


def load_csv_files(file_paths: List[str]):
    """Carga datos desde archivos CSV a la base de datos"""

    print("📦 Cargando datos históricos desde CSV...")
    print(f"📁 Archivos: {len(file_paths)}")
    print()

    # Crear engine y session
    engine = create_engine(settings.database_dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_processed = 0
    total_inserted = 0
    total_updated = 0
    total_errors = 0

    try:
        for file_path in file_paths:
            print(f"📄 Procesando: {file_path}")

            # Leer CSV
            try:
                rows = read_csv_as_text(file_path)
                print(f"   └─ {len(rows)} filas leídas")
            except Exception as e:
                print(f"   └─ ❌ Error leyendo archivo: {e}")
                total_errors += len(rows) if 'rows' in locals() else 0
                continue

            # Procesar filas
            for i, row in enumerate(rows, 1):
                try:
                    # Transformar
                    lead_data = transform_csv_row_to_lead(row)

                    task_id = lead_data.get("task_id")
                    if not task_id:
                        print(f"   └─ ⚠️  Fila {i}: Sin task_id, omitiendo")
                        total_errors += 1
                        continue

                    # Buscar si existe
                    existing = session.query(LeadsCache).filter_by(task_id=task_id).first()

                    if existing:
                        # UPDATE
                        for key, value in lead_data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        total_updated += 1
                    else:
                        # INSERT
                        lead = LeadsCache(**lead_data)
                        session.add(lead)
                        total_inserted += 1

                    total_processed += 1

                    # Commit cada 100 registros
                    if total_processed % 100 == 0:
                        session.commit()
                        print(f"   └─ ✓ {total_processed} registros procesados...")

                except Exception as e:
                    print(f"   └─ ❌ Error en fila {i}: {e}")
                    total_errors += 1
                    continue

            # Commit final del archivo
            session.commit()
            print(f"   └─ ✅ Archivo completado\n")

        # Resumen final
        print("=" * 60)
        print("🎉 Carga completada!")
        print(f"   Total procesado: {total_processed}")
        print(f"   Insertados: {total_inserted}")
        print(f"   Actualizados: {total_updated}")
        print(f"   Errores: {total_errors}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


def main():
    """Punto de entrada del script"""
    print(sys.argv)
    if len(sys.argv) < 2:
        print("❌ Error: No se especificaron archivos CSV")
        print("\nUso:")
        print("  python scripts/load_historical_data.py file1.csv file2.csv ...")
        print("  python scripts/load_historical_data.py /path/to/*.csv")
        sys.exit(1)

    file_paths = sys.argv[1:]

    # Validar que los archivos existen
    valid_paths = []
    for path in file_paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            print(f"⚠️  Archivo no encontrado: {path}")

    if not valid_paths:
        print("❌ No se encontraron archivos válidos")
        sys.exit(1)

    load_csv_files(valid_paths)


if __name__ == "__main__":
    main()

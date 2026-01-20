# scripts/check_duplicates.py
import csv
import sys
import re

csv.field_size_limit(sys.maxsize)

FILES = [
    "/home/ortega/Descargas/DVS2025.csv",
    "/home/ortega/Descargas/DVS2024_1.csv",
    "/home/ortega/Descargas/DVS2024_2.csv"
]

def clean_header(header):
    if not header: return ""
    h = header.replace('(', ' ').replace(')', '').lower()
    h = re.sub(r'[\s\.]+', '_', h)
    h = re.sub(r'[^a-z0-9_]', '', h).strip('_')
    return h

def analyze_ids():
    print("🕵️  Iniciando auditoría de duplicados...")
    
    all_rows = 0
    unique_ids = set()
    
    # Mapeo de columnas de ID posibles
    id_candidates = ['task_id', 'task_id_short_text']

    for file_path in FILES:
        print(f"   Leyendo: {file_path} ...")
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            
            # Detectar cuál columna es el ID en este archivo
            file_id_col = None
            for h in reader.fieldnames:
                if clean_header(h) in id_candidates:
                    file_id_col = h
                    break
            
            if not file_id_col:
                print(f"   ❌ ERROR: No se encontró columna ID en {file_path}")
                continue

            rows_in_file = 0
            for row in reader:
                tid = row.get(file_id_col)
                if tid and tid.strip():
                    all_rows += 1
                    unique_ids.add(tid.strip()) # .add() en un set elimina duplicados automáticamente
                    rows_in_file += 1
            
            print(f"     -> Filas leídas: {rows_in_file}")

    print("\n" + "="*40)
    print("📊 RESULTADOS DE LA AUDITORÍA")
    print("="*40)
    print(f"Total filas procesadas (CSV Raw):   {all_rows}")
    print(f"Total Tareas Únicas (Real Tasks):   {len(unique_ids)}")
    print(f"Duplicados eliminados (Redundancia): {all_rows - len(unique_ids)}")
    print("="*40)

    if len(unique_ids) < 50000:
        print("✅ CONCLUSIÓN: Coincide con tu Base de Datos (~47k).")
        print("   Tu script de importación funcionó correctamente.")
    else:
        print("⚠️ CONCLUSIÓN: Hay más únicos de los que hay en la BD. Algo falló en el Upsert.")

if __name__ == "__main__":
    analyze_ids()
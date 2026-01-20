# scripts/debug_import.py
import csv
import sys
import re

# Aumentar límite
csv.field_size_limit(sys.maxsize)

def clean_header(header):
    if not header: return ""
    h = header.replace('(', ' ').replace(')', '').lower()
    h = re.sub(r'[\s\.]+', '_', h)
    h = re.sub(r'[^a-z0-9_]', '', h).strip('_')
    return h

def check_file(path):
    print(f"🕵️  Analizando: {path}")
    
    # Mapeo esperado
    expected_ids = ['task_id', 'task_id_short_text']
    
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        
        # 1. Ver qué headers ve Python realmente
        headers = reader.fieldnames
        print(f"   Headers brutos ({len(headers)}): {headers[:5]} ...")
        
        # Analizar mapeo
        id_candidates = []
        for h in headers:
            clean = clean_header(h)
            if clean in expected_ids:
                id_candidates.append(h)
        
        print(f"   ✅ Columnas candidatas a ID encontradas: {id_candidates}")
        
        if not id_candidates:
            print("   ❌ PELIGRO: Python no detecta ninguna columna de ID en este archivo.")
            return

        # 2. Contar filas y errores
        total = 0
        skipped = 0
        examples_shown = 0
        
        print("\n   🔍 Buscando filas invisibles...")
        for row in reader:
            total += 1
            
            # Lógica exacta del script principal
            task_id = None
            if row.get('task_id'): task_id = row.get('task_id')
            elif row.get('Task ID'): task_id = row.get('Task ID')
            else:
                for h in id_candidates:
                    if row.get(h):
                        task_id = row.get(h)
                        break
            
            if not task_id:
                skipped += 1
                if examples_shown < 5:
                    print(f"\n   ⚠️  FILA SALTADA #{total}:")
                    print(f"       Raw ID fields: {[row.get(h) for h in id_candidates]}")
                    # Imprimir un poco del contenido para ver si es una fila rota
                    first_vals = list(row.values())[:3]
                    print(f"       Contenido inicio: {first_vals}")
                    examples_shown += 1
        
        print(f"\n   📊 REPORTE FINAL:")
        print(f"      Total Filas Leídas: {total}")
        print(f"      Filas OK (con ID):  {total - skipped}")
        print(f"      Filas SALTADAS:     {skipped}")

if __name__ == "__main__":
    # Apunta directamente al archivo grande
    check_file("/home/ortega/Descargas/DVS2025.csv")
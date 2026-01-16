import pandas as pd
import re
import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
# Coloca aquí la ruta de tu archivo original
CSV_PATH = r"/home/ortega/Descargas/2026-01-08T16_32_49.743Z.csv"

# Columnas que son FECHAS y deben transformarse a DD/MM/AAAA
DATE_COLUMNS = [
    "Due Date","Start Date","Date Created","Date Updated","Date Closed",
    "Date Done","CR Done Date (date)","Date Status SIGNED (date)", "DUE DATE (date)"
]

# Columnas estrictamente necesarias (se borrará el resto)
CSV_REQUIRED_COLUMNS = [
    "Task Name","Status","Assignee","Priority","Due Date","Start Date",
    "Date Created","Date Updated","Date Closed","Date Done","tags",
    "Open Case type (drop down)","CR Done Date (date)",
    "CR vs Signed (formula)","Case Review Status (drop down)",
    "Caso para Resometer (checkbox)","Classify (drop down)",
    "DOCU SIGN - Atty (drop down)","DOCU SIGN -CL (drop down)",
    "Date Status SIGNED (date)","DUE DATE (date)","ID Cliente (short text)",
    "Packet ready for CR (checkbox)","Rapsheet (drop down)",
    "🔖 Label Type (drop down)","🗂️ Proyecto (drop down)",
    "🧑‍⚖️ Abogado Asignado (drop down)"
]

# ============================================================
# FUNCIONES DE LIMPIEZA
# ============================================================

def normalizar_ordinales(s: str) -> str:
    # Quita st, nd, rd, th de los números (ej: 1st -> 1)
    return re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", s)

def convertir_fecha_ddmmaaaa(val: str) -> str:
    """Convierte formatos variados de fecha a DD/MM/AAAA"""
    val = str(val).strip()
    if not val: return ""
    
    # Limpieza de basura (horas, días de la semana, etc)
    s = re.sub(r"\s[-+]\d\d:\d\d$", "", val)
    s = re.sub(r",?\s*\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?", "", s, flags=re.I)
    s = re.sub(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]*", "", s, flags=re.I)
    s = normalizar_ordinales(s).strip().strip(",")

    # Intentar varios formatos
    for fmt in ("%B %d %Y", "%B %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except:
            pass
    return val

def limpiar_assignee_value(a):
    """Normaliza los nombres de los asignados"""
    NOMBRES_VALIDOS = [
        "Pedro Nieves","Eugenia Ibarra","Paola Linares","Jesús Rosario","Jesus Rosario",
        "Jesús Daniel Martínez Irizarry","Jeyka Perez","Laura Rivera","Saquía Rivera Azize",
        "Cristian Soto","Janice Zayas","Barbara Becerra","Felmarie Figuera",
        "Felmarie Figueroa","Vanelisse Encarnación","Edwin Rivera","Eric Dessus",
        "Eric Ian Dessus Matos","Maria Colon","Jesús Martinez","Jose Ballesteros"
    ]
    a = (a or "").strip()
    if not a: return a
    
    # Caso especial Barbara
    if "barbara" in a.lower(): return "Barbara Becerra"
    
    # Búsqueda aproximada
    for name in NOMBRES_VALIDOS:
        if name.lower() in a.lower():
            return name
    return a

def limpiar_id(v):
    """Deja solo los números"""
    return "".join(ch for ch in str(v) if ch.isdigit())

# ============================================================
# PROCESO PRINCIPAL
# ============================================================

def procesar_localmente():
    print("🚀 Leyendo CSV original...")
    # Leer CSV
    df_raw = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    # 1. Filtrar columnas y limpiar espacios básicos
    print("🧹 Filtrando columnas y limpiando espacios...")
    data = {col: df_raw[col] if col in df_raw else "" for col in CSV_REQUIRED_COLUMNS}
    df_clean = pd.DataFrame(data).fillna("").astype(str).apply(lambda s: s.str.strip())

    # 2. Generar el ID CLIENTE (Lógica compleja del script original)
    # El script original combinaba la columna "ID Cliente (short text)" con la columna índice 64 del csv raw
    print("🆔 Generando ID de Cliente compuesto...")
    try:
        col65 = df_raw.iloc[:, 64] # Columna 65 (índice 64)
    except:
        col65 = [""] * len(df_raw) # Si no existe, rellenar con vacíos

    col_form = df_clean.get("ID Cliente (short text)", [""]*len(df_clean))
    
    ids_finales = []
    for a, b in zip(col_form, col65):
        # Prioridad a la columna del short text, si no, usa la columna 65
        val = limpiar_id(a) if str(a).strip() else limpiar_id(b)
        ids_finales.append(val)
    
    # Insertamos el ID calculado al inicio
    df_clean.insert(0, "ID_CALCULADO", ids_finales)

    # 3. Normalizar Fechas
    print("📅 Normalizando fechas...")
    for col in DATE_COLUMNS:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(convertir_fecha_ddmmaaaa)

    # 4. Normalizar Assignee (Asignados)
    print("👤 Normalizando nombres de asignados...")
    if "Assignee" in df_clean.columns:
        df_clean["Assignee"] = df_clean["Assignee"].apply(limpiar_assignee_value)

    # 5. Guardar resultado
    output_file = "CSV_LIMPIO_PARA_REVISAR.csv"
    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ ¡Listo! Archivo guardado como: {output_file}")
    print("   Ahora puedes abrirlo en Excel para verificar la limpieza.")

if __name__ == "__main__":
    procesar_localmente()
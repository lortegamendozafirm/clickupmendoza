import os
import re
import time
import pandas as pd
import gspread
import datetime
from tqdm import tqdm
from google.oauth2.service_account import Credentials

# ============================================================
# CONFIGURACIÓN
# ============================================================

# --- ¡EDITAR ESTA RUTA! ---
# Ruta a tu archivo de credenciales JSON de Google Service Account
SERVICE_ACCOUNT_FILE = r"C:\Users\fam_g\OneDrive\Documents\platinum-loop-463001-n0-6421805364bb.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

MASTER_URL = "https://docs.google.com/spreadsheets/d/1U21BvVZtiJBnGyy9RJ1oRZQR-x4q6xQNCfqqKjqlKxA/edit"
MASTER_TAB = "Master"

UNIFICADO_URL = "https://docs.google.com/spreadsheets/d/10ygkwwapPEnK4_AWMsbVNxmgbnb-pxr-Okoy-5xbbG4/edit"
VISAS_URL     = "https://docs.google.com/spreadsheets/d/1GnOoXNRfRi4AR39m2FSKtfUc-r0bppYNpG4eWwBOm8E/edit"
IMPORT_URL    = "https://docs.google.com/spreadsheets/d/1b9H54Z3mSbtrjJmz5Gc4lm76G5HRNmeJMyK9QLWIPmA/edit"
DESCARGA_MC_URL = "https://docs.google.com/spreadsheets/d/1JTeMfMik_5slthEv1AY1b5jxWen4pAAPZbmR_2TTLFg/edit"

# --- ¡EDITAR ESTA RUTA! ---
# Ruta a tu archivo CSV descargado
CSV_PATH = r"C:\Users\fam_g\Downloads\2026-01-05T14_07_14.384Z The Mendoza Law Firm - Assignment My Case - Case Assigment - 📋 Case Assignment.csv"


DATE_COLUMNS = [
    "Due Date","Start Date","Date Created","Date Updated","Date Closed",
    "Date Done","CR Done Date (date)","Date Status SIGNED (date)"
]

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
# GOOGLE CLIENTE
# ============================================================
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# ============================================================
# HELPERS
# ============================================================
def num_to_col(n):
    s = ""
    while n > 0:
        n, r = divmod(n-1, 26)
        s = chr(r + 65) + s
    return s

def limpiar_id(v):
    return "".join(ch for ch in str(v) if ch.isdigit())

# ============================================================
# LIMPIEZA CSV
# ============================================================
def limpiar_csv_como_original(df):
    print("📌 Limpiando CSV…")
    data = {col: df[col] if col in df else "" for col in CSV_REQUIRED_COLUMNS}
    df2 = (
        pd.DataFrame(data)
        .fillna("")
        .astype(str)
        .apply(lambda s: s.str.strip())
    )
    print("✔ CSV limpio")
    return df2

# ============================================================
# FECHAS
# ============================================================
def normalizar_ordinales(s: str) -> str:
    return re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", s)

def convertir_fecha_ddmmaaaa(val: str) -> str:
    val = str(val).strip()
    if not val:
        return ""
    s = re.sub(r"\s[-+]\d\d:\d\d$", "", val)
    s = re.sub(r",?\s*\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?", "", s, flags=re.I)
    s = re.sub(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]*", "", s, flags=re.I)
    s = normalizar_ordinales(s).strip().strip(",")

    for fmt in ("%B %d %Y", "%B %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except:
            pass
    return val

# ============================================================
# ASSIGNEE NORMALIZATION
# ============================================================
NOMBRES_VALIDOS = [
    "Pedro Nieves","Eugenia Ibarra","Paola Linares","Jesús Rosario","Jesus Rosario",
    "Jesús Daniel Martínez Irizarry","Jeyka Perez","Laura Rivera","Saquía Rivera Azize",
    "Cristian Soto","Janice Zayas","Barbara Becerra","Felmarie Figuera",
    "Felmarie Figueroa","Vanelisse Encarnación","Edwin Rivera","Eric Dessus",
    "Eric Ian Dessus Matos","Maria Colon","Jesús Martinez","Jose Ballesteros"
]

def limpiar_assignee_value(a):
    a = (a or "").strip()
    if not a:
        return a
    # Override: cualquier "barbara" → Barbara Becerra
    if "barbara" in a.lower():
        return "Barbara Becerra"
    # Match aproximado contra la lista de nombres válidos
    for name in NOMBRES_VALIDOS:
        if name.lower() in a.lower():
            return name
    return a

# ============================================================
# LOOKUP HELPERS
# ============================================================
def dict_from_df(df, col):
    return {
        str(r[col]).strip().lower(): r
        for _, r in df.iterrows()
        if str(r[col]).strip()
    }

# ============================================================
# OPEN DATE LOOKUP (AK)
# ============================================================
def cargar_fuentes_open_date():
    print("📌 Cargando DescargaMyCase (Open Date)…")
    sh = client.open_by_url(DESCARGA_MC_URL)
    df = pd.DataFrame(sh.worksheet("DescargaMyCase").get_all_values())

    df.columns = list(df.iloc[0])
    df = df[1:]

    lk_id = {
        str(r["ID LIMPIO"]).strip().lower(): r
        for _, r in df.iterrows()
        if str(r["ID LIMPIO"]).strip()
    }
    lk_name = {
        str(r["Case Name"]).strip().lower(): r
        for _, r in df.iterrows()
        if str(r["Case Name"]).strip()
    }

    print("✔ Open Date listo")
    return lk_id, lk_name

def extraer_fecha_mc(v):
    """Extrae SOLO fechas válidas de la fila, ignorando 'Pending', 'RFA', 'EAD', etc."""
    # Caso string simple
    if isinstance(v, str):
        v = v.strip()
        if any(x in v for x in ["/", "-"]):
            return convertir_fecha_ddmmaaaa(v)
        return ""

    # Caso Series → revisar TODAS las columnas
    if isinstance(v, pd.Series):
        for key, val in v.items():
            val = str(val).strip()

            # Detectar si parece fecha
            if any(x in val for x in ["/", "-"]):

                # Filtrar textos NO fecha
                if any(w in val.lower() for w in ["pending", "ready", "ead", "rfa", "approval"]):
                    continue

                # Validación de formato dd/mm/aaaa, mm/dd/aaaa, yyyy-mm-dd, etc.
                if re.search(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}", val):
                    return convertir_fecha_ddmmaaaa(val)

        return ""

    return ""

def buscar_open_date(idm, nam, lk_id, lk_name):
    if idm in lk_id:
        return extraer_fecha_mc(lk_id[idm]), True
    if nam in lk_name:
        return extraer_fecha_mc(lk_name[nam]), True
    return "", False

# ============================================================
# OTROS LOOKUPS
# ============================================================
def cargar_fuentes_unificado_mgm():
    print("📌 Cargando UNIFICADO/MGM…")
    sh = client.open_by_url(UNIFICADO_URL)
    unif = pd.DataFrame(sh.worksheet("UNIFICADO").get_all_values())
    mgm  = pd.DataFrame(sh.worksheet("MGM").get_all_values())
    print("✔ UNIFICADO/MGM listo")
    return dict_from_df(unif, 0), dict_from_df(unif, 2), dict_from_df(mgm, 0), dict_from_df(mgm, 1)

def buscar_unificado(idm, nam, lk_id, lk_name, lk_mgm_id, lk_mgm_name):
    if idm in lk_id:
        r = lk_id[idm]
        return (r[22] if len(r)>22 else "",
                r[21] if len(r)>21 else "",
                True)
    if nam in lk_name:
        r = lk_name[nam]
        return (r[22] if len(r)>22 else "",
                r[21] if len(r)>21 else "",
                True)
    if idm in lk_mgm_id or nam in lk_mgm_name:
        return "MGM Review", "", True
    return "", "", False

def cargar_fuentes_visas():
    print("📌 Cargando VISAS…")
    sh = client.open_by_url(VISAS_URL)
    df1 = pd.DataFrame(sh.worksheet("VAWA/VISA T").get_all_values())
    df2 = pd.DataFrame(sh.worksheet("OTHER VISAS").get_all_values())
    print("✔ VISAS listo")

    def combo(dfs, col):
        out = {}
        for d in dfs:
            for _, r in d.iterrows():
                k = str(r[col]).strip().lower()
                if k:
                    out[k] = r
        return out

    return combo([df1, df2], 1), combo([df1, df2], 2)

def buscar_visas(idm, nam, lk_id, lk_name):
    if idm in lk_id:
        r = lk_id[idm]
    elif nam in lk_name:
        r = lk_name[nam]
    else:
        return "", "", False
    return (r[7] if len(r)>7 else "",
            r[10] if len(r)>10 else "",
            True)

def cargar_fuentes_import():
    print("📌 Cargando IMPORT…")
    sh = client.open_by_url(IMPORT_URL)
    df = pd.DataFrame(sh.worksheet("IMPORT").get_all_values())
    print("✔ IMPORT listo")
    return dict_from_df(df, 0), dict_from_df(df, 1)

def buscar_import(idm, nam, lk_id, lk_name):
    if idm in lk_id:
        r = lk_id[idm]
    elif nam in lk_name:
        r = lk_name[nam]
    else:
        return "", "", False
    return (r[3] if len(r)>3 else "",
            r[5] if len(r)>5 else "",
            True)

# ============================================================
# BATCH UPDATE
# ============================================================
def batch_update(sh, updates, chunk=200, wait=0.8):
    for i in range(0, len(updates), chunk):
        print(f"⬆ Subiendo batch {i//chunk + 1}/{(len(updates)-1)//chunk + 1}")
        body = {"valueInputOption": "USER_ENTERED", "data": updates[i:i+chunk]}
        try:
            sh.values_batch_update(body)
        except:
            time.sleep(2)
            sh.values_batch_update(body)
        time.sleep(wait)

# ============================================================
# POSTPROCESOS
# ============================================================
def aplicar_postprocesos(sh, ws, final_vals):
    print("📌 Ejecutando postprocesos…")

    header = final_vals[0]
    rows   = final_vals[1:]
    n = len(rows)
    map_ = {h:i for i,h in enumerate(header)}

    # ASSIGNEE
    if "Assignee" in map_:
        idx = map_["Assignee"]
        colL = num_to_col(idx+1)
        print("➡ Normalizando Assignee…")
        ws.update(
            f"{colL}2:{colL}{n+1}",
            [[limpiar_assignee_value(r[idx])] for r in rows]
        )

    # FECHAS
    print("➡ Normalizando fechas…")
    date_updates = []
    for col_name in DATE_COLUMNS:
        if col_name in map_:
            idx = map_[col_name]
            colL = num_to_col(idx+1)
            date_updates.append({
                "range": f"{colL}2:{colL}{n+1}",
                "values": [[convertir_fecha_ddmmaaaa(r[idx])] for r in rows]
            })
    if date_updates:
        batch_update(sh, date_updates, chunk=5)

    print("📌 Cargando fuentes para Lookups…")
    id_idx   = map_["ID"]
    name_idx = map_["Task Name"]

    lk_unif_id, lk_unif_name, lk_mgm_id, lk_mgm_name = cargar_fuentes_unificado_mgm()
    lk_vis_id,  lk_vis_name  = cargar_fuentes_visas()
    lk_imp_id,  lk_imp_name  = cargar_fuentes_import()
    lk_od_id,   lk_od_name   = cargar_fuentes_open_date()

    ac_vals=[]; ad_vals=[]
    ae_vals=[]; af_vals=[]
    ag_vals=[]; ah_vals=[]
    ak_vals=[]

    print("📌 Aplicando Lookups AC–AH–AK…")

    for r in tqdm(rows, desc="Aplicando AC–AH–AK", unit="fila"):

        idm = limpiar_id(r[id_idx]).lower()
        nam = r[name_idx].strip().lower()

        # UNIFICADO/MGM → AC, AD
        w_val, v_val, ok_unif = buscar_unificado(idm, nam, lk_unif_id, lk_unif_name, lk_mgm_id, lk_mgm_name)
        ac_vals.append([w_val if ok_unif and w_val else ("Encontrado" if ok_unif else "No encontrado")])
        ad_vals.append([v_val])

        # VISAS → AE, AF
        h_val, k_val, ok_vis = buscar_visas(idm, nam, lk_vis_id, lk_vis_name)
        ae_vals.append([h_val if ok_vis and h_val else ("Encontrado" if ok_vis else "No encontrado")])
        af_vals.append([k_val])

        # IMPORT → AG, AH
        d_val, f_val, ok_imp = buscar_import(idm, nam, lk_imp_id, lk_imp_name)
        ag_vals.append([d_val if ok_imp and d_val else ("Encontrado" if ok_imp else "No encontrado")])
        ah_vals.append([f_val])

        # OPEN DATE → AK
        od_val, ok_od = buscar_open_date(idm, nam, lk_od_id, lk_od_name)
        ak_vals.append([od_val if ok_od else "No encontrado"])

    updates = [
        {"range":f"AC2:AC{n+1}", "values":ac_vals},
        {"range":f"AD2:AD{n+1}", "values":ad_vals},
        {"range":f"AE2:AE{n+1}", "values":ae_vals},
        {"range":f"AF2:AF{n+1}", "values":af_vals},
        {"range":f"AG2:AG{n+1}", "values":ag_vals},
        {"range":f"AH2:AH{n+1}", "values":ah_vals},
        {"range":f"AK2:AK{n+1}", "values":ak_vals},
    ]

    batch_update(sh, updates, chunk=6)
    print("✔ Postprocesos completados")
    print("✔ AC–AH–AK actualizados correctamente")

# ============================================================
# MAIN
# ============================================================
def main():
    print("🚀 INICIANDO PROCESO…")

    df_raw = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    df_clean = limpiar_csv_como_original(df_raw)

    col65    = df_raw.iloc[:,64]
    col_form = df_clean["ID Cliente (short text)"]

    id_cliente = [
        limpiar_id(a) if str(a).strip() else limpiar_id(b)
        for a,b in zip(col_form, col65)
    ]

    sh = client.open_by_url(MASTER_URL)
    ws = sh.worksheet(MASTER_TAB)

    all_vals = ws.get_all_values() or [[]]
    header_sheet = all_vals[0]
    header_csv   = list(df_clean.columns)

    # Agregar columnas nuevas si hay en el CSV
    faltantes = [c for c in header_csv if c not in header_sheet]
    if faltantes:
        ws.update("A1", [header_sheet + faltantes])
        header_sheet += faltantes

    # CARGA INICIAL
    if len(all_vals) <= 1:
        print("📌 Carga inicial detectada…")

        columnas = ["ID"] + header_csv
        ws.update("A1", [columnas])

        valores = []
        for i,row in enumerate(df_clean.values.tolist()):
            cid = id_cliente[i]
            try: cid = int(cid) if cid else ""
            except: pass
            valores.append([cid] + row)

        ws.update(
            f"A2:{num_to_col(len(columnas))}{len(valores)+1}",
            valores
        )

        aplicar_postprocesos(sh, ws, [columnas] + valores)
        print("🎯 CARGA INICIAL COMPLETADA")
        return

    print("📌 Actualizando filas existentes…")

    def pad(r,n): return r + [""]*(n-len(r)) if len(r)<n else r[:n]
    data_rows = [pad(r, len(header_sheet)) for r in all_vals[1:]]

    header_map = {h:i for i,h in enumerate(header_sheet)}
    id_idx     = header_map["ID"]
    task_idx   = header_map["Task Name"]

    mapa = {
        (limpiar_id(r[id_idx]), r[task_idx].strip()): i+2
        for i,r in enumerate(data_rows)
    }

    updates = []
    nuevos  = []

    print("📌 Revisando filas del CSV…")

    for i,f in enumerate(tqdm(df_clean.to_dict("records"),
                              desc="Actualizando filas existentes",
                              unit="fila")):

        cid = id_cliente[i]
        tsk = f.get("Task Name", "")
        key = (cid.strip(), tsk.strip())

        if key in mapa:
            fila_sheet = mapa[key]
            old = data_rows[fila_sheet-2]

            start = 3
            seg = []
            for c in range(start-1, len(header_sheet)):
                hn  = header_sheet[c]
                val = f.get(hn, old[c])
                if hn in DATE_COLUMNS:
                    val = convertir_fecha_ddmmaaaa(val)
                seg.append(val)

            updates.append({
                "range": f"{num_to_col(start)}{fila_sheet}:{num_to_col(start+len(seg)-1)}{fila_sheet}",
                "values":[seg]
            })

            data_rows[fila_sheet-2][start-1:] = seg

        else:
            nuevos.append(i)

    if updates:
        print(f"⬆ Subiendo {len(updates)} actualizaciones…")
        batch_update(sh, updates)

    if nuevos:
        nuevas = []
        for idx in nuevos:
            fila = df_clean.iloc[idx].tolist()
            cid  = id_cliente[idx]
            try: cid = int(cid) if cid else ""
            except: pass
            nuevas.append([cid] + fila)

        first = len(data_rows) + 2
        ws.update(
            f"A{first}:{num_to_col(len(header_sheet))}{first+len(nuevas)-1}",
            nuevas
        )

        for nf in nuevas:
            data_rows.append(pad(nf, len(header_sheet)))

        print(f"➕ Nuevas filas agregadas: {len(nuevos)}")

    aplicar_postprocesos(sh, ws, [header_sheet] + data_rows)

    print("🎯 PROCESO COMPLETO ✓")

if __name__ == "__main__":
    main()
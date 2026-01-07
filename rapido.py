import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import time
import re
import os

# --- CONFIGURACIÓN ---
ARCHIVO_CREDENCIALES = 'credentials.json'
ID_SHEET_B = "10QLymtnKfgTHSrtgvREI_ht4xJB1WY7s1BgBAqyf9x0"
# Ruta al archivo que generaste con R
RUTA_CSV_LIMPIO = "/home/ortega/Descargas/datos_limpios_para_python.csv" 

def autenticar_google_sheets(json_keyfile):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    return gspread.authorize(creds)

def limpiar_texto_header(texto):
    if not isinstance(texto, str): return str(texto)
    # Quita puntos, espacios y lo hace minúscula
    return re.sub(r'[^a-zA-Z0-9]', '', texto).lower()

def estandarizar_headers(df):
    # Definimos cómo queremos que se llamen las columnas en nuestro código
    # Clave = Nombre que usaremos en el código ("Atty Fees")
    # Valor = Cómo se ve el texto al limpiarlo (sin espacios ni puntos: "attyfees")
    mapa_objetivo = {
        "Client.name": "clientname",
        "Atty Fees": "attyfees" 
    }
    
    nuevos_nombres = {}
    for col_actual in df.columns:
        col_limpia = limpiar_texto_header(col_actual)
        
        for nombre_estandar, meta_limpia in mapa_objetivo.items():
            if col_limpia == meta_limpia:
                nuevos_nombres[col_actual] = nombre_estandar
                break
    
    if nuevos_nombres:
        df = df.rename(columns=nuevos_nombres)
        # print(f"  -> Headers normalizados: {nuevos_nombres}") # Descomentar para depurar
    return df

def main():
    print("1. Cargando datos desde CSV local...")
    if not os.path.exists(RUTA_CSV_LIMPIO):
        print(f"Error: No encuentro el archivo {RUTA_CSV_LIMPIO}")
        return

    # Leemos el CSV generado por R. Forzamos todo a string.
    datos_origen = pd.read_csv(RUTA_CSV_LIMPIO, dtype=str).fillna("")
    print(f"   -> Cargados {len(datos_origen)} registros desde el CSV.")

    print("2. Conectando a Google Sheets...")
    try:
        gc = autenticar_google_sheets(ARCHIVO_CREDENCIALES)
    except Exception as e:
        print(f"Error de autenticación: {e}")
        return

    # Esta es la columna exacta como viene en tu CSV de R
    cols_interes = ["Atty Fees"]

    # Agrupamos por hoja destino
    grupos_por_hoja = datos_origen.groupby("sheet_name")
    sh_b = gc.open_by_key(ID_SHEET_B)

    for nombre_hoja_destino, grupo_datos in grupos_por_hoja:
        print(f"\nProcesando hoja destino: '{nombre_hoja_destino}'...")
        
        try:
            # Abrir hoja B
            try:
                ws_b = sh_b.worksheet(nombre_hoja_destino)
            except gspread.WorksheetNotFound:
                print(f"  [!] Hoja no existe. Saltando.")
                continue

            # Leer datos B
            raw_data_b = ws_b.get_all_values()
            if not raw_data_b:
                print("  [!] Hoja vacía.")
                continue
                
            headers = raw_data_b.pop(0)
            df_b = pd.DataFrame(raw_data_b, columns=headers)
            
            # Normalizar headers de B para encontrar "Client.name" y "Atty Fees"
            df_b = estandarizar_headers(df_b)

            # Validaciones
            if "Client.name" not in df_b.columns:
                print(f"  [ERROR] No se encontró columna ID 'Client.name'.")
                continue
            
            # Verificamos si logramos encontrar la columna Atty Fees en la hoja de destino
            if "Atty Fees" not in df_b.columns:
                 print(f"  [AVISO] No se encontró la columna 'Atty Fees' (o variantes) en esta hoja. No se actualizará.")
                 # Si quieres crear la columna si no existe, avísame. Por ahora solo salta.
                 continue

            # --- LÓGICA DE ACTUALIZACIÓN ---
            cambios_realizados = 0
            df_b['Client.name'] = df_b['Client.name'].astype(str)
            
            for index, fila_origen in grupo_datos.iterrows():
                client_id = str(fila_origen['Client.name'])
                
                # Buscamos coincidencias en Sheet B
                mascara = df_b['Client.name'] == client_id
                
                if mascara.any():
                    col = "Atty Fees"
                    
                    # Obtenemos el valor del CSV usando el NOMBRE, no la posición [2]
                    # Esto arregla el Warning y previene errores si el orden cambia
                    valor_nuevo = fila_origen[col]
                    
                    # Actualizamos directamente
                    if pd.notna(valor_nuevo):
                        df_b.loc[mascara, col] = str(valor_nuevo)
                        
                    cambios_realizados += 1
            
            print(f"  Registros actualizados: {cambios_realizados}")

            if cambios_realizados > 0:
                ws_b.clear()
                set_with_dataframe(ws_b, df_b)
                print(f"  -> Guardado en la nube.")
            
            time.sleep(1.5)

        except Exception as e:
            print(f"  [Error] en hoja '{nombre_hoja_destino}': {e}")

    print("\n--- Proceso finalizado ---")

if __name__ == "__main__":
    main()
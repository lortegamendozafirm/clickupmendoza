import pandas as pd
import numpy as np

def analizar_propiedades_base_datos(csv_path):
    df = pd.read_csv(csv_path)
    analisis = []

    for col in df.columns:
        # Calcular estadísticas básicas
        vacias = df[col].isna().sum()
        unicos = df[col].nunique()
        total = len(df)
        
        # Intentar detectar si es fecha
        es_fecha = False
        sample = df[col].dropna().iloc[0] if unicos > 0 else None
        if sample and isinstance(sample, str):
            try:
                # ClickUp suele exportar fechas como timestamps o strings largos
                if any(x in col.lower() for x in ['date', 'created', 'updated', 'deadline']):
                    es_fecha = True
            except: pass

        # Sugerir tipo de dato SQL
        if es_fecha:
            tipo_sql = "TIMESTAMP / DATETIME"
        elif df[col].dtype == 'int64':
            tipo_sql = "INTEGER"
        elif df[col].dtype == 'float64':
            tipo_sql = "NUMERIC / FLOAT"
        elif unicos == 2 and vacias < (total * 0.5): # Posible booleano/checkbox
            tipo_sql = "BOOLEAN"
        else:
            tipo_sql = "VARCHAR / TEXT"

        analisis.append({
            "Columna": col,
            "Tipo Sugerido": tipo_sql,
            "Llenado %": round(((total - vacias) / total) * 100, 2),
            "Variabilidad": unicos
        })

    return pd.DataFrame(analisis)


df_resultado = analizar_propiedades_base_datos("DB_case_assigment.csv")
df_resultado.to_csv("resultado.csv")
print(df_resultado)
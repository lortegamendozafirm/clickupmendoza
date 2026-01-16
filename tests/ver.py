# scripts/test_sheets_connection.py
import sys
import os
import logging

# --- Configuración de Path para importar 'app' ---
# Esto permite importar módulos de la carpeta superior
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Configurar logging para ver errores detallados
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.sheets_service import GoogleSheetsService
from app.config import settings

def test_sheet_write():
    print("="*60)
    print("🧪 PRUEBA DE CONEXIÓN A GOOGLE SHEETS")
    print("="*60)

    # 1. Verificar Configuración
    print(f"📂 Credenciales Path: {settings.google_sheets_credentials_path}")
    print(f"📊 Spreadsheet ID:    {settings.google_sheets_spreadsheet_id}")
    print(f"📑 Sheet Name:        {settings.google_sheets_sheet_name}")
    print(f"✅ Enabled:           {settings.google_sheets_enabled}")
    
    if not settings.google_sheets_enabled:
        print("\n❌ Error: GOOGLE_SHEETS_ENABLED es False en el .env")
        return

    # 2. Instanciar Servicio
    print("\n🔄 Autenticando...")
    try:
        service = GoogleSheetsService()
    except Exception as e:
        print(f"❌ Error crítico al autenticar: {e}")
        print("Tip: Verifica que la ruta al archivo JSON sea correcta.")
        return

    if not service.client:
        print("❌ El cliente no se inicializó (revisa logs arriba).")
        return
    print("✅ Autenticación exitosa.")

    # 3. Datos de Prueba
    test_data = {
        "test_col_1": "Prueba Funcional",
        "test_col_2": "Nexus Legal",
        "test_col_3": "Estado OK",
        "test_col_4": "12345678"
    }

    # Definimos un mapeo manual para la prueba:
    # Columna 1 -> test_col_1
    # Columna 2 -> test_col_2
    # ...
    test_mapping = {
        "test_col_1": 1,
        "test_col_2": 2,
        "test_col_3": 3,
        "test_col_4": 4
    }

    print("\n📝 Intentando escribir fila de prueba...")
    print(f"   Datos: {test_data.values()}")
    
    success = service.write_row(
        data=test_data, 
        field_mapping=test_mapping
    )

    if success:
        print("\n" + "█"*60)
        print("✅ ¡ÉXITO! Se escribió una fila en tu Google Sheet.")
        print("█"*60)
        print("Ve a tu navegador y verifica que aparecieron los datos.")
    else:
        print("\n" + "█"*60)
        print("❌ FALLÓ LA ESCRITURA")
        print("█"*60)
        print("Posibles causas:")
        print("1. El 'client_email' del JSON no tiene permiso de Editor en la Sheet.")
        print("2. El ID de la Sheet en .env es incorrecto.")
        print("3. El nombre de la pestaña (Sheet Name) no coincide exactamente.")

if __name__ == "__main__":
    test_sheet_write()
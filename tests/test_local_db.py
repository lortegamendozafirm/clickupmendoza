import httpx
import hmac
import hashlib
import json
import os
from dotenv import load_dotenv

# Cargar variables del .env para obtener el secreto real
load_dotenv()

# --- CONFIGURACIÓN ---
# URL local donde corre tu API
WEBHOOK_URL = "http://127.0.0.1:8080/webhooks/clickup"

# TU SECRETO LOCAL (Debe coincidir con el que tiene tu .env)
SECRET = os.getenv("CLICKUP_WEBHOOK_SECRET")

# ID de Lista y Campo que tu código espera (para pasar los filtros)
# Ajusta estos valores según tu configuración local para que no sea ignorado
LIST_ID = os.getenv("CLICKUP_LIST_ID", "901409514974") 
TRIGGER_FIELD_NAME = os.getenv("CLICKUP_TRIGGER_CONDICIONAL", "Link Intake")

if not SECRET:
    print("❌ Error: No se encontró CLICKUP_WEBHOOK_SECRET en el entorno.")
    exit(1)

# --- PAYLOAD SIMULADO ---
# Simulamos una estructura real de ClickUp para un evento 'taskUpdated'
payload = {
    "event": "taskUpdated",
    "task_id": "86b8858fw",
    "webhook_id": "7689a16a-a927-4a64-9040-592925577607",
    "history_items": [
        {
            "id": "3497921389647915967",
            "type": 1,
            "date": "1706646738567",
            "field": "custom_field",
            "parent_id": "900302479007",
            "data": {
                "status": "active"
            },
            "source": None,
            "user": {
                "id": 183,
                "username": "Test User",
                "email": "test@example.com",
                "color": "#827718",
                "initials": "TU",
                "profilePicture": None
            },
            "before": None,
            "after": "https://drive.google.com/open?id=123" # Valor simulado del link
        }
    ]
}

def test_local_integration():
    body = json.dumps(payload)
    
    # Generar firma HMAC-SHA256
    signature = hmac.new(
        SECRET.encode('utf-8'), 
        body.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    print(f"🔹 Enviando petición a: {WEBHOOK_URL}")
    print(f"🔹 Firma generada: {signature}")

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }

    try:
        # Enviamos la petición
        response = httpx.post(WEBHOOK_URL, headers=headers, data=body)
        
        print("\n" + "="*40)
        print(f"RESULTADO: {response.status_code}")
        print("="*40)
        print(response.text)

        if response.status_code == 200:
            print("\n✅ ¡ÉXITO! El servidor aceptó la petición.")
            print("👀 Ahora revisa los logs de tu terminal 'uvicorn'.")
            print("   Deberías ver una transacción SQL (INSERT/UPDATE) en la tabla 'leads_cache'.")
        else:
            print(f"\n⚠️ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("   ¿Está corriendo uvicorn?")

if __name__ == "__main__":
    test_local_integration()
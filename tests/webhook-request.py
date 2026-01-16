import os
import hmac
import hashlib
import json
import httpx
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# ================= CONFIGURACIÓN =================
# 1. Obtenemos el secreto del .env
WEBHOOK_SECRET = os.getenv("CLICKUP_WEBHOOK_SECRET")

# 2. Usamos la URL CORTA (la que funcionó en tu curl)
#    Esta URL suele ser más estable para el enrutamiento inmediato
URL_DESTINO = "https://nexus-legal-api-pahip4iobq-uc.a.run.app/webhooks/clickup"

# =================================================

def simular_evento_clickup():
    if not WEBHOOK_SECRET:
        print("❌ Error: No se encontró 'CLICKUP_WEBHOOK_SECRET' en el archivo .env")
        return

    print(f"🚀 Iniciando prueba de conexión hacia: {URL_DESTINO}")
    print(f"🔐 Usando secreto (primeros 5 caracteres): {WEBHOOK_SECRET[:5]}...")

    # Payload simulado (Un evento taskCreated falso)
    payload = {
        "event": "taskCreated",
        "task_id": "prueba_python_env_1",
        "webhook_id": "webhook_test_local",
        "history_items": [],
        "task": {
            "id": "prueba_python_env_1",
            "name": "Tarea de Prueba desde Python",
            "text_content": "Esta es una simulación",
            "status": {
                "status": "to do"
            }
        }
    }

    # Convertir a string JSON
    body = json.dumps(payload)

    # CALCULAR LA FIRMA REAL
    signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'), 
        body.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature 
    }

    print(f"🔑 Firma generada correctamente: {signature[:10]}...")
    print("📡 Enviando petición POST...")

    try:
        response = httpx.post(URL_DESTINO, headers=headers, data=body, timeout=15.0)
        
        print("\n" + "="*40)
        print(f"RESULTADO: {response.status_code}")
        print("="*40)
        print(response.json())
        
        if response.status_code == 200:
            print("\n✅ ¡ÉXITO TOTAL!")
            print("   Tu servidor validó la firma y aceptó el webhook.")
            print("   Ahora puedes ir a ClickUp y crear una tarea real.")
            
        elif response.status_code == 401:
            print("\n❌ Error 401: Firma rechazada.")
            print("   Esto significa que el secreto en tu .env NO ES IGUAL")
            print("   al secreto que está guardado en Google Secret Manager.")
            print("   Revisa que ambos sean idénticos.")

    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    simular_evento_clickup()
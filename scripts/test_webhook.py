import httpx
import hmac
import hashlib
import json
import os

# --- CONFIGURACIÓN DE PRUEBA ---
# 1. La URL de tu servicio en Cloud Run
WEBHOOK_URL = "https://nexus-legal-api-223080314602.us-central1.run.app/webhooks/clickup"

# 2. El secreto que OBTUVISTE al crear el webhook en Mirror DVS
# (Pégalo aquí tal cual te lo dio el script de creación)
SECRET = "BVD5B1POQG6RVV2ZDUUC1NLDXV7S6KHKNMWBIBRR0OQ38NSNOSFBAW48B5JDNH48" 

# 3. Datos falsos para la prueba
payload = {
    "event": "taskUpdated",
    "task_id": "86b86x0pf", # Un ID real o inventado
    "history_items": [],
    "webhook_id": "uncodigo"
}

def test_webhook():
    body = json.dumps(payload)
    
    # Generar la firma HMAC-SHA256
    # ClickUp usa el body tal cual para firmar
    signature = hmac.new(
        SECRET.encode('utf-8'), 
        body.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    print(f"🔹 Enviando petición a: {WEBHOOK_URL}")
    print(f"🔹 Usando Secret: {SECRET[:5]}...")
    print(f"🔹 Firma generada: {signature}")

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }

    try:
        response = httpx.post(WEBHOOK_URL, headers=headers, data=body)
        
        print("\n" + "="*40)
        print(f"RESULTADO: {response.status_code}")
        print("="*40)
        print(response.text)

        if response.status_code == 200:
            print("\n✅ ¡ÉXITO! El secreto es CORRECTO y el servicio lo aceptó.")
        elif response.status_code == 401:
            print("\n❌ FALLO: 'Invalid webhook signature'.")
            print("   El secreto que tiene Cloud Run NO coincide con el que usaste aquí.")
        else:
            print(f"\n⚠️ Otro error: {response.status_code}")

    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    test_webhook()
import hmac
import hashlib
import httpx
import json
from pathlib import Path
import sys

# Agregar el directorio raíz para importar la configuración
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

def send_signed_test_webhook():
    # 1. Configuración de la prueba
    url = "http://127.0.0.1:8080/webhooks/assignments"
    # IMPORTANTE: Usa el secreto de Assignments que está en tu .env
    secret = settings.clickup_webhook_secret_assignments
    
    # 2. El payload que ClickUp enviaría (formato Webhook)
    payload_dict = {
        "task_id": "86b3ena9g",
        "event": "taskUpdated",
        "webhook_id": "test-debug-123"
    }
    
    # Convertir a string exacto (sin espacios extra para que el hash coincida)
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    
    # 3. Generar la firma HMAC-SHA256
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"🔑 Secreto usado: {secret[:5]}***")
    print(f"✍️  Firma generada: {signature}")
    
    # 4. Enviar la petición
    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }
    
    print(f"📡 Enviando POST a {url}...")
    
    try:
        with httpx.Client() as client:
            response = client.post(url, content=payload_json, headers=headers)
            
            print(f"\n📊 Resultado:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error en la conexión: {e}")

if __name__ == "__main__":
    send_signed_test_webhook()
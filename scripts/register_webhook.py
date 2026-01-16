import os
import sys
import httpx
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

# Configuración
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID")
# NOTA: Cambia esto si tu URL de ngrok cambió
WEBHOOK_URL = "https://nexus-legal-api-223080314602.us-central1.run.app/webhooks/clickup"

def register_and_show_secret():
    if not CLICKUP_API_TOKEN or not CLICKUP_LIST_ID:
        print("❌ Error: Falta CLICKUP_API_TOKEN o CLICKUP_LIST_ID en el .env")
        return

    # 1. Obtener Team ID (simplificado)
    headers = {"Authorization": CLICKUP_API_TOKEN, "Content-Type": "application/json"}
    try:
        resp_team = httpx.get("https://api.clickup.com/api/v2/team", headers=headers)
        team_id = resp_team.json()["teams"][0]["id"]
    except Exception as e:
        print(f"❌ Error conectando a ClickUp: {e}")
        return

    # 2. Crear Webhook
    url = f"https://api.clickup.com/api/v2/team/{team_id}/webhook"
    
    payload = {
        "endpoint": WEBHOOK_URL,
        "events": [
            "taskCreated",
            "taskUpdated",
            "taskMoved",
            "taskStatusUpdated"
        ],
        "list_id": int(CLICKUP_LIST_ID)
    }

    print(f"📡 Registrando webhook en lista {CLICKUP_LIST_ID}...")
    
    try:
        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # 3. EXTRAER Y MOSTRAR EL SECRETO
        new_id = data.get("id")
        new_secret = data.get("webhook", {}).get("secret")

        print("\n" + "="*50)
        print("✅ ¡ÉXITO! Webhook creado.")
        print("="*50)
        print(f"🆔  Webhook ID: {new_id}")
        print(f"🔑  SECRET:     {new_secret}")  # <--- ESTO ES LO QUE NECESITAS
        print("="*50)
        print("\n⚠️  ACCIÓN REQUERIDA:")
        print(f"Copia el valor de 'SECRET' y pégalo en tu archivo .env así:")
        print(f'CLICKUP_WEBHOOK_SECRET="{new_secret}"')
        print("\nLuego reinicia tu servidor uvicorn.")

    except httpx.HTTPStatusError as e:
        print(f"❌ Error de ClickUp: {e.response.text}")

if __name__ == "__main__":
    register_and_show_secret()
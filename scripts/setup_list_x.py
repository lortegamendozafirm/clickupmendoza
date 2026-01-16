import os
import httpx
from dotenv import load_dotenv

# Cargar variables (asegúrate de que tu .env esté en la misma carpeta)
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
# Usamos el ID de la Lista X que me diste en el prompt
LIST_ID_X = "901403238634" 
FIELD_TARGET_ID = "3aa46502-0763-42d3-8cb9-71513566e3ae" # El ID que tienes en tu .env

# Tu URL de ngrok/Cloud Run
WEBHOOK_URL = "https://nexus-legal-api-223080314602.us-central1.run.app/webhooks/clickup"

headers = {
    "Authorization": API_TOKEN, 
    "Content-Type": "application/json"
}

def verify_field_and_create_webhook():
    print(f"🔍 1. Analizando campos en la Lista X ({LIST_ID_X})...")
    
    # 1. Verificar si el Campo existe en esta lista
    try:
        url_fields = f"https://api.clickup.com/api/v2/list/{LIST_ID_X}/field"
        resp = httpx.get(url_fields, headers=headers)
        resp.raise_for_status()
        fields = resp.json().get("fields", [])
        
        found = False
        print("\n--- Campos encontrados en Lista X ---")
        for f in fields:
            print(f" > Campo: '{f['name']}' | ID: {f['id']}")
            if f['id'] == FIELD_TARGET_ID:
                found = True
        print("-------------------------------------")

        if found:
            print(f"✅ ¡CONFIRMADO! El campo ID {FIELD_TARGET_ID} existe en la Lista X.")
            print("   Puedes usar el mismo ID en tu .env sin problemas.")
        else:
            print(f"⚠️ ADVERTENCIA: No encontré el ID {FIELD_TARGET_ID} en la Lista X.")
            print("   Revisa la lista de IDs impresa arriba y actualiza tu .env si es necesario.")
            # Preguntar si continuar
            confirm = input("   ¿Quieres continuar creando el webhook de todos modos? (s/n): ")
            if confirm.lower() != 's':
                return

    except Exception as e:
        print(f"❌ Error verificando campos: {e}")
        return

    # 2. Crear Webhook en Lista X
    print(f"\n🚀 2. Creando Webhook en Lista X ({LIST_ID_X})...")
    
    # Obtenemos Team ID primero
    try:
        r_team = httpx.get("https://api.clickup.com/api/v2/team", headers=headers)
        team_id = r_team.json()["teams"][0]["id"]
    except:
        print("❌ Error obteniendo Team ID")
        return

    url_web = f"https://api.clickup.com/api/v2/team/{team_id}/webhook"
    
    payload = {
        "endpoint": WEBHOOK_URL,
        "events": [
            "taskCreated",  # <--- EL IMPORTANTE AHORA
            "taskUpdated"   # <--- Recomendado dejarlo por si editan el campo después de crear
        ],
        "list_id": int(LIST_ID_X)
    }

    try:
        resp_web = httpx.post(url_web, headers=headers, json=payload)
        resp_web.raise_for_status()
        data = resp_web.json()
        
        secret = data.get("webhook", {}).get("secret")
        
        print("\n" + "="*60)
        print("✅ WEBHOOK CREADO EXITOSAMENTE EN LISTA X")
        print("="*60)
        print(f"🆔 Webhook ID: {data.get('id')}")
        print(f"🔑 NUEVO SECRET: {secret}")
        print("="*60)
        print("\n⚠️ IMPORTANTE: Actualiza tu archivo .env:")
        print(f'1. Cambia CLICKUP_LIST_ID="{LIST_ID_X}"')
        print(f'2. Cambia CLICKUP_WEBHOOK_SECRET="{secret}"')
        
    except httpx.HTTPStatusError as e:
        print(f"❌ Error creando webhook: {e.response.text}")

if __name__ == "__main__":
    verify_field_and_create_webhook()
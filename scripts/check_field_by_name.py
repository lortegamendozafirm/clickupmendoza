import os
import httpx
from dotenv import load_dotenv

# Cargar variables (asegúrate de que tu .env esté en la misma carpeta)
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
# Usamos el ID de la Lista X que me diste en el prompt
LIST_ID_X = "901407053200" 
FIELD_TARGET_ID = "Link Intake" # El ID que tienes en tu .env

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
            if f['name'] == FIELD_TARGET_ID:
                found = True
        print("-------------------------------------")

        if found:
            print(f"✅ ¡CONFIRMADO! El campo ID {FIELD_TARGET_ID} existe en la Lista X.")
            print("   Puedes usar el mismo ID en tu .env sin problemas.")
        else:
            print(f"⚠️ ADVERTENCIA: No encontré el ID {FIELD_TARGET_ID} en la Lista X.")
            print("   Revisa la lista de IDs impresa arriba y actualiza tu .env si es necesario.")

    except Exception as e:
        print(f"❌ Error verificando campos: {e}")
        return


if __name__ == "__main__":
    verify_field_and_create_webhook()
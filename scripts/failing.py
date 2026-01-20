import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("CLICKUP_API_TOKEN")

def list_webhooks():
    if not API_TOKEN:
        print("❌ Falta CLICKUP_API_TOKEN")
        return

    headers = {"Authorization": API_TOKEN}
    
    # 1. Obtener Team ID
    try:
        r = httpx.get("https://api.clickup.com/api/v2/team", headers=headers)
        team_id = r.json()["teams"][0]["id"]
    except:
        print("❌ Error conectando a ClickUp")
        return

    # 2. Listar Webhooks
    print(f"🔍 Buscando webhooks para el equipo {team_id}...\n")
    url = f"https://api.clickup.com/api/v2/team/{team_id}/webhook"
    
    try:
        resp = httpx.get(url, headers=headers)
        webhooks = resp.json().get("webhooks", [])
        
        if not webhooks:
            print("⚠️ No se encontraron webhooks.")
            return

        for w in webhooks:
            print("-" * 50)
            print(f"🆔 ID:       {w['id']}")
            print(f"📋 User:     {w['userid']}")
            print(f"🔗 Endpoint: {w['endpoint']}")
            print(f"🚦 Status:   {w['status']}  <-- ¡REVISA ESTO!")
            
            # Verificamos errores de salud
            health = w.get("health", {})
            if health.get("fail_count", 0) > 0:
                print(f"❌ FAILS:    {health['fail_count']} errores recientes")
            
            # Verificamos eventos
            print(f"📢 Eventos:  {', '.join(w.get('events', []))}")
            
            # Intentamos ver dónde está instalado (List/Folder)
            # Nota: ClickUp no siempre devuelve el resource_id claro en el listado,
            # pero el webhook.id nos sirve para editarlo en la web.
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_webhooks()
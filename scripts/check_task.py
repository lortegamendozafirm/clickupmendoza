import os
import httpx
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")

# Pon aquí el ID de la tarea que estás usando para probar (ej: "86b86m8pu")
TASK_ID = "86b86m9pq" 

def check_task_location():
    headers = {"Authorization": API_TOKEN}
    url = f"https://api.clickup.com/api/v2/task/{TASK_ID}"
    
    try:
        r = httpx.get(url, headers=headers)
        if r.status_code != 200:
            print(f"❌ Error al buscar tarea: {r.status_code}")
            return
            
        task = r.json()
        print(f"🔎 Tarea: {task['name']} ({task['id']})")
        
        # 1. Ver lista principal
        main_list = task['list']
        print(f"🏠 Lista Principal (Home): {main_list['name']} - ID: {main_list['id']}")
        
        # 2. Ver ubicación de webhook
        # Pon aquí el ID de la lista donde registraste el webhook
        WEBHOOK_LIST_ID = "901403238634" 
        
        if main_list['id'] == WEBHOOK_LIST_ID:
            print("✅ La tarea VIVE en la lista del webhook.")
        else:
            print("⚠️ La tarea NO vive en la lista del webhook.")
            
        # 3. Ver Listas Espejo (Locations)
        # ClickUp a veces guarda esto en 'locations' o hay que deducirlo
        print("\n--- Verificando si el webhook debería dispararse ---")
        if main_list['id'] != WEBHOOK_LIST_ID:
             print(f"❌ PROBLEMA DETECTADO: El webhook está en la lista {WEBHOOK_LIST_ID},")
             print(f"   pero la tarea pertenece a la lista {main_list['id']}.")
             print("   Si no es una lista espejo, el webhook NO se activará.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_task_location()
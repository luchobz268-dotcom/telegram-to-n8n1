from telethon import TelegramClient, events
import requests
import os
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime, timezone
import logging

# Desactivar logs innecesarios de Telethon y Flask
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ========== CONFIGURACIÓN ==========
# ⚙️ Asegúrate de que estos valores sean correctos
api_id = 26799526
api_hash = "f530ea8cb15150cc6f866879d751e50c"
channel_username = "pronosticosfutbol365"
webhook_url = "https://n8n-sozl.onrender.com/webhook-test/telegram-message"
session_name = "session_name"

# Configuración del servidor web (Hack para Render Free Tier)
WEB_HOST = '0.0.0.0'
# Render inyectará el puerto en la variable de entorno PORT, si no, usa 8080
WEB_PORT = int(os.environ.get("PORT", 8080)) 

app = Flask(__name__)

# ===================================

@app.route('/')
def home():
    """Endpoint simple para responder al 'ping' externo y evitar el sueño."""
    return "Telegram Bot is running! Status: OK"

# ===================================

client = TelegramClient(session_name, api_id, api_hash)

# ===================================

@client.on(events.NewMessage(chats=channel_username))
async def new_message_handler(event):
    """Captura cada nuevo mensaje y lo envía a tu webhook de n8n."""
    try:
        message = event.message
        text = message.message or ""
        has_media = bool(message.media)
        
        payload = {
            "text": text,
            "has_media": has_media,
            "media_type": type(message.media).__name__ if has_media else None,
            "is_history": False # Indica que es un mensaje nuevo, no del historial
        }

        print(f"📩 Nuevo mensaje detectado: {text[:60]}...")
        
        # Enviar al webhook n8n
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"✅ Enviado a webhook (status {response.status_code})")

    except Exception as e:
        print(f"❌ Error procesando mensaje nuevo: {e}")

# ===================================

async def get_history_and_send():
    """Busca mensajes desde la medianoche de hoy y los envía a n8n."""
    
    # Define la hora de medianoche de hoy en UTC (esencial para Telethon)
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"⏳ Buscando historial desde: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Obtiene mensajes posteriores a la medianoche (máx 100 mensajes, si necesitas más, modifica 'limit')
    messages = await client.get_messages(
        channel_username, 
        offset_date=start_of_day, 
        reverse=True 
    )

    if not messages:
        print("✅ No se encontraron mensajes anteriores hoy.")
        return

    print(f"📦 Encontrados {len(messages)} mensajes. Enviando historial...")
    
    for message in messages:
        try:
            payload = {
                "text": message.message or "",
                "has_media": bool(message.media),
                "media_type": type(message.media).__name__ if message.media else None,
                "is_history": True # Indica que es un mensaje del historial
            }
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"❌ Error al enviar mensaje histórico: {e}")
            
    print("✅ Historial de mensajes de hoy procesado.")

# ===================================
# --- FUNCIONES DE INICIO Y DEPLOY ---
# ===================================

def run_flask():
    """Ejecuta el servidor Flask en un Thread para no bloquear Asyncio."""
    print(f"🌐 Iniciando servidor web en puerto {WEB_PORT} para evitar el sueño...")
    # Ejecutamos Flask en un hilo de Python (Thread) para correr en paralelo con Telethon
    Thread(target=app.run, kwargs={'host': WEB_HOST, 'port': WEB_PORT}).start()

async def run_telethon_and_history():
    """Función asíncrona principal: Inicia cliente, busca historial y se queda escuchando."""
    
    print("🚀 Conectando cliente Telegram...")
    await client.start()

    # 1. Ejecutar la función asíncrona de historial
    await get_history_and_send()
    
    # 2. Escuchar nuevos mensajes indefinidamente
    print("👂 Escuchando nuevos mensajes del canal...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # 1. Iniciamos el servidor Flask en un hilo separado
    run_flask()

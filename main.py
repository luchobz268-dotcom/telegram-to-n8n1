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

# ========== 1. CONFIGURACIÓN ==========
# ⚙️ Asegúrate de que estos valores sean correctos
api_id = 26799526
api_hash = "f530ea8cb15150cc6f866879d751e50c"
channel_username = "pronosticosfutbol365"
# URL de n8n para el modo de prueba
webhook_url = "https://n8n-sozl.onrender.com/webhook-test/telegram-message" 
session_name = "session_name" # Debe coincidir con el nombre de tu archivo .session

# Configuración del servidor web (Hack para Render Free Tier)
WEB_HOST = '0.0.0.0'
WEB_PORT = int(os.environ.get("PORT", 8080)) 

app = Flask(__name__)
client = TelegramClient(session_name, api_id, api_hash)

# ===================================
# --- 2. ENDPOINT WEB (ANTI-SUEÑO) ---
# ===================================

@app.route('/')
def home():
    """Endpoint simple para responder al 'ping' externo y evitar el sueño."""
    return "Telegram Bot is running! Status: OK"

# ===================================
# --- 3. MANEJADOR DE MENSAJES NUEVOS ---
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
            "is_history": False 
        }

        print(f"📩 Nuevo mensaje detectado: {text[:60]}...")
        
        # Enviar al webhook n8n
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"✅ Enviado a webhook (status {response.status_code})")

    except Exception as e:
        print(f"❌ Error procesando mensaje nuevo: {e}")

# ===================================
# --- 4. FUNCIÓN PARA EL HISTORIAL ---
# ===================================

async def get_history_and_send():
    """Busca mensajes desde la medianoche de hoy y los envía a n8n."""
    
    # Define la hora de medianoche de hoy en UTC
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"⏳ Buscando historial desde: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Obtiene mensajes posteriores a la medianoche
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
                "is_history": True
            }
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"❌ Error al enviar mensaje histórico: {e}")
            
    print("✅ Historial de mensajes de hoy procesado.")

# ===================================
# --- 5. INICIO DEL PROGRAMA ---
# ===================================

def run_flask_thread():
    """Ejecuta el servidor Flask en un Thread para el anti-sueño."""
    print(f"🌐 Iniciando servidor web en puerto {WEB_PORT} para evitar el sueño...")
    Thread(target=app.run, kwargs={'host': WEB_HOST, 'port': WEB_PORT}).start()

def start_bot():
    """Conecta el cliente, procesa historial y se queda escuchando."""
    
    print("🚀 Conectando cliente Telegram...")
    
    try:
        # 1. Conecta el cliente de forma síncrona
        client.start()
    except Exception as e:
        # Si falla, informa del error de sesión y detiene la ejecución
        print(f"❌ ERROR AL INICIAR SESIÓN: Verifica el archivo session_name.session. Error: {e}")
        return 

    # 2. Ejecuta el historial 
    print("⏳ Procesando historial de mensajes...")
    client.loop.run_until_complete(get_history_and_send())
    
    # 3. Escucha nuevos mensajes
    print("👂 Escuchando nuevos mensajes del canal...")
    client.run_until_disconnected()

if __name__ == '__main__':
    # El servidor web y el bot se ejecutan en hilos separados
    run_flask_thread()
    start_bot()

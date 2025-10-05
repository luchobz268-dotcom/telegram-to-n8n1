from telethon import TelegramClient, events
import requests
import os
import asyncio
from flask import Flask
from threading import Thread

# ========== CONFIGURACIÓN ==========
# ⚙️ Estos datos se mantienen sin cambios
api_id = 26799526
api_hash = "f530ea8cb15150cc6f866879d751e50c"
channel_username = "pronosticosfutbol365"
webhook_url = "https://n8n-sozl.onrender.com/webhook/telegram-message"
session_name = "session_name"

# Configuración del servidor web (Render Free Tier)
WEB_HOST = '0.0.0.0'
# Render inyectará el puerto en la variable de entorno PORT
WEB_PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)

@app.route('/')
def home():
    """Endpoint simple para responder al 'ping' externo."""
    return "Telegram Bot is running! Status: OK"

# ===================================

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=channel_username))
async def handler(event):
    """Captura cada nuevo mensaje del canal y lo envía a tu webhook."""
    try:
        message = event.message
        text = message.message or ""
        has_media = bool(message.media)
        media_type = type(message.media).__name__ if has_media else None

        payload = {
            "text": text,
            "has_media": has_media,
            "media_type": media_type
        }

        print(f"📩 Nuevo mensaje detectado: {text[:60]}...")
        
        # Enviar al webhook n8n
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"✅ Enviado a webhook (status {response.status_code})")

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

# =============================

def run_telethon():
    """Función síncrona para iniciar el cliente Telethon."""
    print("🚀 Escuchando el canal @pronosticosfutbol365...")
    client.start()
    client.run_until_disconnected()

def run_flask():
    """Función para iniciar el servidor Flask."""
    print(f"🌐 Iniciando servidor web en puerto {WEB_PORT} para evitar el sueño...")
    # Usamos Threading para no bloquear la ejecución del cliente Telethon
    Thread(target=app.run, kwargs={'host': WEB_HOST, 'port': WEB_PORT}).start()

if __name__ == '__main__':
    # 1. Iniciamos el servidor Flask en un hilo separado
    run_flask()
    
    # 2. Iniciamos el cliente Telethon en el hilo principal
    run_telethon()

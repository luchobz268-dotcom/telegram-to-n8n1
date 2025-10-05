from telethon import TelegramClient, events
import requests
import os

# ========== CONFIGURACIÓN ==========
# ⚙️ Consigue estos datos en https://my.telegram.org
api_id = 26799526  # Tu API ID
api_hash = "f530ea8cb15150cc6f866879d751e50c"  # Tu API HASH

# Canal a monitorear
channel_username = "pronosticosfutbol365"  # sin @ adelante

# Webhook de n8n donde se enviarán los mensajes
webhook_url = "https://n8n-sozl.onrender.com/webhook/telegram-message" # ¡WEBHOOK FINAL ACTUALIZADO!

# Nombre del archivo de sesión (se genera al iniciar sesión la primera vez)
session_name = "session_name"

# ===================================

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=channel_username))
async def handler(event):
    """Captura cada nuevo mensaje del canal y lo envía a tu webhook."""
    try:
        message = event.message

        # Texto principal
        text = message.message or ""

        # Si hay medios (fotos, videos, documentos)
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
print("🚀 Escuchando el canal @pronosticosfutbol365...")
client.start()
client.run_until_disconnected()

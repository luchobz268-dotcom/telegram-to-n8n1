from telethon import TelegramClient, events
import requests

# 🔧 CONFIGURA TUS DATOS
api_id = 12345678  # Tu API ID desde https://my.telegram.org
api_hash = 'tu_api_hash'
channel_username = 'nombre_del_canal'  # puede ser @nombre o ID numérico
webhook_url = 'https://tuinstancia.n8n.cloud/webhook/telegram-message'  # tu webhook n8n

# Inicia cliente
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=channel_username))
async def handler(event):
    text = event.message.message or ""
    print(f"Nuevo mensaje detectado: {text}")
    try:
        requests.post(webhook_url, json={"text": text})
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

client.start()
print("🟢 Escuchando canal de Telegram...")
client.run_until_disconnected()

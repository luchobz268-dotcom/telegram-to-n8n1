from telethon import TelegramClient, events
import asyncio
import json
import os
import requests
from datetime import datetime, timedelta
from flask import Flask
import threading

# === CONFIGURACIÓN ===
API_ID = int(os.getenv('TELEGRAM_API_ID', '26799526'))
API_HASH = os.getenv('TELEGRAM_API_HASH', 'f530ea8cb15150cc6f866879d751e50c')
SESSION_STRING = os.getenv('TELEGRAM_SESSION', '')

CANAL_ORIGEN = os.getenv('CANAL_ORIGEN', '@pronosticosfutbol365')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://n8n-sozl.onrender.com/webhook-test/telegram-message')
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '5493515997253')
DIAS_HISTORICOS = int(os.getenv('DIAS_HISTORICOS', '7'))

PORT = int(os.getenv('PORT', '10000'))
ARCHIVO_ENVIADOS = 'mensajes_enviados.json'

# === VALIDACIÓN ===
if not API_ID or not API_HASH or not SESSION_STRING:
    print("🔴 ERROR: Faltan variables requeridas:")
    print(f"  TELEGRAM_API_ID: {'✓' if API_ID else '✗'}")
    print(f"  TELEGRAM_API_HASH: {'✓' if API_HASH else '✗'}")
    print(f"  TELEGRAM_SESSION: {'✓' if SESSION_STRING else '✗'}")
    print("\n💡 Genera la sesión con generate_session.py")
    exit(1)

# === FLASK ===
app = Flask(__name__)

@app.route('/')
def home():
    return {'status': 'running', 'canal': CANAL_ORIGEN}

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# === CLIENTE TELEGRAM CON SESSION STRING ===
from telethon.sessions import StringSession
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# === FUNCIONES ===
def cargar_enviados():
    if os.path.exists(ARCHIVO_ENVIADOS):
        try:
            with open(ARCHIVO_ENVIADOS, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def guardar_enviado(message_id):
    enviados = cargar_enviados()
    enviados.add(message_id)
    if len(enviados) > 1000:
        enviados = set(list(enviados)[-1000:])
    with open(ARCHIVO_ENVIADOS, 'w') as f:
        json.dump(list(enviados), f)

def enviar_a_n8n(mensaje_data):
    if not N8N_WEBHOOK_URL:
        print(f"📝 {mensaje_data['text'][:100] if mensaje_data['text'] else '[Media]'}")
        return True
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=mensaje_data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error n8n: {e}")
        return False

def preparar_mensaje(message):
    return {
        'message_id': message.id,
        'date': message.date.isoformat(),
        'text': message.text or '',
        'whatsapp_number': WHATSAPP_NUMBER,
        'sender_id': message.sender_id,
        'has_media': message.media is not None,
        'media_type': 'photo' if message.photo else 'video' if message.video else None
    }

async def procesar_mensaje(message, es_historico=False):
    enviados = cargar_enviados()
    if message.id in enviados:
        return False
    
    try:
        if enviar_a_n8n(preparar_mensaje(message)):
            guardar_enviado(message.id)
            tipo = "histórico" if es_historico else "nuevo"
            texto = message.text[:50] if message.text else '[Media]'
            print(f"✓ {tipo}: {texto}...")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
    return False

@client.on(events.NewMessage(chats=CANAL_ORIGEN))
async def nuevo_mensaje(event):
    await procesar_mensaje(event.message, False)

async def procesar_historico():
    fecha_limite = datetime.now() - timedelta(days=DIAS_HISTORICOS)
    print(f"\n📜 Revisando últimos {DIAS_HISTORICOS} días...")
    
    enviados = 0
    async for message in client.iter_messages(CANAL_ORIGEN):
        if message.date < fecha_limite:
            break
        if await procesar_mensaje(message, True):
            enviados += 1
            await asyncio.sleep(0.5)
    
    print(f"✓ Histórico: {enviados} mensajes\n")

async def main():
    print("🤖 TELEGRAM → N8N → WHATSAPP")
    print(f"📥 Canal: {CANAL_ORIGEN}")
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    await client.start()
    print("✓ Conectado")
    
    await procesar_historico()
    print("⏳ Esperando mensajes...\n")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

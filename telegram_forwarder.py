from telethon import TelegramClient, events
import asyncio
import json
import os
import requests
from datetime import datetime, timedelta

# === CONFIGURACIÓN DESDE VARIABLES DE ENTORNO ===
API_ID = int(os.getenv('TELEGRAM_API_ID', '26799526'))
API_HASH = os.getenv('TELEGRAM_API_HASH', 'f530ea8cb15150cc6f866879d751e50c')
PHONE = os.getenv('TELEGRAM_PHONE', '+5493515997253')

# Canal de origen
CANAL_ORIGEN = os.getenv('CANAL_ORIGEN', '@pronosticosfutbol365')

# Webhook de n8n
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://n8n-sozl.onrender.com/webhook-test/telegram-message')

# Días de historial a revisar
DIAS_HISTORICOS = int(os.getenv('DIAS_HISTORICOS', '7'))

# Archivo para control de duplicados
ARCHIVO_ENVIADOS = 'mensajes_enviados.json'

# === CLIENTE TELEGRAM ===
client = TelegramClient('sesion_telegram', API_ID, API_HASH)

# === CONTROL DE DUPLICADOS ===
def cargar_enviados():
    """Carga la lista de IDs de mensajes ya enviados"""
    if os.path.exists(ARCHIVO_ENVIADOS):
        try:
            with open(ARCHIVO_ENVIADOS, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def guardar_enviado(message_id):
    """Guarda un ID de mensaje como ya enviado"""
    enviados = cargar_enviados()
    enviados.add(message_id)
    # Mantener solo los últimos 1000 IDs
    if len(enviados) > 1000:
        enviados = set(list(enviados)[-1000:])
    with open(ARCHIVO_ENVIADOS, 'w') as f:
        json.dump(list(enviados), f)

def enviar_a_n8n(mensaje_data):
    """Envía el mensaje a n8n vía webhook"""
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=mensaje_data,
            timeout=10
        )
        if response.status_code == 200:
            return True
        else:
            print(f"✗ n8n respondió con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error al enviar a n8n: {e}")
        return False

def preparar_mensaje(message):
    """Prepara el mensaje en formato JSON para n8n"""
    data = {
        'message_id': message.id,
        'date': message.date.isoformat(),
        'text': message.text or '',
        'sender': message.sender_id,
        'chat': CANAL_ORIGEN,
        'has_media': message.media is not None,
        'media_type': None,
        'file_url': None
    }
    
    # Detectar tipo de media
    if message.photo:
        data['media_type'] = 'photo'
    elif message.video:
        data['media_type'] = 'video'
    elif message.document:
        data['media_type'] = 'document'
    elif message.audio:
        data['media_type'] = 'audio'
    
    return data

async def procesar_mensaje(message, es_historico=False):
    """Procesa y envía un mensaje a n8n"""
    enviados = cargar_enviados()
    
    # Verificar si ya fue enviado
    if message.id in enviados:
        if not es_historico:
            print(f"⊘ Mensaje {message.id} ya enviado")
        return False
    
    try:
        # Preparar datos del mensaje
        mensaje_data = preparar_mensaje(message)
        
        # Enviar a n8n
        if enviar_a_n8n(mensaje_data):
            guardar_enviado(message.id)
            
            tipo = "histórico" if es_historico else "nuevo"
            texto_preview = message.text[:50] if message.text else "[Media]"
            print(f"✓ Mensaje {tipo} enviado a n8n: {texto_preview}...")
            return True
        else:
            print(f"✗ No se pudo enviar mensaje {message.id} a n8n")
            return False
            
    except Exception as e:
        print(f"✗ Error al procesar mensaje {message.id}: {e}")
        return False

@client.on(events.NewMessage(chats=CANAL_ORIGEN))
async def nuevo_mensaje(event):
    """Detecta nuevos mensajes en tiempo real"""
    await procesar_mensaje(event.message, es_historico=False)

async def procesar_historico():
    """Procesa mensajes de los últimos N días"""
    fecha_limite = datetime.now() - timedelta(days=DIAS_HISTORICOS)
    
    print(f"\n📜 Revisando mensajes de los últimos {DIAS_HISTORICOS} días...")
    print(f"   (desde {fecha_limite.strftime('%d/%m/%Y %H:%M')})")
    
    enviados = 0
    omitidos = 0
    revisados = 0
    
    try:
        async for message in client.iter_messages(CANAL_ORIGEN):
            revisados += 1
            
            if message.date < fecha_limite:
                break
            
            if await procesar_mensaje(message, es_historico=True):
                enviados += 1
                await asyncio.sleep(0.5)
            else:
                omitidos += 1
        
        print(f"\n✓ Historial procesado:")
        print(f"  - Enviados a n8n: {enviados}")
        print(f"  - Omitidos: {omitidos}")
        print(f"  - Revisados: {revisados}\n")
        
    except Exception as e:
        print(f"✗ Error en procesamiento histórico: {e}")

async def main():
    """Función principal"""
    print("=" * 60)
    print("🤖 BOT TELEGRAM → N8N → WHATSAPP")
    print("=" * 60)
    print(f"📥 Canal origen: {CANAL_ORIGEN}")
    print(f"🔗 Webhook n8n: {N8N_WEBHOOK_URL}")
    print(f"📅 Días históricos: {DIAS_HISTORICOS}")
    print(f"💾 Control duplicados: {ARCHIVO_ENVIADOS}")
    print("=" * 60)
    
    # Iniciar cliente
    await client.start(phone=PHONE)
    print("\n✓ Cliente Telegram conectado")
    
    # Procesar mensajes históricos
    await procesar_historico()
    
    print("⏳ Escuchando nuevos mensajes...")
    print("Presiona Ctrl+C para detener\n")
    
    # Mantener activo
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido por el usuario")
    except Exception as e:
        print(f"\n✗ Error crítico: {e}")

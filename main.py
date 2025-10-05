# Asegúrate de que estas líneas estén al inicio de tu main.py:
from telethon import TelegramClient, events
# ... (otras importaciones) ...
from datetime import datetime, timezone 
import asyncio
# ... (resto de tu código) ...

# -------------------------------------------------------------
# Nueva función asíncrona para manejar el historial
# -------------------------------------------------------------
async def get_history_and_send():
    """Busca mensajes desde la medianoche de hoy y los envía a n8n."""
    
    # Define la hora de medianoche de hoy en UTC (esencial para Telethon)
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"⏳ Buscando historial desde: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Obtiene mensajes posteriores a la medianoche
    messages = await client.get_messages(
        channel_username, 
        offset_date=start_of_day, 
        reverse=True # Procesar en orden correcto (más viejo a más nuevo)
    )

    if not messages:
        print("✅ No se encontraron mensajes anteriores hoy.")
        return

    print(f"📦 Encontrados {len(messages)} mensajes. Enviando...")
    
    for message in messages:
        # Lógica de envío simplificada
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


# -------------------------------------------------------------
# Modificación de la función principal de inicio (run_telethon)
# -------------------------------------------------------------
def run_telethon():
    """Conecta el cliente, procesa el historial y luego escucha nuevos mensajes."""
    print("🚀 Conectando cliente Telegram...")
    client.start() 

    # 1. EJECUTAR EL HISTORIAL (usando el bucle de eventos del cliente)
    client.loop.run_until_complete(get_history_and_send())
    
    # 2. ESCUCHAR NUEVOS MENSAJES
    print("👂 Escuchando nuevos mensajes del canal...")
    client.run_until_disconnected()


# -------------------------------------------------------------
# La sección __main__ debe verse así:
# -------------------------------------------------------------
if __name__ == '__main__':
    # 1. Iniciamos el servidor Flask en un hilo separado para evitar que Render lo duerma
    run_flask()
    
    # 2. Iniciamos el cliente Telethon y el historial en el hilo principal
    run_telethon()

# ... (Código de configuración, Flask, etc.) ...

async def get_history_and_send():
    """Obtiene y procesa todos los mensajes del canal desde el inicio del día."""
    from datetime import datetime, timedelta, timezone
    
    # 1. Definir el punto de inicio (Hoy a las 00:00:00)
    # Usamos UTC para Telethon, que es el estándar
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"⏳ Buscando mensajes desde: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # 2. Consultar el historial de mensajes
    # 'offset_date' le dice a Telethon que solo devuelva mensajes *posteriores* a esta fecha.
    messages = await client.get_messages(
        channel_username, 
        offset_date=start_of_day, 
        reverse=True # Importante: asegura que los procesamos en el orden correcto (del más viejo al más nuevo)
    )

    # 3. Procesar y Enviar
    if not messages:
        print("✅ No se encontraron mensajes anteriores en el historial de hoy.")
        return

    print(f"📦 Encontrados {len(messages)} mensajes anteriores. Procesando...")
    
    for message in messages:
        # Aquí reusamos la lógica de envío del 'handler'
        try:
            text = message.message or ""
            has_media = bool(message.media)
            media_type = type(message.media).__name__ if has_media else None
            
            payload = {
                "text": text,
                "has_media": has_media,
                "media_type": media_type,
                "is_history": True # Flag para n8n, si lo necesitas
            }

            print(f"⬆️ Enviando historial: {text[:40]}...")
            requests.post(webhook_url, json=payload, timeout=10)

        except Exception as e:
            print(f"❌ Error al enviar mensaje histórico: {e}")
            
    print("✅ Historial de mensajes de hoy procesado y enviado.")

# ... (El handler @client.on(events.NewMessage) sigue igual) ...

# Usa una imagen base de Python 3.11 ligera
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos (main.py y session_name.session)
COPY . .

# Comando para ejecutar el bot
CMD ["python3", "main.py"]

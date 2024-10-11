# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos y luego instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servidor en el contenedor
COPY app.py .

# Exponer el puerto 8000 para acceder al servidor
EXPOSE 8000

# Comando para ejecutar la aplicación con uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

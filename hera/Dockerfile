# Usa Ubuntu 22.04 como imagen base
FROM ubuntu:22.04

# Establecer variables de entorno no interactivo para apt
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza el sistema e instala Python, pip, y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    curl \
    poppler-utils && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py

# Instala paquetes básicos de Python
RUN pip install requests

# Si tienes más dependencias en requirements.txt, descomenta estas líneas
# COPY requirements.txt /app/
# RUN pip install -r /app/requirements.txt

# Establece el directorio de trabajo
WORKDIR /app

# Copia todos los archivos y subdirectorios al contenedor
COPY . /app/

# Ejecuta tu aplicación Python principal
CMD ["python3", "hera.py"]

# Usa Ubuntu 22.04 como imagen base
FROM ubuntu:22.04

# Establecer variables de entorno no interactivo para apt
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza el sistema e instala Python, pip, y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    curl \
    poppler-utils && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos los archivos y subdirectorios al contenedor
COPY . /app/

# Define las variables de entorno necesarias
ENV WORKSPACE=tu_workspace
ENV API_KEY=tu_api_key

# Ejecuta tu aplicación Python principal
CMD ["python3", "app/hera.py"]

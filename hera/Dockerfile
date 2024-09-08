# Usa Ubuntu 22.04 como imagen base
FROM ubuntu:22.04

# Establecer variables de entorno no interactivo para apt
ENV DEBIAN_FRONTEND=noninteractive

# Instala Python 3.10 y pip
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    curl && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py

# Instala paquetes básicos de Python
RUN pip install requests

WORKDIR /app

# Copia el archivo hera.py al contenedor
COPY hera.py .

# Ejecuta tu aplicación Python
CMD ["python3", "hera.py"]
# Usa la imagen base de Ubuntu 22.04
FROM ubuntu:22.04

# Establece variables de entorno no interactivas (para evitar prompts durante la instalación)
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza el sistema, instala dependencias y limpia el cache en un solo paso
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    wget \
    netcat \
    build-essential \
    libssl-dev \
    libcurl4-openssl-dev \
    zlib1g-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instala Ollama usando el script oficial
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copia el script entrypoint.sh al contenedor y da permisos de ejecución
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Exponer el puerto para Ollama (puerto predeterminado 11434)
EXPOSE 11434

# Usar el entrypoint personalizado
CMD ["/usr/local/bin/entrypoint.sh"]

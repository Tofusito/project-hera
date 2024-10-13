#!/bin/bash

set -ex

ollama serve &

# Función para descargar un modelo si no está presente
download_model() {
    if ! ollama list | grep -q "$1"; then
        echo "Descargando $1..."
        ollama pull "$1"
    else
        echo "El modelo $1 ya está presente."
    fi
}

# Descargar modelos en paralelo
download_model "$OLLAMA_MODEL" &
download_model "$OLLAMA_MODEL_EMBED" &
download_model "$OLLAMA_MODEL_CODE" &

# Esperar a que terminen todas las tareas en segundo plano
wait

# Fin del script

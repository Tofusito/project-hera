#!/bin/bash

set -x

ollama serve &

# Descargar los modelos si no están presentes
if ! ollama list | grep -q "ollama run $OLLAMA_MODEL"; then
  echo "Descargando $OLLAMA_MODEL..."
  ollama pull $OLLAMA_MODEL
else
  echo "El modelo $OLLAMA_MODEL ya está presente."
fi

if ! ollama list | grep -q "nomic-embed-text"; then
  echo "Descargando nomic-embed-text..."
  ollama pull nomic-embed-text:v1.5
else
  echo "El modelo nomic-embed-text ya está presente."
fi

# Ejecutar cualquier otro paso necesario aquí...
wait

# Fin del script

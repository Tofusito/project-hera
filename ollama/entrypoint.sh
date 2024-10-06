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

if ! ollama list | grep -q "mxbai-embed-large:latest"; then
  echo "Descargando mxbai-embed-large:latest..."
  ollama pull mxbai-embed-large:latest
else
  echo "El modelo mxbai-embed-large:latest ya está presente."
fi

# Ejecutar cualquier otro paso necesario aquí...
wait

# Fin del script

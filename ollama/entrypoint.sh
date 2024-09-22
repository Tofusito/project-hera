#!/bin/bash

# Descargar los modelos si no están presentes
if ! ollama list | grep -q "llama3.1:8b-instruct-q4_0"; then
  echo "Descargando llama3.1:8b-instruct-q4_0..."
  ollama pull llama3.1:8b-instruct-q4_0
else
  echo "El modelo llama3.1:8b-instruct-q4_0 ya está presente."
fi

if ! ollama list | grep -q "nomic-embed-text"; then
  echo "Descargando nomic-embed-text..."
  ollama pull nomic-embed-text:v1.5
else
  echo "El modelo nomic-embed-text ya está presente."
fi

# Ejecutar cualquier otro paso necesario aquí...

# Fin del script

#!/bin/bash

# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que el servidor esté completamente iniciado
sleep 5

# Descargar el modelo llama3.1:8b-instruct-q4_0
ollama pull llama3.1:8b-instruct-q4_0
ollama pull nomic-embed-text

# Mantener el contenedor corriendo
wait
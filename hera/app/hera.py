# app/main.py

import json
import time
import subprocess
import requests
from services.ollama_service import OllamaService
from services.anythingllm_service import AnythingLLMService
from converters.converter import Converter
from converters.load_and_embed import LoadAndEmbed
from utils.logger import setup_logger

# Configuración del logger
logger = setup_logger(__name__)

def main():
    # Configuración de servicios
    model = "llama3.1:8b-instruct-q4_0"
    ollama_url = "http://ollama_service:11434/api/chat"
    ollama_healthcheck_url = "http://ollama_service:11434/api/tags"
    anythingllm_url = "http://anythingllm:3001/api/ping"
    content = "Por favor, dame un saludo original y creativo, solo una frase, simple."

    ollama_service = OllamaService(
        url=ollama_url,
        healthcheck_url=ollama_healthcheck_url,
        model=model
    )

    anythingllm_service = AnythingLLMService(url=anythingllm_url)

    converter = Converter(input_dir="/app/documentos/input", output_dir="/app/documentos/converted")
    loader = LoadAndEmbed()

    # Esperar a que Ollama y AnythingLLM estén disponibles
    if not ollama_service.wait_until_available() or not anythingllm_service.wait_until_available():
        logger.error("No se pudo conectar a Ollama o AnythingLLM. Servicio(s) no disponible(s).")
        return

    # Hacer solicitud a Ollama
    response = ollama_service.make_request(content)

    if response:
        message = response.get("message", {}).get("content", "No se generó texto.")
        logger.info(f"Saludo generado por Ollama: {message}")

        # Ejecutar conversión y carga
        converter.convert_and_process_documents()
        loader.load_and_embed_documents()

if __name__ == "__main__":
    main()

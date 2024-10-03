# app/main.py

import json
import time
import subprocess
import requests
from services.ollama_service import OllamaService
from services.anythingllm_service import AnythingLLMService
from converters.reformat import process_documents  # Importar la función de procesamiento
from converters.converter import Converter
from converters.load_and_embed import LoadAndEmbed
from utils.logger import setup_logger
import os

# Configuración del logger
logger = setup_logger(__name__)

def main():
    # Configuración de servicios
    model = os.getenv('OLLAMA_MODEL')
    ollama_url = "http://ollama_service:11434/api/chat"
    ollama_healthcheck_url = "http://ollama_service:11434/api/tags"
    anythingllm_url = "http://anythingllm:3001"  # URL base sin el endpoint
    content = "Por favor, dame un saludo original y creativo, solo una frase, simple."

    # Inicializar servicios
    ollama_service = OllamaService(
        url=ollama_url,
        healthcheck_url=ollama_healthcheck_url,
        model=model
    )

    anythingllm_service = AnythingLLMService(url=anythingllm_url)

    converter = Converter(input_dir="/app/documentos/input", output_dir="/app/documentos/converted")
    loader = LoadAndEmbed()

    # Esperar a que Ollama y AnythingLLM estén disponibles
    logger.info("Esperando a que Ollama y AnythingLLM estén disponibles...")
    if not ollama_service.wait_until_available() or not anythingllm_service.wait_until_available():
        logger.error("No se pudo conectar a Ollama o AnythingLLM. Servicio(s) no disponible(s).")
        return

    logger.info("Conexión establecida con Ollama y AnythingLLM.")

    # Asegurar que el workspace exista
    logger.info("Verificando la existencia del workspace en AnythingLLM...")
    if not anythingllm_service.ensure_workspace("admin"):
        logger.error("No se pudo asegurar que el workspace esté listo.")
        return

    logger.info("Workspace está listo para usarse.")

    # Obtener la API Key desde AnythingLLMService
    api_key = anythingllm_service.api_key
    if not api_key:
        logger.error("API Key no está disponible.")
        return

    # Hacer solicitud a Ollama
    logger.info("Realizando solicitud a Ollama...")
    response = ollama_service.make_request(content)

    if response:
        message = response.get("message", {}).get("content", "No se generó texto.")
        logger.info(f"Saludo generado por Ollama: {message}")

        # Ejecutar conversión y procesamiento inicial de documentos
        logger.info("Ejecutando conversión de documentos...")
        converter.convert_and_process_documents()
        logger.info("Conversión de documentos completada.")

        # Ejecutar procesamiento adicional de documentos (adaptación/reformateo)
        # logger.info("Ejecutando procesamiento adicional de documentos para RAG...")
        # input_dir = "/app/documentos/converted"
        # output_dir = "/app/documentos/reformateados"
        # process_documents(input_dir, output_dir, ollama_service, logger)
        # logger.info("Procesamiento adicional de documentos completado.")

        # Cargar y embebedar documentos procesados
        logger.info("Cargando y embebiendo documentos...")
        loader.load_and_embed_documents(api_key=api_key)
    else:
        logger.error("No se recibió una respuesta válida de Ollama.")

if __name__ == "__main__":
    main()

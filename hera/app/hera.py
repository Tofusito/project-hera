# app/main.py

from services.anythingllm_service import AnythingLLMService
from converters.load_and_embed import LoadAndEmbed
from utils.logger import setup_logger
import os

# Configuración del logger
logger = setup_logger(__name__)

def main():
    # Configuración de servicios
    anythingllm_service = AnythingLLMService()

    input_dir = os.getenv('INPUT_DIR')

    loader = LoadAndEmbed()

    # Esperar a que Ollama y AnythingLLM estén disponibles
    logger.info("Esperando a que Ollama y AnythingLLM estén disponibles...")
    if not anythingllm_service.wait_until_available():
        logger.error("No se pudo conectar A AnythingLLM. Serviciono disponible.")
        return

    logger.info("Conexión establecida con AnythingLLM.")

    # Asegurar que el workspace exista
    logger.info("Verificando la existencia del workspace en AnythingLLM...")
    if not anythingllm_service.ensure_workspace("admin"):
        logger.error("No se pudo asegurar que el workspace esté listo.")
        return

    logger.info("Workspace está listo para usarse.")

    # Obtener la API Key desde AnythingLLMService
    api_key = anythingllm_service.get_api_key()
    if not api_key:
        logger.error("API Key no está disponible.")
        return

    # Cargar y embebedar documentos procesados
    logger.info("Cargando y embebiendo documentos...")
    loader.load_and_embed_documents(api_key=api_key)

if __name__ == "__main__":
    main()

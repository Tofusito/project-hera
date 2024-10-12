# app/services/ollama_service.py

import time
import json
import requests
from utils.logger import setup_logger

logger = setup_logger(__name__)

class OllamaService:
    def __init__(self, url, healthcheck_url, model):
        self.url = url
        self.healthcheck_url = healthcheck_url
        self.model = model
        self.headers = {"Content-Type": "application/json"}

    def wait_until_models_loaded(self, max_retries=10, interval=60):
        logger.info("Esperando que los modelos de Ollama se carguen...")
        retries = 0

        while retries < max_retries:
            try:
                response = requests.get(self.healthcheck_url)
                logger.info(f"Respuesta del healthcheck: Status: {response.status_code}, Content: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Datos de respuesta: {data}")
                    
                    if data.get("models") and len(data["models"]) > 1:
                        logger.info("Los modelos de Ollama están cargados y disponibles.")
                        logger.info(f"Modelos disponibles: {data['models']}")
                        return True
                    else:
                        retries += 1
                        logger.warning(f"Los modelos de Ollama no están disponibles. Intento {retries}/{max_retries}. Reintentando en {interval} segundos...")
                else:
                    logger.warning(f"No se pudo conectar a Ollama. Código de estado: {response.status_code}. Intento {retries}/{max_retries}. Reintentando en {interval} segundos...")
                    logger.info(f"Contenido de la respuesta: {response.text}")
            except requests.exceptions.RequestException as e:
                retries += 1
                logger.error(f"Error al intentar conectarse a Ollama: {e}. Intento {retries}/{max_retries}. Reintentando en {interval} segundos...")
            time.sleep(interval)

        logger.error("Tiempo de espera agotado para que los modelos de Ollama estén disponibles.")
        return False

    def make_request(self, content, retry_delay=60):
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": content}
            ],
            "stream": False
        }

        while True:
            try:
                response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 404:
                    logger.error(f"Modelo no encontrado: {response.text}. Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)

                else:
                    logger.error(f"Error al hacer la solicitud a Ollama: {response.status_code} - {response.text}")
                    time.sleep(retry_delay)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error de conexión con Ollama: {e}. Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)

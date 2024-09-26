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

    def wait_until_available(self, timeout=180, interval=5):
        logger.info("Esperando a que Ollama esté disponible...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.healthcheck_url)
                if response.status_code == 200:
                    logger.info("Ollama está disponible.")
                    return True
            except requests.exceptions.RequestException:
                pass
            logger.warning(f"Ollama no está disponible, reintentando en {interval} segundos...")
            time.sleep(interval)
        logger.error("Tiempo de espera agotado para Ollama.")
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

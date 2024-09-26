# app/services/anythingllm_service.py

import time
import requests
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AnythingLLMService:
    def __init__(self, url):
        self.url = url

    def wait_until_available(self, timeout=180, interval=5):
        logger.info(f"Esperando a que AnythingLLM esté disponible en {self.url}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.url)
                if response.status_code == 200:
                    logger.info("AnythingLLM está disponible.")
                    return True
            except requests.exceptions.RequestException:
                pass
            logger.warning(f"AnythingLLM no está disponible, reintentando en {interval} segundos...")
            time.sleep(interval)
        logger.error("Tiempo de espera agotado para AnythingLLM.")
        return False

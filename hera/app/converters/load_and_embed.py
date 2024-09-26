# app/converters/load_and_embed.py

import os
import requests
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)

class LoadAndEmbed:
    def __init__(self):
        self.workspace = os.getenv('WORKSPACE')
        self.api_key = os.getenv('API_KEY')
        self.base_url = "http://anythingllm:3001"
        self.directory = "/app/documentos/converted"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        if not self.workspace or not self.api_key:
            logger.error("WORKSPACE y API_KEY deben estar configurados como variables de entorno.")
            raise ValueError("WORKSPACE y API_KEY deben estar configurados como variables de entorno.")

    def extract_titles_from_items(self, items):
        titles = set()
        for item in items:
            if item.get('type') == 'file':
                title = item.get('title')
                if title:
                    titles.add(title)
            elif item.get('type') == 'folder':
                titles.update(self.extract_titles_from_items(item.get('items', [])))
        return titles

    def get_existing_documents(self):
        url = f"{self.base_url}/api/v1/documents"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                documents = data.get('localFiles', {}).get('items', [])
                existing_titles = self.extract_titles_from_items(documents)
                logger.info(f"Documentos existentes obtenidos: {len(existing_titles)}")
                return existing_titles
            else:
                logger.error(f"Error al obtener documentos existentes: {response.status_code}")
                return set()
        except ValueError as e:
            logger.error(f"Error al decodificar JSON de la respuesta: {e}")
            return set()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al conectar con AnythingLLM: {e}")
            return set()

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                response = requests.post(
                    f"{self.base_url}/api/v1/document/upload",
                    headers=self.headers,
                    files={"file": file},
                    data={"workspace": self.workspace}
                )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al cargar el archivo {file_path}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al cargar el archivo {file_path}: {e}")
            return None

    def update_embeddings(self, adds):
        payload = {"adds": adds, "deletes": []}
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/workspace/{self.workspace}/update-embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload)
            )
            if response.status_code == 200:
                logger.info("Embeddings actualizados correctamente.")
            else:
                logger.error(f"Error al actualizar embeddings: {response.status_code}")
        except Exception as e:
            logger.error(f"Error al actualizar embeddings: {e}")

    def load_and_embed_documents(self):
        existing_titles = self.get_existing_documents()
        adds = []

        for file_name in os.listdir(self.directory):
            file_path = os.path.join(self.directory, file_name)
            if os.path.isfile(file_path):
                base_name = os.path.splitext(file_name)[0]
                expected_title = f"{base_name}.txt"

                if expected_title in existing_titles:
                    logger.info(f"El archivo '{expected_title}' ya ha sido cargado. Omitiendo.")
                    continue

                logger.info(f"Cargando archivo: {file_path}")
                response = self.upload_file(file_path)
                if response and 'documents' in response:
                    document_location = response['documents'][0]['location']
                    adds.append(document_location)

        if adds:
            logger.info(f"Actualizando embeddings para {len(adds)} documentos.")
            self.update_embeddings(adds)
        else:
            logger.info("No hay nuevos documentos para actualizar embeddings.")

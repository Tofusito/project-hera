import os
import requests
import json
from utils.logger import setup_logger

import logging
logger = setup_logger(__name__, level=logging.DEBUG)
logger.setLevel(logging.DEBUG)

class LoadAndEmbed:
    def __init__(self):
        logger.debug("Inicializando LoadAndEmbed")
        self.workspace = os.getenv('WORKSPACE', 'assistant')
        self.base_url = "http://anythingllm:3001"
        self.directory = "/app/documentos/converted"

        logger.debug(f"Workspace configurado como: {self.workspace}")
        logger.debug(f"Base URL configurada como: {self.base_url}")
        logger.debug(f"Directorio de documentos configurado como: {self.directory}")

        if not self.workspace:
            logger.error("WORKSPACE debe estar configurado como variable de entorno.")
            raise ValueError("WORKSPACE debe estar configurado como variable de entorno.")

    def extract_titles_from_items(self, items):
        logger.debug("Extrayendo títulos de los elementos")
        titles = set()
        for item in items:
            if item.get('type') == 'file':
                title = item.get('title')
                if title:
                    titles.add(title)
                    logger.debug(f"Título extraído: {title}")
            elif item.get('type') == 'folder':
                logger.debug(f"Extrayendo títulos de la carpeta: {item.get('name')}")
                titles.update(self.extract_titles_from_items(item.get('items', [])))
        return titles

    def get_existing_documents(self):
        logger.debug("Obteniendo documentos existentes desde AnythingLLM")
        url = f"{self.base_url}/api/v1/documents"
        if not hasattr(self, 'headers') or not self.headers:
            logger.error("Headers no están configurados. Asegúrese de que 'load_and_embed_documents' se haya llamado primero.")
            return []
        try:
            logger.debug(f"Realizando solicitud GET a {url}")
            response = requests.get(url, headers=self.headers)
            logger.debug(f"Respuesta recibida con código de estado: {response.status_code}")
            logger.debug(f"Respuesta completa recibida: {response.text}")
            if response.status_code == 200:
                data = response.json()
                documents = data.get('localFiles', {}).get('items', [])
                logger.info(f"Documentos existentes obtenidos: {len(documents)}")
                logger.debug(f"Listado completo de documentos existentes: {documents}")
                return documents  # Devolvemos los documentos completos
            else:
                logger.error(f"Error al obtener documentos existentes: {response.status_code}")
                return []
        except ValueError as e:
            logger.error(f"Error al decodificar JSON de la respuesta: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al conectar con AnythingLLM: {e}")
            return []

    def update_embeddings(self, adds):
        logger.debug("Actualizando embeddings")
        payload = {"adds": adds, "deletes": []}
        try:
            logger.debug(f"Realizando solicitud POST para actualizar embeddings: {payload}")
            response = requests.post(
                f"{self.base_url}/api/v1/workspace/{self.workspace}/update-embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            logger.debug(f"Respuesta recibida con código de estado: {response.status_code}")
            if response.status_code == 200:
                logger.info("Embeddings actualizados correctamente.")
            else:
                logger.error(f"Error al actualizar embeddings: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al actualizar embeddings: {e}")

    def load_and_embed_documents(self, api_key):
        logger.debug("Cargando y embebiendo documentos")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        logger.debug(f"Headers configurados: {self.headers}")
        
        # Recuperar títulos de documentos ya cargados para evitar duplicados
        existing_documents = self.get_existing_documents()
        existing_titles = self.extract_titles_from_items(existing_documents)

        # Cargar todos los documentos de /app/documentos/converted que no estén ya cargados
        for file_name in os.listdir(self.directory):
            file_path = os.path.join(self.directory, file_name)
            logger.debug(f"Procesando archivo: {file_name}")
            if os.path.isfile(file_path) and file_name not in existing_titles:
                try:
                    with open(file_path, 'rb') as file:
                        logger.debug(f"Cargando archivo: {file_path}")
                        response = requests.post(
                            f"{self.base_url}/api/v1/document/upload",
                            headers=self.headers,
                            files={"file": file},
                            data={"workspace": self.workspace}
                        )
                    logger.debug(f"Respuesta recibida al cargar archivo: {response.status_code}")
                    if response.status_code == 200:
                        logger.info(f"Archivo {file_name} cargado correctamente.")
                        try:
                            os.remove(file_path)
                            logger.info(f"Archivo {file_name} eliminado después de cargar correctamente.")
                        except Exception as e:
                            logger.error(f"Error al eliminar el archivo {file_name}: {e}")
                    else:
                        logger.error(f"Error al cargar el archivo {file_name}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error al cargar el archivo {file_name}: {e}")
            else:
                logger.info(f"El archivo '{file_name}' ya existe en AnythingLLM. Omitiendo carga.")

        # Recuperar todos los documentos ya cargados desde AnythingLLM para actualizar embeddings
        logger.debug("Recuperando documentos existentes para actualizar embeddings")
        existing_documents = self.get_existing_documents()

        # Agregar todos los documentos obtenidos para los embeddings
        adds = []
        def collect_files(items, parent_name=""):
            for item in items:
                if item.get('type') == 'file':
                    document_location = f"{parent_name}/{item.get('name')}"
                    logger.debug(f"Añadiendo documento para embeddings: {document_location}")
                    adds.append(document_location)
                elif item.get('type') == 'folder':
                    folder_name = f"{parent_name}/{item.get('name')}" if parent_name else item.get('name')
                    logger.debug(f"Entrando en la carpeta: {folder_name}")
                    collect_files(item.get('items', []), folder_name)
        
        collect_files(existing_documents)

        # Actualizar los embeddings para todos los documentos recuperados
        if adds:
            logger.info(f"Actualizando embeddings para {len(adds)} documentos.")
            self.update_embeddings(adds)
        else:
            logger.info("No hay documentos para actualizar embeddings.")
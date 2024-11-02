import os
import time
import requests
import jwt
import datetime
import boto3
from utils.logger import setup_logger


logger = setup_logger(__name__)

# Configurar el cliente de Secrets Manager para LocalStack
secrets_client = boto3.client(
    'secretsmanager',
    region_name='us-east-1',
    endpoint_url=os.getenv('AWS_ENDPOINT').rstrip('/'),
    aws_access_key_id='dummy',  # Credenciales dummy para LocalStack
    aws_secret_access_key='dummy'
)

class AnythingLLMService:
    def __init__(self):
        """
        Inicializa el servicio AnythingLLM.

        Args:
            url (str): La URL base del servicio AnythingLLM.
        """
        
        self.base_url = os.getenv('ANYTHINGLLM_ENDPOINT').rstrip('/')

        workspace = os.getenv('WORKSPACES').split(',')
        # Eliminamos posibles espacios en blanco.
        self.workspace = [name.strip() for name in workspace if name.strip()]
        
        self.password = os.getenv('PASSWORD')  # Obtenemos la contraseña de la variable de entorno
        self.jwt_secret = os.getenv('JWT_SECRET')  # Obtenemos el JWT_SECRET de la variable de entorno

        logger.info(f"Inicializando AnythingLLMService con base_url: {self.base_url}")
        logger.info(f"Workspace obtenido: {self.workspace}")
        logger.info(f"JWT_SECRET y PASSWORD han sido cargados correctamente.")

        # Verificar la existencia de las variables de entorno
        if not self.workspace:
            logger.error("WORKSPACE no está definida en las variables de entorno.")
            raise ValueError("WORKSPACE no definida")

        if not self.password:
            logger.error("PASSWORD no está definida en las variables de entorno.")
            raise ValueError("PASSWORD no definida")

        if not self.jwt_secret:
            logger.error("JWT_SECRET no está definida en las variables de entorno.")
            raise ValueError("JWT_SECRET no definida")

    def get_api_key(self):
        """
        Recupera un secreto desde AWS Secrets Manager.
        
        Args:
            secret_name (str): El nombre del secreto.
            
        Returns:
            str: El valor del secreto como una cadena JSON si existe, None si no existe.
        """
        try:
            response = secrets_client.get_secret_value(SecretId='anythingllm_api_key')
            logger.info("API Key encontrada en Secrets Manager.")
            return response['SecretString']
        except secrets_client.exceptions.ResourceNotFoundException:
            logger.info("El secreto 'anythingllm_api_key' no existe en Secrets Manager.")
            return None
        except Exception as e:
            logger.error(f"Error al verificar la API Key en Secrets Manager: {e}")
            return None
    
    def generate_jwt(self, username):
        """
        Genera un token JWT para autenticación con el servicio.

        Args:
            username (str): Nombre de usuario para el token.

        Returns:
            str: JWT generado.
        """
        logger.info(f"Generando JWT para el usuario: {username}")
        secret_key = self.jwt_secret
        payload = {
            'id': 1,  # ID fijo según tu solicitud
            'username': username,
            'iat': datetime.datetime.now(datetime.timezone.utc),  # Usamos timezone.utc
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)  # Expira en 1 hora
        }

        token = jwt.encode(payload, secret_key, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        logger.info(f"JWT generado correctamente para el usuario: {username}")
        return token

    def wait_until_available(self, timeout=180, interval=5):
        """
        Espera hasta que el servicio AnythingLLM esté disponible.

        Args:
            timeout (int): Tiempo máximo en segundos para esperar.
            interval (int): Intervalo en segundos entre reintentos.

        Returns:
            bool: True si el servicio está disponible, False si el tiempo de espera se agota.
        """
        ping_url = f"{self.base_url}/api/ping"
        logger.info(f"Esperando a que AnythingLLM esté disponible en {ping_url}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(ping_url)
                logger.debug(f"Respuesta del ping: {response.status_code}")
                if response.status_code == 200:
                    logger.info("AnythingLLM está disponible.")
                    return True
            except requests.exceptions.RequestException as e:
                logger.warning(f"Excepción al intentar conectar con AnythingLLM: {e}")
            logger.warning(f"AnythingLLM no está disponible, reintentando en {interval} segundos...")
            time.sleep(interval)
        logger.error("Tiempo de espera agotado para AnythingLLM.")
        return False

    def enable_multi_user(self):
        """
        Habilita el modo multiusuario en AnythingLLM.
        """
        logger.info("Intentando habilitar el modo multiusuario en AnythingLLM...")
        enable_multi_user_url = f"{self.base_url}/api/system/enable-multi-user"
        payload = {
            "username": "admin",
            "password": self.password  # Utiliza la contraseña de la variable de entorno
        }
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',  # Cambiado a 'application/json' para mejor compatibilidad
        }

        logger.debug(f"Realizando POST a {enable_multi_user_url} con payload: {payload}")
        try:
            response = requests.post(enable_multi_user_url, headers=headers, json=payload)
            if response.status_code == 200:
                logger.info("Modo multiusuario habilitado correctamente.")
                return True
            else:
                logger.error(f"Error al habilitar el modo multiusuario: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Excepción al habilitar el modo multiusuario: {e}")
            return False

    def generate_api_key(self, username):
        """
        Genera una API Key utilizando un JWT para autenticación con una solicitud HTTP usando requests.
        La API Key generada se almacena directamente en AWS Secrets Manager.

        Args:
            username (str): Nombre de usuario para generar el JWT y usarlo en la autenticación.

        Returns:
            bool: True si la API key se generó y guardó correctamente en Secrets Manager, False en caso contrario.
        """
        logger.info(f"Generando API Key para el usuario: {username}")
        
        # Generar el JWT
        token = self.generate_jwt(username)
        logger.debug(f"JWT generado: {token}")

        # Configurar la URL para generar el API Key
        api_key_url = f'{self.base_url}/api/admin/generate-api-key'

        # Configurar los headers
        headers = {
            'Accept': '*/*',
            'Authorization': f'Bearer {token}',
            'Connection': 'keep-alive',
            'Origin': 'http://localhost:3001',
            'Referer': 'http://localhost:3001/settings/api-keys',
            'Content-Type': 'application/json'
        }

        logger.debug(f"Realizando solicitud POST a {api_key_url} con headers: {headers}")
        try:
            # Realizar la solicitud POST para generar la API Key
            response = requests.post(api_key_url, headers=headers)
            logger.debug(f"Respuesta de la solicitud de generación de API Key: {response.status_code} - {response.text}")

            # Verificar el código de estado de la respuesta
            if response.status_code == 200:
                logger.info("API Key generada correctamente.")
                api_key_data = response.json()  # Obtener el JSON de la respuesta

                # Extraer el 'secret' de la respuesta
                api_secret = api_key_data['apiKey']['secret']
                logger.info(f"API Secret obtenida: {api_secret}")

                # Guardar la API Key en Secrets Manager
                try:
                    secrets_client.create_secret(Name='anythingllm_api_key', SecretString=api_secret)
                    logger.info("API Key creada en Secrets Manager.")
                except secrets_client.exceptions.ResourceExistsException:
                    logger.info("El secreto 'anythingllm_api_key' ya existe. Actualizando...")
                    secrets_client.put_secret_value(SecretId='anythingllm_api_key', SecretString=api_secret)
                    logger.info("API Key actualizada en Secrets Manager.")
                except Exception as e:
                    logger.error(f"Error al almacenar la API Key en Secrets Manager: {e}")
                    return False

                return True

            else:
                logger.error(f"Error al generar la API Key: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Excepción durante la solicitud de generación de API Key: {e}")
            return False

    def check_api_key(self):
        """
        Verifica si la API Key existe en AWS Secrets Manager y la muestra para depuración.

        Returns:
            bool: True si la API Key se recuperó correctamente, False si no existe.
        """
        logger.info("Verificando si la API Key existe en Secrets Manager...")
        try:
            logger.debug("Intentando obtener el valor del secreto con el ID 'anythingllm_api_key'.")
            response = secrets_client.get_secret_value(SecretId='anythingllm_api_key')

            # Mostrar la respuesta completa para depuración
            logger.debug(f"Respuesta completa de Secrets Manager: {response}")

            if 'SecretString' in response:
                logger.info("API Key encontrada en Secrets Manager.")
                self.api_key = response['SecretString']  # Guardar la API Key recuperada
                logger.debug(f"API Key recuperada: {self.api_key}")
                return True
            else:
                logger.warning("La respuesta de Secrets Manager no contiene 'SecretString'. Verificar el formato del secreto.")
                return False

        except secrets_client.exceptions.ResourceNotFoundException:
            logger.info("El secreto 'anythingllm_api_key' no existe en Secrets Manager.")
            return False
        except Exception as e:
            logger.error(f"Error al verificar la API Key en Secrets Manager: {e}")
            return False

    def create_workspace(self, workspace):
        """
        Crea un nuevo workspace utilizando el Bearer token generado dinámicamente.

        Args:
            username (str): Nombre de usuario para generar el JWT.

        Returns:
            bool: True si el workspace se creó exitosamente, False en caso contrario.
        """
        logger.info(f"Intentando crear el workspace '{workspace}'...")

        # Intentar recuperar la API Key de Secrets Manager
        try:
            response = secrets_client.get_secret_value(SecretId='anythingllm_api_key')
            token = response['SecretString']
            logger.info("API Key obtenida desde Secrets Manager.")
        except secrets_client.exceptions.ResourceNotFoundException:
            logger.error("La API Key no existe en Secrets Manager. No se puede proceder.")
            return False
        except Exception as e:
            logger.error(f"Error al obtener la API Key desde Secrets Manager: {e}")
            return False

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        create_url = f"{self.base_url}/api/v1/workspace/new"
        payload = {
            "name": workspace
        }
        logger.debug(f"Realizando solicitud POST a {create_url} con payload: {payload}")
        try:
            response = requests.post(create_url, headers=headers, json=payload)
            logger.debug(f"Respuesta de la creación de workspace: {response.status_code} - {response.text}")
            if response.status_code in [200, 201]:
                logger.info(f"Workspace '{workspace}' creado exitosamente.")
                return True
            else:
                logger.error(f"Error al crear el workspace: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Excepción al crear el workspace: {e}")
            return False

    def ensure_workspace(self, username):
        """
        Asegura que el workspace exista. Si no existe, realiza los pasos necesarios para crearlo.

        Args:
            username (str): Nombre de usuario para generar el JWT.

        Returns:
            bool: True si el workspace existe o se creó exitosamente, False en caso contrario.
        """
        logger.info("Asegurando que el workspace exista...")
        if not self.check_api_key():
            logger.info("Es el primer arranque. Iniciando el proceso de configuración inicial.")

            # Habilitar el modo multiusuario
            if not self.enable_multi_user():
                logger.error("No se pudo habilitar el modo multiusuario.")
                return False

            # Generar y guardar la API Key
            if not self.generate_api_key(username):
                logger.error("No se pudo generar la API Key.")
                return False

            for ws in self.workspace:
                # Crear el workspace asistente
                if not self.create_workspace(ws):
                    logger.error(f"No se pudo crear el workspace '{ws}'.")
                    return False

            logger.info("Configuración inicial completada exitosamente.")
            return True

        logger.info(f"AnythingLLM ya está configurado.")
        return True

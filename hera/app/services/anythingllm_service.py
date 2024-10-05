import os
import time
import requests
import jwt
import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AnythingLLMService:
    def __init__(self, url):
        """
        Inicializa el servicio AnythingLLM.

        Args:
            url (str): La URL base del servicio AnythingLLM.
        """
        self.base_url = url.rstrip('/')  # Asegura que no termine con '/'
        self.workspace = os.getenv('WORKSPACE')
        self.password = os.getenv('PASSWORD')  # Obtenemos la contraseña de la variable de entorno
        self.jwt_secret = os.getenv('JWT_SECRET')  # Obtenemos el JWT_SECRET de la variable de entorno
        self.api_key = os.getenv('API_KEY')
        self.api_key_path = "/app/session/api_key"  # Directorio donde se guardará la API Key


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
        El `secret` recibido se guarda en un fichero local llamado `api_key`.

        Args:
            username (str): Nombre de usuario para generar el JWT y usarlo en la autenticación.

        Returns:
            bool: True si la API key se generó y guardó correctamente, False en caso contrario.
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
            'Content-Type': 'application/json'  # Añadido para asegurar la correcta interpretación del payload
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

                # Asegurar que el directorio /app/session exista
                os.makedirs(os.path.dirname(self.api_key_path), exist_ok=True)

                # Guardar el 'secret' en el archivo 'api_key'
                try:
                    with open(self.api_key_path, 'w') as f:
                        f.write(api_secret)
                    logger.info(f"La API Secret ha sido guardada correctamente en {self.api_key_path}.")
                except Exception as e:
                    logger.error(f"Error al escribir en el archivo '{self.api_key_path}': {e}")
                    return False

                # Opcional: también establecer como variable de entorno
                os.environ['API_KEY'] = api_secret
                self.api_key = api_secret

                logger.info("API Key establecida como variable de entorno y almacenada correctamente.")
                return True

            else:
                logger.error(f"Error al generar la API Key: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Excepción durante la solicitud de generación de API Key: {e}")
            return False

    def load_api_key(self):
        """
        Carga la API Key desde el archivo 'api_key' en /app/session si existe.

        Returns:
            bool: True si la API Key se cargó correctamente, False si el archivo no existe o hay un error.
        """
        logger.info(f"Intentando cargar la API Key desde el archivo '{self.api_key_path}'...")
        if os.path.exists(self.api_key_path):
            try:
                with open(self.api_key_path, 'r') as f:
                    self.api_key = f.read().strip()
                logger.info(f"API Key cargada correctamente desde el archivo '{self.api_key_path}': {self.api_key}")
                return True
            except Exception as e:
                logger.error(f"Error al leer el archivo '{self.api_key_path}': {e}")
                return False
        else:
            logger.info(f"El archivo '{self.api_key_path}' no existe.")
            return False

    def workspace_exists(self):
        """
        Verifica si la API Key existe localmente.

        Returns:
            bool: True si la API Key existe, False si no existe.
        """
        logger.info("Verificando si la API Key existe localmente...")
        if self.load_api_key():
            logger.info("API Key encontrada.")
            return True
        else:
            logger.info("API Key no encontrada, es el primer arranque.")
            return False

    def create_workspace(self, username):
        """
        Crea un nuevo workspace utilizando el Bearer token generado dinámicamente.

        Args:
            username (str): Nombre de usuario para generar el JWT.

        Returns:
            bool: True si el workspace se creó exitosamente, False en caso contrario.
        """
        logger.info(f"Intentando crear el workspace '{self.workspace}'...")
        token = self.api_key
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        create_url = f"{self.base_url}/api/v1/workspace/new"
        payload = {
            "name": self.workspace
        }
        logger.debug(f"Realizando solicitud POST a {create_url} con payload: {payload}")
        try:
            response = requests.post(create_url, headers=headers, json=payload)
            logger.debug(f"Respuesta de la creación de workspace: {response.status_code} - {response.text}")
            if response.status_code in [200, 201]:
                logger.info(f"Workspace '{self.workspace}' creado exitosamente.")
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
        if not self.workspace_exists():
            logger.info("Es el primer arranque. Iniciando el proceso de configuración inicial.")

            # Habilitar el modo multiusuario
            if not self.enable_multi_user():
                logger.error("No se pudo habilitar el modo multiusuario.")
                return False

            # Generar y guardar la API Key
            if not self.generate_api_key(username):
                logger.error("No se pudo generar la API Key.")
                return False

            # Crear el workspace
            if not self.create_workspace(username):
                logger.error(f"No se pudo crear el workspace '{self.workspace}'.")
                return False

            logger.info("Configuración inicial completada exitosamente.")
            return True

        logger.info(f"El workspace '{self.workspace}' ya está configurado.")
        return True

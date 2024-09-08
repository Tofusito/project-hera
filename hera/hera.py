import requests
import json
import time

# Variables del modelo y la URL de la API de Ollama
MODEL = "llama3.1:8b-instruct-q4_0"
URL = "http://ollama_service:11888/api/chat"
HEALTHCHECK_URL = "http://ollama_service:11888/api/tags"

# Contenido del mensaje (puedes reemplazarlo por lo que desees)
CONTENT = "Por favor, dame un saludo original y creativo."

# Datos que se enviarán en la solicitud POST
data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": CONTENT}
    ],
    "stream": False
}

# Encabezados para la solicitud
headers = {
    "Content-Type": "application/json"
}

# Esperar hasta que Ollama esté disponible
def wait_for_ollama(url, timeout=180, interval=5):
    print("Esperando a que Ollama esté disponible...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Ollama está disponible.")
                return True
        except requests.exceptions.RequestException:
            pass
        print("Ollama no está disponible, reintentando en {} segundos...".format(interval))
        time.sleep(interval)
    print("Tiempo de espera agotado.")
    return False

# Esperar a que Ollama esté disponible antes de realizar la solicitud
if wait_for_ollama(HEALTHCHECK_URL):
    try:
        # Realizar la solicitud POST a Ollama
        response = requests.post(URL, headers=headers, data=json.dumps(data))

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Extraer y mostrar el contenido del mensaje de la respuesta
            result = response.json()
            message_content = result.get("message", {}).get("content", "No se generó texto.")
            print("Saludo generado por Ollama:", message_content)
        else:
            print(f"Error al hacer la solicitud: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
else:
    print("No se pudo conectar a Ollama. Servicio no disponible.")
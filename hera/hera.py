import requests
import json
import time
import subprocess

# Variables del modelo y la URL de la API de Ollama y AnythingLLM
MODEL = "llama3.1:8b-instruct-q4_0"
OLLAMA_URL = "http://ollama_service:11434/api/chat"
OLLAMA_HEALTHCHECK_URL = "http://ollama_service:11434/api/tags"
ANYTHINGLLM_URL = "http://anythingllm:3001/api/ping"  # URL para verificar que AnythingLLM está disponible

# Contenido del mensaje (puedes reemplazarlo por lo que desees)
CONTENT = "Por favor, dame un saludo original y creativo, solo una frase, simple."

# Datos que se enviarán en la solicitud POST a Ollama
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
    print("Esperando a que Ollama esté disponible...", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Ollama está disponible.", flush=True)
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Ollama no está disponible, reintentando en {interval} segundos...", flush=True)
        time.sleep(interval)
    print("Tiempo de espera agotado.", flush=True)
    return False

# Esperar hasta que AnythingLLM esté disponible usando la URL de ping
def wait_for_anythingllm(url, timeout=180, interval=5):
    print(f"Esperando a que AnythingLLM esté disponible en {url}...", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("AnythingLLM está disponible.", flush=True)
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"AnythingLLM no está disponible, reintentando en {interval} segundos...", flush=True)
        time.sleep(interval)
    print("Tiempo de espera agotado para AnythingLLM.", flush=True)
    return False

# Ejecutar el script converter.py
def run_converter():
    print("Ejecutando el script converter.py para convertir archivos y luego cargarlos a AnythingLLM...", flush=True)
    try:
        subprocess.run(["python3", "/app/converter.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar converter.py: {e}", flush=True)
        time.sleep(60)  # Esperar 1 minuto antes de volver a intentar
        run_converter()  # Reintentar la ejecución del convertidor

# Función para manejar error 404 y reintentar indefinidamente
def make_request_to_ollama():
    while True:  # Reintentar indefinidamente
        try:
            # Realizar la solicitud POST a Ollama
            response = requests.post(OLLAMA_URL, headers=headers, data=json.dumps(data))

            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                # Extraer y mostrar el contenido del mensaje de la respuesta
                result = response.json()
                message_content = result.get("message", {}).get("content", "No se generó texto.")
                print("Saludo generado por Ollama:", message_content, flush=True)

                # Ejecutar la conversión y carga de documentos si Ollama y AnythingLLM están listos
                run_converter()
                break  # Salir del bucle si todo fue exitoso

            elif response.status_code == 404:
                print(f"Modelo no encontrado: {response.text}. Reintentando en 1 minuto...", flush=True)
                time.sleep(60)  # Esperar 1 minuto antes de reintentar

            else:
                print(f"Error al hacer la solicitud a Ollama: {response.status_code}", flush=True)
                print(response.text, flush=True)
                time.sleep(60)  # Esperar 1 minuto antes de reintentar

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con Ollama: {e}", flush=True)
            time.sleep(60)  # Esperar 1 minuto antes de reintentar

# Verificar que Ollama y AnythingLLM estén disponibles antes de proceder
if wait_for_ollama(OLLAMA_HEALTHCHECK_URL) and wait_for_anythingllm(ANYTHINGLLM_URL):
    make_request_to_ollama()
else:
    print("No se pudo conectar a Ollama o AnythingLLM. Servicio(s) no disponible(s).", flush=True)
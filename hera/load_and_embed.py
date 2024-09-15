import os
import requests
import json

# Variables de entorno
WORKSPACE = os.getenv('WORKSPACE')
API_KEY = os.getenv('API_KEY')
BASE_URL = "http://anythingllm:3001
DIRECTORY = "/app/documentos"

if not WORKSPACE or not API_KEY:
    raise ValueError("WORKSPACE y API_KEY deben estar configurados como variables de entorno.")

# Función para cargar un archivo al servidor de AnythingLLM
def upload_file(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post(
            f"{BASE_URL}/api/v1/document/upload",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": file},
            data={"workspace": WORKSPACE}
        )
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")  # Imprimir el contenido de la respuesta

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as e:
                print(f"Error al decodificar JSON: {e}")
                return None
        else:
            print(f"Error al cargar el archivo {file_path}: {response.status_code}")
            return None

# Función para comprobar si un documento ya está embebido
def is_embedded(document_location):
    response = requests.get(
        f"{BASE_URL}/api/v1/workspace/{WORKSPACE}/documents",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response text: {response.text}")  # Imprimir el contenido de la respuesta

    if response.status_code == 200:
        try:
            documents = response.json()  # Intenta decodificar la respuesta como JSON
        except ValueError as e:
            print(f"Error al decodificar JSON: {e}")
            return False
        
        for doc in documents.get('documents', []):
            if doc['location'] == document_location:
                return True
    return False

# Cargar y embebir archivos no cargados
def load_and_embed_documents():
    adds = []
    for file_name in os.listdir(DIRECTORY):
        file_path = os.path.join(DIRECTORY, file_name)
        if os.path.isfile(file_path):
            print(f"Cargando archivo: {file_path}")
            response = upload_file(file_path)
            if response and 'documents' in response:
                document_location = response['documents'][0]['location']
                if not is_embedded(document_location):
                    adds.append(document_location)
                else:
                    print(f"El documento ya está embebido: {document_location}")
    
    if adds:
        print(f"Actualizando embeddings para {len(adds)} documentos.")
        update_embeddings(adds)

# Función para actualizar embeddings en AnythingLLM
def update_embeddings(adds):
    json_adds = json.dumps({"adds": adds, "deletes": []})
    response = requests.post(
        f"{BASE_URL}/api/v1/workspace/{WORKSPACE}/update-embeddings",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        data=json_adds
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response text: {response.text}")  # Imprimir el contenido de la respuesta

    if response.status_code == 200:
        print("Embeddings actualizados correctamente.")
    else:
        print(f"Error al actualizar embeddings: {response.status_code}")

if __name__ == "__main__":
    load_and_embed_documents()

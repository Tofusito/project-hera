import os
import requests
import json

# Variables de entorno
WORKSPACE = os.getenv('WORKSPACE')
API_KEY = os.getenv('API_KEY')
BASE_URL = "http://anythingllm:3001"
DIRECTORY = "/app/documentos/converted"

if not WORKSPACE or not API_KEY:
    raise ValueError("WORKSPACE y API_KEY deben estar configurados como variables de entorno.")

def extract_titles_from_items(items):
    titles = set()
    for item in items:
        if item.get('type') == 'file':
            title = item.get('title')
            if title:
                titles.add(title)
        elif item.get('type') == 'folder':
            titles.update(extract_titles_from_items(item.get('items', [])))
    return titles

def get_existing_documents():
    url = f"{BASE_URL}/api/v1/documents"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        try:
            data = response.json()
            documents = data.get('localFiles', {}).get('items', [])
            existing_titles = extract_titles_from_items(documents)
            print(f"Documentos existentes obtenidos: {len(existing_titles)}")
            return existing_titles
        except ValueError as e:
            print(f"Error al decodificar JSON de la respuesta: {e}")
            return set()
    else:
        print(f"Error al obtener documentos existentes: {response.status_code}")
        return set()

def upload_file(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post(
            f"{BASE_URL}/api/v1/document/upload",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": file},
            data={"workspace": WORKSPACE}
        )
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as e:
                print(f"Error al decodificar JSON: {e}")
                return None
        else:
            print(f"Error al cargar el archivo {file_path}: {response.status_code}")
            return None

def load_and_embed_documents():
    existing_titles = get_existing_documents()

    adds = []
    for file_name in os.listdir(DIRECTORY):
        file_path = os.path.join(DIRECTORY, file_name)
        if os.path.isfile(file_path):
            base_name = os.path.splitext(file_name)[0]
            expected_title = f"{base_name}.txt"

            if expected_title in existing_titles:
                print(f"El archivo '{expected_title}' ya ha sido cargado. Omitiendo.")
                continue

            print(f"Cargando archivo: {file_path}")
            response = upload_file(file_path)
            if response and 'documents' in response:
                document_location = response['documents'][0]['location']
                adds.append(document_location)

    if adds:
        print(f"Actualizando embeddings para {len(adds)} documentos.")
        update_embeddings(adds)

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
    if response.status_code == 200:
        print("Embeddings actualizados correctamente.")
    else:
        print(f"Error al actualizar embeddings: {response.status_code}")

if __name__ == "__main__":
    load_and_embed_documents()

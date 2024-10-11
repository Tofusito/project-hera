from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer
import torch

# Crear la app de FastAPI
app = FastAPI()

# Cargar el modelo y el tokenizador
tokenizer = AutoTokenizer.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True)
model = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True)

# Clase para recibir las solicitudes
class TextData(BaseModel):
    texts: list[str]

@app.post("/get_embeddings")
def get_embeddings(data: TextData):
    # Tokenizar las oraciones
    inputs = tokenizer(data.texts, return_tensors="pt", padding=True, truncation=True)
    
    # Pasar por el modelo
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)  # Usar la media de las representaciones
    
    # Convertir los embeddings a listas para poder enviarlas en la respuesta
    embeddings_list = embeddings.numpy().tolist()

    return {"embeddings": embeddings_list}


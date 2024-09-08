#!/bin/bash

# Iniciar AnythingLLM
{
  cd /app/server/ &&
    npx prisma generate --schema=./prisma/schema.prisma &&
    npx prisma migrate deploy --schema=./prisma/schema.prisma &&
    node /app/server/index.js
} &
{ node /app/collector/index.js; } &

# Esperar a que el servidor de AnythingLLM esté disponible en el puerto 3001
echo "Esperando a que el servidor de AnythingLLM esté disponible en el puerto 3001..."
while ! nc -z localhost 3001; do   
  sleep 5
done

echo "El servidor de AnythingLLM está activo, cargando documentos..."

# Definir el directorio donde se encuentran los archivos y el workspace
DIRECTORY="/app/documentos"
WORKSPACE="${WORKSPACE}"
API_KEY="${API_KEY}"
BASE_URL="http://localhost:3001"

# Verificar que las variables de entorno estén configuradas
if [ -z "$WORKSPACE" ] || [ -z "$API_KEY" ]; then
  echo "Error: WORKSPACE y API_KEY deben estar configurados como variables de entorno."
  exit 1
fi

# Array para almacenar los documentos cargados
adds=()

# Cargar archivos desde el directorio especificado
for file in "$DIRECTORY"/*
do
  if [ -f "$file" ]; then
    echo "Cargando archivo: $file"
    # Hacer la petición curl para subir el archivo al puerto 3001
    response=$(curl -X POST $BASE_URL/api/v1/document/upload \
    -H "Authorization: Bearer $API_KEY" \
    -F "file=@$file" \
    -F "workspace=$WORKSPACE" \
    -w "%{http_code}" \
    -o /tmp/curl_response.json)
    
    # Mostrar la respuesta JSON
    echo "Respuesta del servidor:"
    cat /tmp/curl_response.json
    
    # Comprobar el código de respuesta HTTP
    if [ "$response" -eq 200 ]; then
      echo "Archivo cargado exitosamente: $file"
      # Extraer el nombre del archivo JSON del campo "location" en la respuesta
      json_file=$(jq -r '.documents[0].location' /tmp/curl_response.json)
      echo "Documento JSON extraído: $json_file"
      
      # Añadir archivo a la lista de documentos agregados
      adds+=("\"$json_file\"")
    else
      echo "Error al cargar el archivo: $file (HTTP Code: $response)"
    fi
  fi
done

# Llamar al endpoint para actualizar embeddings si se cargaron archivos
if [ ${#adds[@]} -gt 0 ]; then
  echo "Actualizando embeddings en el workspace..."
  
  # Construir el JSON manualmente
  json_adds=$(printf ", %s" "${adds[@]}")
  json_adds="[${json_adds:2}]"  # Eliminar la primera coma

  curl -X POST $BASE_URL/api/v1/workspace/$WORKSPACE/update-embeddings \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"adds\": $json_adds, \"deletes\": []}"

  echo "Embeddings actualizados para los documentos: ${adds[@]}"
else
  echo "No se cargaron archivos, no se actualizarán embeddings."
fi

# Esperar a que alguno de los procesos finalice
wait -n
exit $?
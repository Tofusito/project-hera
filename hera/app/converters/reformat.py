import os
import json
import requests
from typing import Optional
import logging

def process_documents(input_dir: str, output_dir: str, ollama_service, logger: logging.Logger):
    """
    Recorre todos los archivos .txt y .json en input_dir, los envía a la API de Ollama
    para adaptarlos o reformatearlos según corresponda y guarda los resultados en output_dir,
    incluyendo el prompt utilizado para cada archivo.

    :param input_dir: Directorio donde se encuentran los archivos originales.
    :param output_dir: Directorio donde se guardarán los archivos procesados.
    :param ollama_service: Instancia de OllamaService para realizar solicitudes a la API.
    :param logger: Instancia de logger para registrar el proceso.
    """
    logger.info(f"Inicio del procesamiento de documentos. Input: '{input_dir}', Output: '{output_dir}'")

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Directorio de salida creado: {output_dir}")
        except Exception as e:
            logger.error(f"❌ No se pudo crear el directorio de salida '{output_dir}': {e}")
            return

    for root, dirs, files in os.walk(input_dir):
        logger.info(f"Explorando directorio: {root}")
        for file in files:
            if file.lower().endswith(('.txt', '.json')):
                ruta_archivo = os.path.join(root, file)
                logger.info(f"Procesando archivo: {ruta_archivo}")

                try:
                    # Leer el contenido del archivo como texto plano
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    logger.info(f"Contenido cargado (primeros 200 caracteres): {contenido[:200]}...")

                    if not contenido.strip():
                        logger.warning(f"⚠️ El archivo '{ruta_archivo}' está vacío o no contiene contenido válido.")
                        continue

                    # Preparar el prompt para Ollama
                    prompt = (
                        "A continuación se presenta contenido que necesita ser limpiado y reformateado. "
                        "Por favor, realiza las siguientes acciones:\n"
                        "1. Elimina cualquier dato redundante.\n"
                        "2. Corrige errores ortográficos y de formato.\n"
                        "3. Mantén la misma estructura y formato del archivo original.\n"
                        "Devuelve únicamente el contenido limpio y reformateado entre los marcadores [INICIO] y [FIN], todo en una sola línea si es posible.\n\n"
                        "[INICIO]\n"
                        f"{contenido}\n"
                        "[FIN]"
                    )
                    logger.info(f"Prompt preparado para reformatear: {prompt[:200]}...")  # Muestra los primeros 200 caracteres del prompt
                    logger.info(f"Enviando a la API de Ollama...")

                    # Guardar el prompt en un archivo dentro de output_dir
                    nombre_prompt = f"prompt_{os.path.splitext(file)[0]}.txt"
                    ruta_prompt = os.path.join(output_dir, nombre_prompt)
                    try:
                        with open(ruta_prompt, 'w', encoding='utf-8') as f_prompt:
                            f_prompt.write(prompt)
                        logger.info(f"✅ Prompt guardado en: {ruta_prompt}")
                    except Exception as e:
                        logger.error(f"❌ Error al guardar el prompt: {ruta_prompt}. Detalles: {e}")
                        # Opcional: Puedes decidir si continuar o no en caso de error al guardar el prompt
                        # continue

                    # Enviar la solicitud a Ollama
                    respuesta = ollama_service.make_request(prompt)
                    logger.info(f"Respuesta recibida de Ollama (tipo: {type(respuesta)}): {respuesta}")

                    if respuesta:
                        logger.info(f"Procesando respuesta para el archivo: {ruta_archivo}")

                        # Extraer el contenido de la respuesta
                        if isinstance(respuesta, dict):
                            if 'message' in respuesta and 'content' in respuesta['message']:
                                contenido_str = respuesta['message']['content']
                                logger.info(f"Contenido extraído de 'message' -> 'content': {contenido_str[:200]}...")
                            else:
                                logger.error(f"❌ La estructura de la respuesta no contiene 'message' -> 'content' para el archivo: {ruta_archivo}")
                                logger.info(f"Estructura completa de la respuesta: {respuesta}")
                                continue
                        elif isinstance(respuesta, str):
                            # Extraer solo el contenido entre los marcadores si están presentes
                            inicio = respuesta.find("[INICIO]") + len("[INICIO]")
                            fin = respuesta.find("[FIN]")
                            if inicio != -1 and fin != -1:
                                contenido_str = respuesta[inicio:fin].strip()
                                logger.info(f"Contenido extraído entre marcadores: {contenido_str[:200]}...")
                            else:
                                contenido_str = respuesta.strip()
                                logger.info(f"Respuesta es una cadena. Contenido: {contenido_str[:200]}...")
                        else:
                            logger.error(f"❌ Respuesta de la API en formato inesperado para el archivo: {ruta_archivo} (tipo: {type(respuesta)})")
                            continue

                        # Preparar la ruta de salida para el archivo de texto reformateado
                        nombre_salida = os.path.splitext(file)[0] + "_reformateado.txt"
                        ruta_salida = os.path.join(output_dir, nombre_salida)
                        logger.info(f"Guardando contenido reformateado en: {ruta_salida}")

                        # Guardar la respuesta en un archivo de texto
                        try:
                            with open(ruta_salida, 'w', encoding='utf-8') as f_salida:
                                f_salida.write(contenido_str)
                            logger.info(f"✅ Archivo reformateado guardado en: {ruta_salida}")
                        except Exception as e:
                            logger.error(f"❌ Error al guardar el archivo reformateado: {ruta_salida}. Detalles: {e}")
                    else:
                        logger.error(f"❌ No se pudo procesar el archivo: {ruta_archivo}. La API devolvió una respuesta vacía.")

                except Exception as e:
                    logger.error(f"❌ Error al procesar el archivo '{ruta_archivo}': {e}", exc_info=True)

import os
import logging
import shutil


def process_documents(input_dir: str, output_dir: str, ollama_service, logger: logging.Logger):
    """
    Recorre todos los archivos en input_dir, los envía a la API de Ollama para adaptarlos o reformatearlos según corresponda y guarda los resultados en output_dir.

    :param input_dir: Directorio donde se encuentran los archivos originales.
    :param output_dir: Directorio donde se guardaran los archivos procesados.
    :param ollama_service: Instancia de OllamaService para realizar solicitudes a la API.
    :param logger: Instancia de logger para registrar el proceso.
    """
    logger.info(f"Inicio del procesamiento de documentos. Input: '{input_dir}', Output: '{output_dir}'")

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Directorio de salida creado: {output_dir}")
        except Exception as e:
            logger.error(f"No se pudo crear el directorio de salida '{output_dir}': {e}")
            return

    for root, _, files in os.walk(input_dir):
        for file in files:
            ruta_archivo = os.path.join(root, file)
            logger.info(f"Procesando archivo: {ruta_archivo}")

            try:
                if file.lower().endswith('.txt'):
                    # Procesar archivos .txt con la API de Ollama
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        contenido = f.read()

                    if not contenido.strip():
                        logger.warning(f"El archivo '{ruta_archivo}' está vacío o no contiene contenido válido.")
                        continue

                    # Prompt optimizado para la API de Ollama
                    prompt = (
                        "Por favor procesa el siguiente contenido entre [INICIO] y [FIN] usando un razonamiento de cadena de pensamiento para obtener el mejor resultado:\n"
                        "1. Primero analiza el contenido identificando cualquier redundancia, error gramatical o formato inconsistente.\n"
                        "2. Luego, realiza una limpieza eliminando datos redundantes, frases repetitivas y texto innecesario.\n"
                        "3. Corrige todos los errores ortográficos y de gramática detectados.\n"
                        "4. Reformatea el contenido para que sea claro, conciso y consistente, sin cambiar su significado.\n"
                        "5. Finalmente, revisa el contenido limpio para asegurar que sea coherente y directo.\n"
                        "6. Devuelve únicamente el contenido limpio y reformateado, sin ninguna explicación adicional, sin análisis, sin comentarios, sin marcas, sin adornos.\n"
                        "[INICIO]\n"
                        f"{contenido}\n"
                        "[FIN]"
                    )
                    logger.info(f"Enviando a la API de Ollama...")

                    # Enviar la solicitud a Ollama
                    respuesta = ollama_service.make_request(prompt)

                    if isinstance(respuesta, str) and respuesta.strip():
                        contenido_str = respuesta.strip()
                        nombre_salida = os.path.splitext(file)[0] + "_reformateado.txt"
                        ruta_salida = os.path.join(output_dir, nombre_salida)

                        with open(ruta_salida, 'w', encoding='utf-8') as f_salida:
                            f_salida.write(contenido_str)

                        logger.info(f"Archivo reformateado guardado en: {ruta_salida}")

                        # Borrar el archivo original después de ser reformateado
                        os.remove(ruta_archivo)
                        logger.info(f"Archivo original '{ruta_archivo}' eliminado después del reformateo.")
                    else:
                        logger.error(f"No se pudo procesar el archivo: {ruta_archivo}. Respuesta vacía o inesperada.")

                elif file.lower().endswith(('.csv', '.xlsx')):
                    # Mover archivos .csv y .xlsx sin procesar
                    ruta_salida = os.path.join(output_dir, file)
                    shutil.move(ruta_archivo, ruta_salida)
                    logger.info(f"Archivo '{file}' movido a: {ruta_salida}")

                else:
                    # Eliminar archivos que no sean .txt, .csv, o .xlsx
                    os.remove(ruta_archivo)
                    logger.info(f"Archivo '{ruta_archivo}' no es compatible y ha sido eliminado.")

            except Exception as e:
                logger.error(f"Error al procesar el archivo '{ruta_archivo}': {e}", exc_info=True)
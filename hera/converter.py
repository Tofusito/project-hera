import os
import subprocess
import mimetypes
from load_and_embed import load_and_embed_documents
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import hashlib

# Directorio de documentos
DIRECTORY = "/app/documentos/input"

# Directorio para almacenar los archivos procesados
DESTINATION_DIR = "/app/documentos/converted"

# Número máximo de hilos concurrentes
MAX_WORKERS = 10

# Crear el directorio de destino si no existe
os.makedirs(DESTINATION_DIR, exist_ok=True)

# Definir las extensiones de archivos según el tipo
IMAGE_EXTENSIONS = {'.jpeg', '.jpg', '.png'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
CODE_EXTENSIONS = {
    '.py', '.java', '.js', '.c', '.cpp', '.cs', '.rb', '.go', '.php',
    '.yaml', '.yml', '.hcl', '.ts', '.swift', '.kt', '.rs', '.scala',
    '.pl', '.sh', '.bat', '.ps1', '.lua', '.sql'
}
TEXT_EXTENSIONS = {'.txt', '.md'}
PDF_EXTENSION = '.pdf'

def generate_unique_filename(original_path, extension):
    """
    Genera un nombre de archivo único basado en el hash MD5 del path completo.
    """
    base_name = os.path.basename(original_path).rsplit('.', 1)[0]
    unique_suffix = hashlib.md5(original_path.encode()).hexdigest()[:8]
    return f"{base_name}_{unique_suffix}{extension}"

def convert_pdf_to_txt(file_path):
    """
    Convierte un archivo PDF a TXT utilizando pdftotext.
    Mueve el archivo TXT al directorio de destino si la conversión es exitosa.
    """
    try:
        txt_file_name = generate_unique_filename(file_path, '.txt')
        output_file = os.path.join(DESTINATION_DIR, txt_file_name)
        command = ['pdftotext', file_path, output_file]
        
        # Ejecutar el comando de conversión
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0 and os.path.exists(output_file):
            os.remove(file_path)
            print(f"Convertido y eliminado: {file_path} -> {output_file}")
            return output_file
        else:
            print(f"Error al convertir: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error en pdftotext para {file_path}: {e.stderr.decode().strip()}")
        return None
    except Exception as e:
        print(f"Error inesperado al convertir {file_path}: {e}")
        return None

def delete_image(file_path):
    """
    Elimina archivos de imagen (JPEG o PNG).
    """
    try:
        os.remove(file_path)
        print(f"Imagen eliminada: {file_path}")
    except Exception as e:
        print(f"Error al eliminar imagen {file_path}: {e}")

def process_audio(file_path):
    """
    Función placeholder para procesar archivos de audio en el futuro.
    """
    print(f"Archivo de audio encontrado (pendiente de procesamiento): {file_path}")
    pass  # Implementar en el futuro

def copy_code_file(file_path):
    """
    Copia archivos de código al directorio de destino.
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        code_file_name = generate_unique_filename(file_path, file_extension)
        destination_file = os.path.join(DESTINATION_DIR, code_file_name)
        shutil.copy2(file_path, destination_file)
        print(f"Archivo de código copiado: {file_path} -> {destination_file}")
    except Exception as e:
        print(f"Error al copiar archivo de código {file_path}: {e}")

def move_text_file(file_path):
    """
    Mueve archivos de texto (.txt) y markdown (.md) al directorio de destino.
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        text_file_name = generate_unique_filename(file_path, file_extension)
        destination_file = os.path.join(DESTINATION_DIR, text_file_name)
        shutil.move(file_path, destination_file)
        print(f"Archivo de texto/mardown movido: {file_path} -> {destination_file}")
    except Exception as e:
        print(f"Error al mover archivo de texto/mardown {file_path}: {e}")

def process_file(file_path):
    """
    Procesa un solo archivo según su tipo:
    - Si es PDF, lo convierte a TXT y mueve el TXT al directorio de destino.
    - Si es una imagen JPEG o PNG, la elimina.
    - Si es un archivo de audio, llama a la función placeholder.
    - Si es un archivo de código, lo copia al directorio de destino.
    - Si es un archivo de texto o markdown, lo mueve al directorio de destino.
    - Otros tipos de archivos se ignoran.
    """
    try:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == PDF_EXTENSION:
            convert_pdf_to_txt(file_path)
        elif ext in IMAGE_EXTENSIONS:
            delete_image(file_path)
        elif ext in AUDIO_EXTENSIONS:
            process_audio(file_path)
        elif ext in CODE_EXTENSIONS:
            copy_code_file(file_path)
        elif ext in TEXT_EXTENSIONS:
            move_text_file(file_path)
        else:
            print(f"Archivo ignorado (tipo no manejado): {file_path}")
    except Exception as e:
        print(f"Error al procesar {file_path}: {e}")

def convert_and_process_documents():
    """
    Recorre todos los archivos en el directorio y subdirectorios,
    procesándolos con un pool de hilos limitado a MAX_WORKERS.
    """
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        # Recorrer todos los directorios y subdirectorios
        for root, dirs, files in os.walk(DIRECTORY):
            for file in files:
                file_path = os.path.join(root, file)
                futures.append(executor.submit(process_file, file_path))
        
        # Esperar a que todos los hilos terminen y manejar excepciones si es necesario
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Excepción en hilo: {e}")
    
    # Llamar al script de carga y embebido una vez que todo ha sido procesado
    load_and_embed_documents()

if __name__ == "__main__":
    convert_and_process_documents()

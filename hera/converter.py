import os
import subprocess
import mimetypes
from load_and_embed import load_and_embed_documents

# Directorio de documentos
DIRECTORY = "/app/documentos"

# Función para convertir archivos a txt
def convert_to_txt(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type == 'application/pdf':
        output_file = file_path.replace('.pdf', '.txt')
        command = ['pdftotext', file_path, output_file]
    else:
        output_file = file_path.replace(os.path.splitext(file_path)[1], '.txt')
        command = ['iconv', '-f', 'utf-8', '-t', 'utf-8', file_path, '-o', output_file]

    subprocess.run(command)
    os.remove(file_path)  # Eliminar el archivo original
    return output_file

# Función para revisar y convertir archivos
def convert_and_process_documents():
    for file_name in os.listdir(DIRECTORY):
        file_path = os.path.join(DIRECTORY, file_name)
        if os.path.isfile(file_path) and not file_path.endswith('.txt'):
            print(f"Convirtiendo archivo: {file_path}")
            txt_file = convert_to_txt(file_path)
            print(f"Archivo convertido a: {txt_file}")
    
    # Llamar al script de carga y embebido
    load_and_embed_documents()

if __name__ == "__main__":
    convert_and_process_documents()

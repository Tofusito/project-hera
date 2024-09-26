# app/converters/converter.py

import os
import shutil
import subprocess
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.file_utils import generate_unique_filename
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Converter:
    def __init__(self, input_dir, output_dir, max_workers=10):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.pdf_extension = '.pdf'
        self.image_extensions = {'.jpeg', '.jpg', '.png'}
        self.audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        self.code_extensions = {
            '.py', '.java', '.js', '.c', '.cpp', '.cs', '.rb', '.go', '.php',
            '.yaml', '.yml', '.hcl', '.ts', '.swift', '.kt', '.rs', '.scala',
            '.pl', '.sh', '.bat', '.ps1', '.lua', '.sql'
        }
        self.text_extensions = {'.txt', '.md'}
        os.makedirs(self.output_dir, exist_ok=True)

    def convert_pdf_to_txt(self, file_path):
        try:
            txt_file_name = generate_unique_filename(file_path, '.txt')
            output_file = os.path.join(self.output_dir, txt_file_name)
            command = ['pdftotext', file_path, output_file]
            
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0 and os.path.exists(output_file):
                os.remove(file_path)
                logger.info(f"Convertido y eliminado: {file_path} -> {output_file}")
                return output_file
            else:
                logger.error(f"Error al convertir: {file_path}")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en pdftotext para {file_path}: {e.stderr.decode().strip()}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al convertir {file_path}: {e}")
            return None

    def delete_image(self, file_path):
        try:
            os.remove(file_path)
            logger.info(f"Imagen eliminada: {file_path}")
        except Exception as e:
            logger.error(f"Error al eliminar imagen {file_path}: {e}")

    def process_audio(self, file_path):
        logger.info(f"Archivo de audio encontrado (pendiente de procesamiento): {file_path}")
        # Implementar procesamiento de audio en el futuro

    def copy_code_file(self, file_path):
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            code_file_name = generate_unique_filename(file_path, file_extension)
            destination_file = os.path.join(self.output_dir, code_file_name)
            shutil.copy2(file_path, destination_file)
            logger.info(f"Archivo de código copiado: {file_path} -> {destination_file}")
        except Exception as e:
            logger.error(f"Error al copiar archivo de código {file_path}: {e}")

    def move_text_file(self, file_path):
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            text_file_name = generate_unique_filename(file_path, file_extension)
            destination_file = os.path.join(self.output_dir, text_file_name)
            shutil.move(file_path, destination_file)
            logger.info(f"Archivo de texto/markdown movido: {file_path} -> {destination_file}")
        except Exception as e:
            logger.error(f"Error al mover archivo de texto/markdown {file_path}: {e}")

    def process_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == self.pdf_extension:
            self.convert_pdf_to_txt(file_path)
        elif ext in self.image_extensions:
            self.delete_image(file_path)
        elif ext in self.audio_extensions:
            self.process_audio(file_path)
        elif ext in self.code_extensions:
            self.copy_code_file(file_path)
        elif ext in self.text_extensions:
            self.move_text_file(file_path)
        else:
            logger.info(f"Archivo ignorado (tipo no manejado): {file_path}")

    def convert_and_process_documents(self):
        logger.info("Iniciando conversión y procesamiento de documentos...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.process_file, os.path.join(root, file))
                for root, _, files in os.walk(self.input_dir)
                for file in files
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Excepción en hilo: {e}")
        logger.info("Conversión y procesamiento de documentos completados.")

import os
import re
import shutil
import subprocess
import pandas as pd
import json
from docx import Document
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.file_utils import generate_unique_filename
from utils.logger import setup_logger
import zipfile
import time

logger = setup_logger(__name__)

class Converter:
    def __init__(self, input_dir, output_dir, max_workers=10):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.max_workers = max_workers
        os.makedirs(self.output_dir, exist_ok=True)

    def convert_pdf_to_txt(self, file_path):
        """Convierte PDF a txt usando PyPDF2"""
        try:
            txt_file_name = generate_unique_filename(file_path, '.txt')
            output_file = os.path.join(self.output_dir, txt_file_name)
            
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                text = ''
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text is not None:
                        text += page_text

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)

            logger.info(f"PDF convertido a texto: {file_path} -> {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error al convertir PDF {file_path}: {e}")
            return None

    def convert_doc_to_txt(self, file_path):
        """Convierte archivos DOCX a texto usando python-docx"""
        try:
            txt_file_name = generate_unique_filename(file_path, '.txt')
            output_file = os.path.join(self.output_dir, txt_file_name)

            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)

            logger.info(f"DOC/DOCX convertido a texto: {file_path} -> {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error al convertir DOC/DOCX {file_path}: {e}")
            return None

    def convert_code_to_txt(self, file_path):
        """Convierte archivos de código (.js, .py) a txt"""
        try:
            txt_file_name = generate_unique_filename(file_path, '.txt')
            output_file = os.path.join(self.output_dir, txt_file_name)

            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code_content)

            logger.info(f"Archivo de código convertido a texto: {file_path} -> {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error al convertir archivo de código {file_path}: {e}")
            return None

    def copy_file(self, file_path):
        """Copia archivos directamente a la carpeta de salida"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            file_name = generate_unique_filename(file_path, file_extension)
            destination_file = os.path.join(self.output_dir, file_name)

            shutil.copy(file_path, destination_file)
            logger.info(f"Archivo copiado: {file_path} -> {destination_file}")
            return destination_file
        except Exception as e:
            logger.error(f"Error al copiar archivo {file_path}: {e}")
            return None

    def process_file(self, file_path):
        """Determina el tipo de archivo y lo convierte a txt o markdown, luego lo elimina"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        success = False

        if ext == '.pdf':
            success = self.convert_pdf_to_txt(file_path) is not None
        elif ext in ['.doc', '.docx']:
            success = self.convert_doc_to_txt(file_path) is not None
        elif ext in ['.js', '.py']:
            success = self.convert_code_to_txt(file_path) is not None
        elif ext in ['.xls', '.xlsx', '.md', '.txt', '.json']:
            success = self.copy_file(file_path) is not None
        else:
            logger.info(f"Formato no soportado: {file_path}")

        # Si el archivo fue procesado correctamente, lo eliminamos
        if success:
            retry_count = 3
            for attempt in range(retry_count):
                try:
                    os.remove(file_path)
                    logger.info(f"Archivo eliminado: {file_path}")
                    break
                except Exception as e:
                    logger.error(f"Error al eliminar el archivo {file_path}, intento {attempt + 1} de {retry_count}: {e}")
                    time.sleep(1)  # Espera un segundo antes de volver a intentar

    def remove_empty_dirs(self, dir_path):
        """Elimina recursivamente los directorios vacíos"""
        for root, dirs, files in os.walk(dir_path, topdown=False):
            if not files and not dirs:
                try:
                    os.rmdir(root)
                    logger.info(f"Directorio vacío eliminado: {root}")
                except OSError as e:
                    logger.error(f"No se pudo eliminar el directorio {root}: {e}")

    def convert_and_process_documents(self):
        logger.info("Iniciando conversión de documentos...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batch_size = 10
            files = [os.path.join(root, file) for root, _, files in os.walk(self.input_dir) for file in files]
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                futures = [executor.submit(self.process_file, file) for file in batch]

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Excepción en hilo: {e}")

        self.remove_empty_dirs(self.input_dir)
        logger.info("Conversión y limpieza completada.")
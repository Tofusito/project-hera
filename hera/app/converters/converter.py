import os
import shutil
import subprocess
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.file_utils import generate_unique_filename
from utils.logger import setup_logger
import zipfile

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
                    text += page.extract_text()

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

    def convert_excel_to_md(self, file_path):
        """Convierte Excel a formato de tabla markdown usando pandas"""
        try:
            # Genera un nombre de archivo único en el formato .md
            md_file_name = generate_unique_filename(file_path, '.md')
            output_file = os.path.join(self.output_dir, md_file_name)
            
            # Abre el archivo Excel especificando 'openpyxl' como motor
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Abre el archivo de salida en modo escritura
            with open(output_file, 'w', encoding='utf-8') as f:
                # Itera sobre cada hoja del archivo Excel
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                    # Verifica si la hoja está vacía
                    if df.empty:
                        logger.info(f"La hoja '{sheet_name}' está vacía en el archivo {file_path}")
                        continue
                    
                    # Escribir el nombre de la hoja como un título de sección en Markdown
                    f.write(f"# Hoja: {sheet_name}\n\n")
                    
                    # Convertir el DataFrame a Markdown
                    md_table = df.to_markdown(index=False)
                    f.write(md_table)
                    f.write("\n\n")

            logger.info(f"Excel convertido a tabla markdown: {file_path} -> {output_file}")
            return output_file
        except zipfile.BadZipFile:
            logger.error(f"Error: El archivo no es un archivo .xlsx válido (no es un archivo ZIP): {file_path}")
        except ImportError as e:
            logger.error(f"Error: Falta la dependencia opcional 'tabulate'. Instala la librería usando pip: {e}")
        except Exception as e:
            logger.error(f"Error al convertir Excel {file_path}: {e}")
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
        elif ext in ['.xls', '.xlsx']:
            success = self.convert_excel_to_md(file_path) is not None
        elif ext in ['.md', '.txt']:
            success = self.copy_file_to_root(file_path) is not None
        else:
            logger.info(f"Formato no soportado: {file_path}")

        # Si el archivo fue procesado correctamente, lo eliminamos
        if success:
            try:
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
            except Exception as e:
                logger.error(f"Error al eliminar el archivo {file_path}: {e}")

    def copy_file_to_root(self, file_path):
        """Copia el archivo de texto tal cual a la raíz de output_dir"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            file_name = generate_unique_filename(file_path, file_extension)
            destination_file = os.path.join(self.output_dir, file_name)
            
            shutil.copy2(file_path, destination_file)
            logger.info(f"Archivo copiado: {file_path} -> {destination_file}")
            return destination_file
        except Exception as e:
            logger.error(f"Error al copiar archivo {file_path}: {e}")
            return None

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
        
        self.remove_empty_dirs(self.input_dir)
        logger.info("Conversión y limpieza completada.")

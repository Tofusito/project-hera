import os
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

    def convert_excel_to_json(self, file_path):
        """Convierte archivos Excel a JSON usando pandas"""
        try:
            # Generar un nombre de archivo único para el archivo JSON
            json_file_name = generate_unique_filename(file_path, '.json')
            output_file = os.path.join(self.output_dir, json_file_name)
            
            logger.debug(f"Archivo de salida JSON: {output_file}")

            # Leer el archivo Excel con pandas
            df_dict = pd.read_excel(file_path, sheet_name=None)  # sheet_name=None lee todas las hojas
            logger.debug(f"Hojas encontradas en el Excel: {list(df_dict.keys())}")

            if not df_dict:
                logger.warning(f"No se encontraron hojas en el archivo Excel: {file_path}")
                return None

            result = {}
            for sheet_name, sheet_data in df_dict.items():
                logger.debug(f"Procesando hoja: {sheet_name}")

                if sheet_data.empty:
                    logger.warning(f"La hoja '{sheet_name}' está vacía.")
                    result[sheet_name] = []
                    continue

                # Verificar las columnas y filas
                logger.debug(f"Columnas en '{sheet_name}': {list(sheet_data.columns)}")
                logger.debug(f"Número de filas en '{sheet_name}': {len(sheet_data)}")
                logger.debug(f"Primeras filas de '{sheet_name}':\n{sheet_data.head()}")

                # Opcional: Ajustar encabezados si es necesario
                # sheet_data = pd.read_excel(file_path, sheet_name=sheet_name, header=1)  # Por ejemplo, si los encabezados están en la segunda fila

                # Reemplazar NaN con valores nulos para JSON
                sheet_data = sheet_data.fillna('')  # O usa sheet_data.where(pd.notnull(sheet_data), None) para nulos
                result[sheet_name] = sheet_data.to_dict(orient='records')

            # Verificar el contenido de 'result' antes de guardar
            logger.debug(f"Contenido a guardar en JSON:\n{json.dumps(result, ensure_ascii=False, indent=4)[:500]}...")  # Muestra solo los primeros 500 caracteres

            # Guardar la salida en formato JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

            logger.info(f"Excel convertido a JSON: {file_path} -> {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error al convertir Excel {file_path}: {e}", exc_info=True)
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
            success = self.convert_excel_to_json(file_path) is not None
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


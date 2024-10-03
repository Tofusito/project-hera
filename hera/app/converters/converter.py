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

    def convert_excel_to_csv(self, file_path):
        """Convierte archivos Excel a CSV usando pandas, con limpieza exhaustiva de datos."""
        try:
            # Leer todas las hojas del archivo Excel
            df_dict = pd.read_excel(file_path, sheet_name=None)
            logger.debug(f"Hojas encontradas en el Excel: {list(df_dict.keys())}")

            if not df_dict:
                logger.warning(f"No se encontraron hojas en el archivo Excel: {file_path}")
                return None

            csv_files = []

            for sheet_name, sheet_data in df_dict.items():
                logger.debug(f"Procesando hoja: {sheet_name}")

                if sheet_data.empty:
                    logger.warning(f"La hoja '{sheet_name}' está vacía.")
                    continue

                # Limpieza exhaustiva de datos
                cleaned_data = self._clean_dataframe(sheet_data)
                
                # Generar nombre de archivo único para el CSV
                csv_file_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_{sheet_name}.csv"
                output_file = os.path.join(self.output_dir, csv_file_name)
                
                logger.debug(f"Archivo de salida CSV: {output_file}")

                # Guardar el DataFrame limpio como CSV
                cleaned_data.to_csv(output_file, index=False, encoding='utf-8')
                logger.info(f"Excel convertido a CSV: {file_path} -> {output_file}")

                csv_files.append(output_file)

            return csv_files

        except Exception as e:
            logger.error(f"Error al convertir Excel {file_path} a CSV: {e}", exc_info=True)
            return None

    def _clean_dataframe(self, df):
        """Realiza una limpieza exhaustiva del DataFrame."""
        # Hacer una copia para no modificar el original
        cleaned_df = df.copy()
        
        # 1. Manejo de valores nulos
        # Identificar columnas numéricas y no numéricas
        numeric_columns = cleaned_df.select_dtypes(include=['int64', 'float64']).columns
        non_numeric_columns = cleaned_df.select_dtypes(exclude=['int64', 'float64']).columns
        
        # Reemplazar nulos en columnas numéricas con 0
        cleaned_df[numeric_columns] = cleaned_df[numeric_columns].fillna(0)
        
        # Reemplazar nulos en columnas no numéricas con string vacío
        cleaned_df[non_numeric_columns] = cleaned_df[non_numeric_columns].fillna('')
        
        # 2. Eliminar filas y columnas completamente vacías
        cleaned_df.dropna(how='all', inplace=True)
        cleaned_df.dropna(axis=1, how='all', inplace=True)
        
        # 3. Limpieza de strings
        for column in non_numeric_columns:
            cleaned_df[column] = cleaned_df[column].astype(str).apply(self._clean_string)
        
        # 4. Normalización de fechas
        date_columns = cleaned_df.select_dtypes(include=['datetime64']).columns
        for column in date_columns:
            cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 5. Eliminar duplicados
        cleaned_df.drop_duplicates(inplace=True)
        
        # 6. Normalización de nombres de columnas
        cleaned_df.columns = [self._normalize_column_name(col) for col in cleaned_df.columns]
        
        return cleaned_df

    def _clean_string(self, s):
        """Limpia y normaliza strings."""
        if not isinstance(s, str):
            return s
        # Eliminar espacios extra y caracteres especiales
        s = re.sub(r'\s+', ' ', s.strip())
        # Eliminar caracteres no imprimibles
        s = ''.join(char for char in s if char.isprintable())
        return s

    def _normalize_column_name(self, column_name):
        """Normaliza los nombres de las columnas."""
        # Convertir a minúsculas y reemplazar espacios por guiones bajos
        normalized = re.sub(r'\s+', '_', column_name.lower().strip())
        # Eliminar caracteres especiales
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        return normalized

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
            success = self.convert_excel_to_csv(file_path) is not None
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


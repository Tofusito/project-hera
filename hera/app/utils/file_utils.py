# app/utils/file_utils.py

import os

def generate_unique_filename(original_path, extension):
    """
    Genera un nombre de archivo único basado en el hash MD5 del path completo.
    """
    base_name = os.path.basename(original_path).rsplit('.', 1)[0]
    return f"{base_name}{extension}"

import os
import zipfile
from .logger import setup_logger

logger = setup_logger()

def extract_zip(
    path_zip: str,
    path_out=None,
    delete_zip: bool=True
):
    try:
        if not zipfile.is_zipfile(path_zip):
            logger.warning(f"O arquivo '{path_zip}' nao eh um arquivo zip. Seguindo sem descompactar.")
            return None

        zip_directory = os.path.dirname(path_zip) if not path_out else path_out
        zip_name = os.path.basename(path_zip)
        folder_name = os.path.splitext(zip_name)[0]
        extract_path = os.path.join(zip_directory, folder_name)

        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        with zipfile.ZipFile(path_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        if delete_zip:
            os.remove(path_zip)
        return extract_path
    except FileNotFoundError:
        logger.error(f"O arquivo '{path_zip}' nao foi encontrado.")
        raise FileNotFoundError(f"O arquivo '{path_zip}' nao foi encontrado.")

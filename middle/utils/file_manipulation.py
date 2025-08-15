import pdb  # noqa: F401
import os
import io
import zipfile
import shutil
from .logger import setup_logger

logger = setup_logger()

def extract_zip(
    arquivo_zip: str,
    nome_zip: str = None,
    path_out=None,
    delete_zip: bool=True
):
    try:
        if isinstance(arquivo_zip, bytes):
            zip_file = io.BytesIO(arquivo_zip)
        else:
            zip_file = arquivo_zip
        if not zipfile.is_zipfile(zip_file):
            logger.warning(f"O arquivo '{zip_file}' nao eh um arquivo zip. Seguindo sem descompactar.")
            return None

        zip_directory = os.path.dirname(zip_file) if not path_out else path_out
        nome_zip = os.path.basename(zip_file) if not nome_zip else nome_zip
        folder_name = os.path.splitext(nome_zip)[0]
        extract_path = os.path.join(zip_directory, folder_name)

        shutil.rmtree(extract_path, ignore_errors=True)
        if os.path.exists: 
            try: 
                os.remove(extract_path)
            except: 
                pass   
                 
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        if delete_zip and type(zip_file) is str:
            os.remove(zip_file)
        return extract_path
    except FileNotFoundError:
        logger.error(f"O arquivo '{zip_file}' nao foi encontrado.")
        raise FileNotFoundError(f"O arquivo '{zip_file}' nao foi encontrado.")
    
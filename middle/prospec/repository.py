import requests
from ..utils import (
    setup_logger, Constants, get_auth_header
)

constants = Constants()

logger = setup_logger()

def get_ids_estudos():
    res = requests.get(
        f"{constants.BASE_URL}/estudos-middle/api/prospec/base-studies",
        headers=get_auth_header()
        )
    if res.status_code != 200 or not res.json():
        logger.error("Erro ao buscar estudos base")
        res.raise_for_status()
    return res.json()


def download_estudo(id_estudo: str):
    res = requests.get(
        f"{constants.BASE_URL}/estudos-middle/api/prospec/study/{id_estudo}/download",
        headers=get_auth_header()
    )
    if res.status_code != 200:
        logger.error(f"Erro ao baixar estudo {id_estudo}: {res.text}")
        res.raise_for_status()
    
    
    logger.info(f"Estudo {id_estudo} baixado com sucesso.")
    return {"content": res.content, "filename": res.headers.get("content-disposition").split("filename=")[-1].strip('"')}



def upload_estudo(id_estudo: str, paths_modified: list, tag: str):
    url = f"{constants.BASE_URL}/estudos-middle/api/prospec/study/{id_estudo}/update-study"
    files = []
    for path in paths_modified:
        files.append(('files', open(path, 'rb')))
    data = {'tag': tag}
    headers = get_auth_header()
    response = requests.post(url, files=files, data=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Erro ao enviar arquivos para o estudo {id_estudo}: {response.text}")
        response.raise_for_status()
    logger.info(f"Arquivos enviados com sucesso para o estudo {id_estudo}.")
    return response.json()


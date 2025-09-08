import os
import requests
import datetime
from .utils import (
    get_auth_header,
    Constants,
)
constants = Constants()

def infer_file_extension(data: bytes) -> str:
    signatures = [
        (b"%PDF", "pdf"),
        (b"\x89PNG\r\n\x1a\n", "png"),
        (b"\xFF\xD8\xFF", "jpg"),
        (b"GIF8", "gif"),
        (b"\x49\x44\x33", "mp3"),
        (b"\xFF\xFB", "mp3"),
        (b"PK\x03\x04", "zip"),
    ]

    for sig, ext in signatures:
        if data.startswith(sig):
            return ext
    return "bin"

def download_from_s3(id_produto: str, filename: str, path_download: str) -> str:
    auth = get_auth_header()
    
    res = requests.get(
        f"{constants.BASE_URL}/webhook/api/webhooks/{id_produto}/download", 
        headers=auth
    )
    if res.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do S3: {res.text}")
        
    file_content = requests.get(res.json()['url'])
    if file_content.status_code != 200:
        raise Exception(f"Erro ao obter conteúdo do arquivo: {file_content.text}")
    
    content = file_content.content
    # ext = infer_file_extension(content)
    
    filename = os.path.basename(filename).strip().replace("/", "_").replace("\\", "_")
    filename = filename[filename.rfind('/')+1:]
    os.makedirs(path_download, exist_ok=True)
    filename = os.path.join(path_download, f"{filename}")
    with open(filename, 'wb') as f:
        f.write(content)
    return filename


def handle_webhook_file(webhook_payload: dict, path_download: str) -> str:
    return download_from_s3(webhook_payload['id'], webhook_payload['nome'], path_download)


def get_latest_webhook_product(
    nome_produto: str,
    data: datetime.date = datetime.date.today(),
    date_range:int = 35,
) -> dict:
    
    """Busca um produto especifico no webhook, disponivel nos ultimos x dias.

    Args:
        nome_produto (str): nome do produto a ser buscado(mesmo nome disponibilizado pela sintegre).
        data (datetime.date, optional): data maxima de publicacao do produto Defaults to today.
        date_range (int, optional): Quantidade de dias para tras a buscar o produto Defaults to 35.

    Returns:
        dict: dicionario com todos os produtos encontrados no periodo selecionado.
    """
    res = requests.get(
        f"{constants.BASE_URL}/webhook/api/webhooks/timeline/filtered",
        {"nome": nome_produto,
         "startDate": data - datetime.timedelta(days=date_range)},
        headers=get_auth_header()
    )
    if res.status_code == 200:
        return res.json()['groups'][0]['events']
    else:
        raise Exception(
            f"Erro ao buscar dados: {res.status_code} - {res.text}")
        

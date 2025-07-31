import os
import requests
import datetime
from .utils import (
    get_auth_header,
    constants,
)

def handle_webhook_file(webhook_payload: dict, path_download: str) -> str:
    filename = os.path.join(path_download, webhook_payload['nome'])
    auth = get_auth_header()
    
    res = requests.get(
        f"{constants.BASE_URL}/webhook/api/webhooks/{
            webhook_payload['id']}/download", 
        headers=auth
    )
    if res.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do S3: {res.text}")
        
    file_content = requests.get(res.json()['url'])
    with open(filename, 'wb') as f:
        f.write(file_content.content)
    return filename


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
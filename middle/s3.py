import os
import requests
from .utils import (
    get_auth_header,
    constants,
)

def handle_webhook_file(webhook_payload: dict, path_download: str) -> str:
    filename = os.path.join(path_download, webhook_payload['filename'])
    auth = get_auth_header()
    
    res = requests.get(
        f"{constants}/webhook/api/webhooks/{
            webhook_payload['webhookId']}/download", 
        headers=auth
    )
    if res.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do S3: {res.text}")
        
    file_content = requests.get(res.json()['url'])
    with open(filename, 'wb') as f:
        f.write(file_content.content)
    return filename
import os
import requests
from ..utils.auth import get_auth_header
from ..utils.logger import setup_logger

logger = setup_logger()


def send_whatsapp_message(destinatario: str, mensagem: str, arquivo):
    url = os.getenv("WHATSAPP_API")
    if not url:
        logger.error("Variavel de ambiente WHATSAPP_API nao esta definida")
        raise Exception("Variavel de ambiente WHATSAPP_API nao esta definida")

    fields = {
        "destinatario": destinatario,
        "mensagem": mensagem,
    }
    headers = get_auth_header()
    files = {}
    if arquivo:
        files = {"arquivo": (arquivo, open(arquivo, "rb"))}
    response = requests.post(url, data=fields, files=files, headers=headers)
    print("Status Code:", response.status_code)

import os
import requests
from ..utils.auth import get_auth_header


def send_whatsapp_message(destinatario: str, mensagem: str, arquivo):
    url = os.getenv("WHATSAPP_API", "http://localhost:6000/whatsapp-message")
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

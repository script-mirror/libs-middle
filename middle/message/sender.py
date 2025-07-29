import os
import requests
from typing import List
from ..utils.auth import get_auth_header
from ..utils.logger import setup_logger

logger = setup_logger()


def send_whatsapp_message(destinatario: str, mensagem: str, arquivo):
    """
    Envia uma mensagem via WhatsApp para o destinatário especificado.

    Args:
        destinatario (str): Número de telefone do destinatário.
        mensagem (str): Texto da mensagem a ser enviada.
        arquivo: Caminho do arquivo (str) ou objeto de arquivo para anexar, ou None.

    Raises:
        Exception: Se a variável de ambiente BASE_URL não estiver definida.
    """
    url = os.getenv("BASE_URL")
    if not url:
        logger.error("Variavel de ambiente WHATSAPP_API nao esta definida")
        raise Exception("Variavel de ambiente WHATSAPP_API nao esta definida."
                        "Utilize o load_env() para carregar as variáveis de ambiente.")

    fields = {
        "destinatario": destinatario,
        "mensagem": mensagem,
    }
    headers = get_auth_header()
    files = {}
    if arquivo:
        if type(arquivo) is str:
            files = {"arquivo": (arquivo, open(arquivo, "rb"))}
        else:
            files = {"arquivo": ("arquivo.jpg", arquivo)}
    response = requests.post(url, data=fields, files=files, headers=headers)
    logger.info(f"WhatsApp message sent to {destinatario}. Status Code: {response.status_code}")

def send_email_message(
    destinatario: List[str],
    mensagem: str,
    arquivos: list = None,
    user: str = None,
    assunto: str = "Middle"
    ):
    """
    Envia um e-mail para os destinatários especificados.

    Args:
        destinatario (List[str]): Lista de e-mails dos destinatários.
        mensagem (str): Texto da mensagem do e-mail.
        arquivos (list, optional): Lista de arquivos para anexar. Default é None.
        user (str, optional): Usuário remetente do e-mail. Default é None.
        assunto (str, optional): Assunto do e-mail. Default é "Middle".

    """
    url = os.getenv("BASE_URL")
    url = f"{url}/estudos-middle/api/email/send"

    payload = {
        "destinatario": destinatario,
        "assunto": assunto,
        "mensagem": mensagem,
    }
    if user is not None:
        payload["user"] = user
    if arquivos is not None:
        payload["arquivos"] = arquivos if isinstance(arquivos, list) else [arquivos]

    headers = get_auth_header()
    response = requests.post(url, json=payload, headers=headers)
    logger.info(f"Email sent to {destinatario} with subject '{assunto}'. Status Code: {response.status_code}")



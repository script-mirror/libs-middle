import requests
from ..utils.auth import get_auth_header
from ..utils.logger import setup_logger
from ..utils import Constants

constants = Constants()


logger = setup_logger()


def send_whatsapp_message(destinatario: str, mensagem: str, arquivo = None):
    """
    Envia uma mensagem via WhatsApp para o destinatário especificado.

    Args:
        destinatario (str): Número de telefone do destinatário.
        mensagem (str): Texto da mensagem a ser enviada.
        arquivo: Caminho do arquivo (str) ou objeto de arquivo para anexar, ou None.

    Raises:
        Exception: Se a variável de ambiente BASE_URL não estiver definida.
    """
    url = constants.BASE_URL
    if not url:
        logger.error("Variavel de ambiente WHATSAPP_API nao esta definida")
        raise Exception("Variavel de ambiente WHATSAPP_API nao esta definida."
                        "Utilize o load_env() para carregar as variáveis de ambiente.")
    url = f"{url}/bot-whatsapp/whatsapp-message"

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
    logger.info(f"Mensagem WhatsApp enviada para {destinatario}. Status Code: {response.status_code}")
    return response

def send_email_message(
    user: str = constants.EMAIL_CLIME,
    destinatario = constants.EMAIL_MIDDLE,
    mensagem: str = "",
    assunto: str = "Middle",
    arquivos = [],
    ):
    """
    Envia um e-mail para os destinatários especificados.

    Args:
        user (str, optional): Usuário remetente do e-mail. Default é None.
        destinatario (List[str]): Lista de e-mails dos destinatários.
        mensagem (str): Texto da mensagem do e-mail.
        assunto (str, optional): Assunto do e-mail. Default é "Middle".
        arquivos (list, optional): Lista de arquivos para anexar. Default é None.

    """
    url = constants.BASE_URL
    if not url:
        logger.error("Arquivo .env não carregado ou BASE_URL não definida.")
        raise Exception("Arquivo .env não carregado ou BASE_URL não definida. "
                        "Utilize o load_env() para carregar as variáveis de ambiente.")
    url = f"{url}/estudos-middle/api/email/send"
    if type(destinatario) is str:
        destinatario = [destinatario]
    fields = {
        "destinatario": ",".join(destinatario),
        "assunto": assunto,
        "mensagem": mensagem,
    }
    if user is not None:
        fields["user"] = user
    files = []
    for arquivo in arquivos:
        files.append(("arquivos", open(arquivo, "rb")))

    headers = get_auth_header()
    response = requests.post(url, data=fields, files=files, headers=headers)
    logger.info(f"E-mail enviado para {destinatario} com assunto '{assunto}'. Status Code: {response.status_code}")
    if not (200 <= response.status_code < 300):
        logger.error(f"Falha ao enviar e-mail. Campos: {fields}")
        logger.error(f"Texto da resposta: {response.text}")

    return response

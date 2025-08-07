from ..utils import Constants
from ..message import send_whatsapp_message

constants = Constants()

def enviar_whatsapp_erro(
    dag_id: str,
    task_id: str,
    destinatario: str,
):
    """
    Envia uma mensagem de erro via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    mensagem, = f"❌ Erro na DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

def enviar_whatsapp_sucesso(
    dag_id: str,
    destinatario: str,
):
    """
    Envia uma mensagem de sucesso via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    mensagem = f"✅ Sucesso na DAG: *{dag_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

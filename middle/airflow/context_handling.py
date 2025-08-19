from ..utils import Constants
from ..message import send_whatsapp_message

constants = Constants()

def enviar_whatsapp_erro(
    context: dict,
):
    """
    Envia uma mensagem de erro via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    dag_id = context.get('dag_id')
    task_id = context.get('task_id')
    destinatario = context.get('destinatario')
    mensagem, = f"❌ Erro na DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

def enviar_whatsapp_sucesso(
    context: dict,
):
    """
    Envia uma mensagem de sucesso via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    dag_id = context.get('dag_id')
    task_id = context.get('task_id')
    destinatario = context.get('destinatario')
    mensagem = f"✅ Sucesso na DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

from ..utils import constants
from ..message import send_whatsapp_message

def enviar_whatsapp_error(context):
    """
    Envia uma mensagem de erro via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id
    task_id = task_instance.task_id
    destinatario = context.get("destinatario", constants.WHATSAPP_AIRFLOW)
    mensagem = f"❌ Erro na DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

def enviar_whatsapp_sucesso(context):
    """
    Envia uma mensagem de sucesso via WhatsApp para o destinatário configurado.

    Args:
        context: Argumentos adicionais que podem ser passados para a função.
    """
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id
    destinatario = context.get("destinatario", constants.WHATSAPP_AIRFLOW)
    mensagem = f"✅ Sucesso na DAG: *{dag_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

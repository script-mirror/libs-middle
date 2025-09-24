from ..utils import Constants
from ..message import send_whatsapp_message

constants = Constants()

def enviar_whatsapp_erro(
    context=None,
    **kwargs
):
    """
    Envia uma mensagem de erro via WhatsApp para o destinatário configurado.

    Args:
        kwargs: Argumentos adicionais que podem ser passados para a função.
    """
    if context:
        dag_id = context.get('dag_run').dag_id if context.get('dag_run') else context.get('dag_id')
        task_id = context.get('task_instance').task_id if context.get('task_instance') else context.get('task_id')
        destinatario = context.get('destinatario', 'airflow')
    else:
        dag_id = kwargs.get('dag_id')
        task_id = kwargs.get('task_id')
        destinatario = kwargs.get('destinatario', 'airflow')
    
    mensagem = f"❌ DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

def enviar_whatsapp_sucesso(
    context=None,
    **kwargs
):
    """
    Envia uma mensagem de sucesso via WhatsApp para o destinatário configurado.

    Args:
        kwargs: Argumentos adicionais que podem ser passados para a função.
    """
    if context:
        dag_id = context.get('dag_run').dag_id if context.get('dag_run') else context.get('dag_id')
        task_id = context.get('task_instance').task_id if context.get('task_instance') else context.get('task_id')
        destinatario = context.get('destinatario', 'airflow')
    else:
        dag_id = kwargs.get('dag_id')
        task_id = kwargs.get('task_id')
        destinatario = kwargs.get('destinatario', 'airflow')
    
    mensagem = f"✅ DAG: *{dag_id}*\nTask: *{task_id}*"
    send_whatsapp_message(destinatario, mensagem, None)

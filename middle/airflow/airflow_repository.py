import pytz
import requests
import datetime
from ..utils import Constants, setup_logger

logger = setup_logger()
constants = Constants()

def auth_airflow():
    logger.info("Attempting Airflow authentication")
    auth_url = f"{constants.BASE_URL}/airflow-middle/auth/token"
    auth_data = {
        "username": constants.USER_AIRFLOW,
        "password": constants.PASSWORD_AIRFLOW,
    }
    
    auth_data = {
        "username": 'airflow',
        "password": 'raizen',
    }
    print(auth_data)
    logger.debug(f"Sending auth request to {auth_url} with username {constants.USER_AIRFLOW}")
    try:
        response = requests.post(auth_url, json=auth_data)
        logger.debug(f"Received response with status code {response.status_code}")
        if response.status_code >= 200 and response.status_code < 300:
            token = response.json().get("access_token")
            logger.info("Airflow authentication successful")
            return {"Authorization": f"Bearer {token}"}
        else:
            logger.error(f"Airflow authentication failed: {response.text}")
            raise Exception(f"Falha na autenticação com o Airflow {response.text}")
    except Exception as e:
        logger.error(f"Error during Airflow authentication: {str(e)}")
        raise

def trigger_dag(
    dag_id: str,
    conf: dict={},
):
    logger.info(f"Triggering DAG {dag_id}")
    trigger_dag_url = f"{constants.BASE_URL}/airflow-middle/api/v2/dags/{dag_id}/dagRuns"
    json = {"conf": conf}
    
    if "execution_date" in conf:
        execution_date_str = conf.pop("execution_date")
        try:
            if isinstance(execution_date_str, str) and len(execution_date_str) == 10:
                execution_date = datetime.datetime.strptime(execution_date_str, '%Y-%m-%d')
                execution_date = execution_date.replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
                
            elif isinstance(execution_date_str, datetime.datetime):
                execution_date = execution_date_str
                if execution_date.tzinfo is None:
                    execution_date = execution_date.replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
                    
            else:
                raise ValueError(f"Formato de data inválido: {execution_date_str}")
                
            json["logical_date"] = execution_date.isoformat()
            logger.info(f"Usando data de execução personalizada: {json['logical_date']}")
        except Exception as e:
            logger.warning(f"Erro ao processar execution_date: {str(e)}. Usando data atual.")
            json["logical_date"] = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()
    else:
        json["logical_date"] = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()()
    logger.debug(f"Sending trigger request to {trigger_dag_url} with config {json}")
    try:
        answer = requests.post(trigger_dag_url, json=json, headers=auth_airflow())
        logger.info(f"DAG {dag_id} trigger response: {answer.status_code}")
        logger.debug(f"Response content: {answer.text}")
        return answer
    except Exception as e:
        logger.error(f"Error triggering DAG {dag_id}: {str(e)}")
        raise

def auth_airflow_legado():
    logger.info("Attempting legacy Airflow authentication")
    try:
        auth = requests.auth.HTTPBasicAuth(constants.USER_AIRFLOW, constants.PASSWORD_AIRFLOW)
        logger.debug(f"Legacy auth created for user {constants.USER_AIRFLOW}")
        return auth
    except Exception as e:
        logger.error(f"Error during legacy Airflow authentication: {str(e)}")
        raise

def trigger_dag_legada(
    dag_id: str,
    conf: dict={},
):
    logger.info(f"Triggering legacy DAG {dag_id}")
    trigger_dag_url = f"{constants.BASE_URL}/airflow/api/v1/dags/{dag_id}/dagRuns"
    json = {"conf": conf}
    logger.debug(f"Sending legacy trigger request to {trigger_dag_url} with config {json}")
    try:
        answer = requests.post(trigger_dag_url, json=json, auth=auth_airflow_legado())
        logger.info(f"Legacy DAG {dag_id} trigger response: {answer.status_code}")
        logger.debug(f"Response content: {answer.text}")
        return answer
    except Exception as e:
        logger.error(f"Error triggering legacy DAG {dag_id}: {str(e)}")
        raise
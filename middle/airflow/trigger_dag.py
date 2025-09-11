import pytz
import requests
import datetime
from ..utils import Constants

constants = Constants()


def auth_airflow():
    auth_url = f"{constants.BASE_URL}/airflow-middle/auth/token"
    auth_data = {
        "username": constants.USER_AIRFLOW,
        "password": constants.PASSWORD_AIRFLOW,
    }
    response = requests.post(auth_url, json=auth_data)
    if response.status_code >= 200 and response.status_code < 300:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    else:
        raise Exception("Falha na autenticação com o Airflow")

def trigger_airflow_dag(
    dag_id: str,
    conf: dict={},
):

    trigger_dag_url = f"{constants.BASE_URL}/airflow-middle/dags/{dag_id}/dagRuns"
    json = {"conf": conf}

    json["logical_date"] = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat()
    answer = requests.post(trigger_dag_url, json=json, headers=auth_airflow())
    return answer
    
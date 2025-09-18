import os
import time
import requests
from .auth import get_auth_header
from .logger import setup_logger
from ._constants import Constants
from typing import Optional, Dict, Any

logger = setup_logger()
constants = Constants()

def _check_image_generation_status(job_id: str) -> requests.Response:
    URL_HTML_TO_IMAGE: Optional[str] = constants.URL_HTML_TO_IMAGE
    if not URL_HTML_TO_IMAGE:
        logger.error("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
        raise Exception("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
    response: requests.Response = requests.get(
        f"{URL_HTML_TO_IMAGE}/job/{job_id}",
        headers=get_auth_header()
    )
    return response


def _get_image(job_id: str) -> Optional[bytes]:
    URL_HTML_TO_IMAGE: Optional[str] = constants.URL_HTML_TO_IMAGE
    if not URL_HTML_TO_IMAGE:
        logger.error("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
        raise Exception("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
    response: requests.Response = requests.get(
        f"{URL_HTML_TO_IMAGE}/job/{job_id}/image",
        headers=get_auth_header()
    )
    logger.info(f"get image {response.status_code}")
    if response.status_code < 200 or response.status_code >= 300:
        return None
    return response.content


def html_to_image(
    html_str: str,
) -> Optional[bytes]:
    URL_HTML_TO_IMAGE: Optional[str] = constants.URL_HTML_TO_IMAGE
    if not URL_HTML_TO_IMAGE:
        logger.error("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
        raise Exception("Variavel de ambiente URL_HTML_TO_IMAGE nao definida")
    payload: Dict[str, Any] = {
        "html": html_str,
        "options": {
            "type": "png",
            "quality": 100,
            "trim": True,
            "deviceScaleFactor": 1,
            "background": True
        }
    }

    response: requests.Response = requests.post(
        URL_HTML_TO_IMAGE, headers=get_auth_header(), json=payload
    )

    # Check initial response status
    if response.status_code < 200 or response.status_code >= 300:
        raise Exception(f"Erro ao gerar imagem: {response.status_code}")

    job_data: Dict[str, Any] = response.json()
    job_id: str = job_data['jobId']

    while True:
        status_response: requests.Response = _check_image_generation_status(
            job_id
        )
        status_data: Dict[str, Any] = status_response.json()
        if status_data['status'] == 'completed':
            break
        logger.info(f"Aguardando processamento da imagem {job_id}")
        time.sleep(1)

    image: Optional[bytes] = _get_image(job_id)
    return image

from datetime import datetime, timedelta
import requests
import pandas as pd
import os
import re
import random
import time
import socket
from ._constants import Constants, setup_logger
from typing import Optional
logger = setup_logger()
constants = Constants()

def get_decks_ccee(
    path: str,
    deck: str,
    file_name: str,
    dtAtual: datetime = datetime.now(),
    numDiasHistorico: int = 35,
    max_retries: int = 3
) -> Optional[str]:
    
    session = None
    try:
        # Detectar ambiente
        is_container = (
            os.path.exists('/.dockerenv') or 
            os.environ.get('AIRFLOW_HOME') is not None or
            'airflow' in os.environ.get('HOSTNAME', '').lower()
        )
        
        logger.info(f"Ambiente: {'Container' if is_container else 'Local'}")
        
        if is_container:
            max_retries = max(max_retries, 10)  # Aumentar tentativas
            base_delay = 300  # 5 minutos base
            timeout_request = 600  # 10 minutos
            initial_delay = random.uniform(120, 300)  # 2-5 minutos inicial
        else:
            base_delay = 60
            timeout_request = 120
            initial_delay = random.uniform(10, 30)
        
        logger.info(f"Delay inicial: {initial_delay:.1f}s")
        time.sleep(initial_delay)
        
        # Criar sessão com configurações mais robustas
        session = requests.Session()
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # User agents mais variados e atuais
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        user_agent = random.choice(user_agents)
        
        # Headers mais completos para a página inicial
        initial_headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        # 1. Visitar página inicial
        logger.info("Visitando página inicial...")
        main_response = session.get(
            'https://www.ccee.org.br/', 
            headers=initial_headers, 
            timeout=timeout_request
        )
        main_response.raise_for_status()
        
        # Delay após página inicial
        time.sleep(random.uniform(5, 15))
        
        # 2. Navegar para página do acervo
        logger.info("Navegando para página do acervo...")
        acervo_headers = initial_headers.copy()
        acervo_headers['Referer'] = 'https://www.ccee.org.br/'
        
        acervo_response = session.get(
            'https://www.ccee.org.br/web/guest/acervo-ccee',
            headers=acervo_headers,
            timeout=timeout_request
        )
        acervo_response.raise_for_status()
        
        # Delay maior entre navegação e busca
        navigation_delay = random.uniform(15, 45) if is_container else random.uniform(5, 15)
        logger.info(f"Delay navegação: {navigation_delay:.1f}s")
        time.sleep(navigation_delay)
        
        # Headers para a busca AJAX
        search_headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.ccee.org.br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.ccee.org.br/web/guest/acervo-ccee',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # Parâmetros e dados da requisição
        dtFinal_str = dtAtual.strftime('%d/%m/%Y')
        dtInicial_str = (dtAtual - timedelta(days=numDiasHistorico)).strftime('%d/%m/%Y')
        
        params = {
            'p_p_id': 'org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_cacheability': 'cacheLevelPage',
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_param1': 'Value1',
        }

        data = {
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_resultadosPagina': '10',
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_keyword': deck,
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_numberPage': '0',
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_initialDate': dtInicial_str,
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_finalDate': dtFinal_str,
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_fc': ''
        }

        # Fazer a busca com retry mais inteligente
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Delay exponencial mais agressivo
                    if is_container:
                        delay = min(1800, base_delay * (2 ** attempt))  # Máx 30min
                    else:
                        delay = base_delay * (attempt + 1)
                    
                    logger.info(f"Tentativa {attempt + 1}: aguardando {delay}s...")
                    time.sleep(delay)
                    
                    # Renovar sessão a cada 3 tentativas
                    if attempt % 3 == 0:
                        logger.info("Renovando sessão...")
                        session.close()
                        session = requests.Session()
                        user_agent = random.choice(user_agents)
                        search_headers['User-Agent'] = user_agent
                        
                        # Refazer navegação
                        time.sleep(random.uniform(30, 60))
                        main_response = session.get('https://www.ccee.org.br/', headers=initial_headers)
                        time.sleep(random.uniform(10, 20))
                        acervo_response = session.get('https://www.ccee.org.br/web/guest/acervo-ccee', headers=acervo_headers)
                        time.sleep(random.uniform(20, 40))

                # Delay aleatório antes da requisição
                pre_request_delay = random.uniform(10, 30) if is_container else random.uniform(2, 8)
                time.sleep(pre_request_delay)

                logger.info(f"Fazendo busca - tentativa {attempt + 1}/{max_retries}")

                response = session.post(
                    'https://www.ccee.org.br/web/guest/acervo-ccee',
                    headers=search_headers,
                    params=params,
                    data=data,
                    timeout=timeout_request
                )
                
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden - tentativa {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise requests.exceptions.HTTPError(f"403 Forbidden após {max_retries} tentativas")
                
                response.raise_for_status()
                logger.info(f"Busca bem-sucedida! Status: {response.status_code}")
                break
                
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt == max_retries - 1:
                    raise

        # Resto do código permanece igual...
        # (parsing JSON, download do arquivo, etc.)
        
    except Exception as e:
        logger.error(f"Erro em get_decks_ccee: {str(e)}")
        raise
    finally:
        if session:
            session.close()
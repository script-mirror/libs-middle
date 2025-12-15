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

def get_user_agents():
    return [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]

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
        # Detectar se está rodando em container
        is_container = (
            os.path.exists('/.dockerenv') or 
            os.environ.get('AIRFLOW_HOME') is not None or
            'airflow' in os.environ.get('HOSTNAME', '').lower() or
            'container' in os.environ.get('HOSTNAME', '').lower()
        )
        
        logger.info(f"Ambiente detectado: {'Container/Airflow' if is_container else 'Local'}")
        
        if is_container:
            max_retries = max(max_retries, 8)
            base_delay = 180  # 3 minutos base
            timeout_request = 300  # 5 minutos
            timeout_download = 600  # 10 minutos
            initial_delay = random.uniform(60, 120)  # 1-2 minutos inicial
            
            logger.info(f"Aguardando {initial_delay:.1f}s inicial (container)...")
            time.sleep(initial_delay)
        else:
            base_delay = 30
            timeout_request = 60
            timeout_download = 120
            initial_delay = 0
        
        dtFinal_str = dtAtual.strftime('%d/%m/%Y')
        dtInicial_str = (dtAtual - timedelta(days=numDiasHistorico)).strftime('%d/%m/%Y')
        
        user_agent = random.choice(get_user_agents())
        logger.info(f"User-Agent selecionado: {user_agent}")

        # Criar sessão para manter cookies
        session = requests.Session()
        
        # Headers iniciais para estabelecer sessão
        initial_headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

        # Primeiro, visitar a página principal para estabelecer cookies de sessão
        logger.info("Estabelecendo sessão com CCEE...")
        main_response = session.get(
            'https://www.ccee.org.br/web/guest/acervo-ccee', 
            headers=initial_headers, 
            timeout=timeout_request
        )
        main_response.raise_for_status()
        
        logger.info(f"Cookies recebidos: {len(session.cookies)} cookies")
        for cookie in session.cookies:
            logger.info(f"Cookie: {cookie.name}={cookie.value[:50]}...")

        initial_wait = random.uniform(10, 25) if is_container else random.uniform(1, 3)
        logger.info(f"Aguardando {initial_wait:.1f}s...")
        time.sleep(initial_wait)

        headers = {
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.ccee.org.br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.ccee.org.br/web/guest/acervo-ccee',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }

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

        logger.info(f"Buscando documentos: {deck}")
        logger.info(f"Período: {dtInicial_str} até {dtFinal_str}")

        # Make POST request with retries
        for attempt in range(max_retries):
            try:
                # Delay exponencial mais agressivo no servidor
                if attempt > 0:
                    if is_container:
                        # Servidor: delays maiores (3min, 6min, 12min, 20min)
                        delay = min(1200, base_delay * (2 ** attempt))
                    else:
                        # Local: delays menores (30s, 60s, 90s)
                        delay = base_delay * (attempt + 1)
                    
                    logger.info(f"Aguardando {delay} segundos antes da tentativa {attempt + 1}...")
                    time.sleep(delay)
                
                # Delay aleatório adicional
                random_delay = random.uniform(15, 35) if is_container else random.uniform(2, 8)
                logger.info(f"Delay aleatório adicional: {random_delay:.1f}s")
                time.sleep(random_delay)

                logger.info(f"Iniciando tentativa {attempt + 1}/{max_retries}...")

                response = session.post(
                    'https://www.ccee.org.br/web/guest/acervo-ccee',
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=timeout_request
                )
                
                # REMOVIDO: import pdb; pdb.set_trace()
                logger.info(f"Tentativa {attempt + 1}: Status response: {response.status_code}")
                
                if response.status_code == 403:
                    logger.warning(f"Erro 403 - tentativa {attempt + 1}/{max_retries}")
                    logger.warning(f"Response headers: {dict(response.headers)}")
                    logger.warning(f"Response content: {response.text[:500]}")
                    
                    # Tentar reestabelecer a sessão
                    if attempt < max_retries - 1:
                        logger.info("Reestabelecendo sessão...")
                        session.cookies.clear()
                        
                        # Novo User-Agent para reestabelecimento
                        new_user_agent = random.choice(get_user_agents())
                        initial_headers['User-Agent'] = new_user_agent
                        headers['User-Agent'] = new_user_agent
                        
                        main_response = session.get(
                            'https://www.ccee.org.br/web/guest/acervo-ccee', 
                            headers=initial_headers, 
                            timeout=timeout_request
                        )
                        
                        # REMOVIDO: pdb.set_trace()
                        
                        # Espera extra após reestabelecer sessão
                        session_wait = random.uniform(30, 60) if is_container else random.uniform(3, 8)
                        logger.info(f"Aguardando {session_wait:.1f}s após reestabelecer sessão...")
                        time.sleep(session_wait)
                    continue
                
                response.raise_for_status()
                break
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch data after {max_retries} attempts: {str(e)}")

        # Parse JSON response
        try:
            data_response = response.json()
            logger.info(f"JSON parsed successfully. Results: {len(data_response.get('results', []))}")
        except ValueError as e:
            logger.error(f"Response content: {response.text[:1000]}")
            raise ValueError(f"Failed to parse JSON response: {str(e)}")

        # Create DataFrame and filter
        df_produtos = pd.DataFrame(data_response.get('results', []))
        if df_produtos.empty:
            raise ValueError("No results found in the response.")

        df_produto = df_produtos[df_produtos['nomeDocumentoList'].str.contains(file_name, case=False, na=False)]
        if df_produto.empty:
            raise ValueError(f"No files found matching '{file_name}'.")

        # Get the URL of the first matching file
        url = df_produto['url'].iloc[0]
        selected_row = df_produto.iloc[0]
        
        # Tentar encontrar o arquivo mais recente ou com formato correto
        for index, row in df_produto.iterrows():
            if len(str(row['nomeComplementar']).split("-")) == 2:
                url = row['url']
                selected_row = row
                logger.info(f"Found document: {row['nomeComplementar']}")
                break
        
        logger.info(f"Selected document: {selected_row['nomeComplementar']}")
        logger.info(f"Downloading file from URL: {url}")
              
        # Ensure the directory exists
        os.makedirs(path, exist_ok=True)

        # Download the file
        file_name_safe = url.split("/")[-1]  # Usar o nome do arquivo da URL
        if not file_name_safe or file_name_safe == '':
            file_name_safe = url.split("/")[-2] + ".zip"
        
        # Sanitizar nome do arquivo
        file_name_safe = re.sub(r'[<>:"/\\|?*]', '_', file_name_safe)
        path_full = os.path.join(path, file_name_safe)

        # Download com a mesma sessão
        for attempt in range(max_retries):
            try:
                download_headers = {
                    'User-Agent': user_agent,  # Usar o mesmo User-Agent
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.ccee.org.br/web/guest/acervo-ccee',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin'
                }
                
                response = session.get(url, headers=download_headers, timeout=timeout_download, stream=True)
                response.raise_for_status()
                
                with open(path_full, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Download completed: {path_full}")
                return path_full
                
            except (requests.RequestException, requests.Timeout) as e:
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to download file after {max_retries} attempts: {str(e)}")

    except Exception as e:
        logger.error(f"Error in get_decks_ccee: {str(e)}")
        raise RuntimeError(f"Failed to process request: {str(e)}")

    finally:
        if session:
            session.close()

    return None

if __name__ == '__main__':
    try:
        result = get_decks_ccee(
            path=constants.PATH_ARQUIVOS_TEMP,
            deck='dessem',
            file_name='Deck de Preços - Dessem'
        )
        if result:
            print(f"Successfully downloaded file to: {result}")
        else:
            print("Download failed.")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
from datetime import datetime, timedelta
import requests
import pandas as pd
import os
import re
import time
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
        dtFinal_str = dtAtual.strftime('%d/%m/%Y')
        dtInicial_str = (dtAtual - timedelta(days=numDiasHistorico)).strftime('%d/%m/%Y')

        # Criar sessão para manter cookies
        session = requests.Session()
        
        # Headers iniciais para estabelecer sessão
        initial_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }

        # Primeiro, visitar a página principal para estabelecer cookies de sessão
        logger.info("Estabelecendo sessão com CCEE...")
        main_response = session.get(
            'https://www.ccee.org.br/web/guest/acervo-ccee', 
            headers=initial_headers, 
            timeout=30
        )
        main_response.raise_for_status()
        
        logger.info(f"Cookies recebidos: {len(session.cookies)} cookies")
        for cookie in session.cookies:
            logger.info(f"Cookie: {cookie.name}={cookie.value[:50]}...")

        # Aguardar um pouco para simular comportamento humano
        time.sleep(2)

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
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
                # Aguardar entre tentativas
                if attempt > 0:
                    delay = 30 * (attempt + 1)  # 30, 60, 90 segundos
                    logger.info(f"Aguardando {delay} segundos antes da tentativa {attempt + 1}...")
                    time.sleep(delay)

                response = session.post(
                    'https://www.ccee.org.br/web/guest/acervo-ccee',
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=60
                )
                
                logger.info(f"Tentativa {attempt + 1}: Status response: {response.status_code}")
                
                if response.status_code == 403:
                    logger.warning(f"Erro 403 - tentativa {attempt + 1}/{max_retries}")
                    logger.warning(f"Response headers: {dict(response.headers)}")
                    logger.warning(f"Response content: {response.text[:500]}")
                    
                    # Tentar reestabelecer a sessão
                    if attempt < max_retries - 1:
                        logger.info("Reestabelecendo sessão...")
                        session.cookies.clear()
                        main_response = session.get(
                            'https://www.ccee.org.br/web/guest/acervo-ccee', 
                            headers=initial_headers, 
                            timeout=30
                        )
                        time.sleep(5)
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
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
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
                
                response = session.get(url, headers=download_headers, timeout=120, stream=True)
                response.raise_for_status()
                
                with open(path_full, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Download completed: {path_full}")
                return path_full        # Define POST data

                
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
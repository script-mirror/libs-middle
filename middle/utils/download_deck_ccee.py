from datetime import datetime, timedelta
import requests
import pandas as pd
import os
from _constants import Constants, setup_logger
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
    
    try:
        # Format date strings
        dtFinal_str = dtAtual.strftime('%d/%m/%Y')
        dtInicial_str = (dtAtual - timedelta(days=numDiasHistorico)).strftime('%d/%m/%Y')

        # Define headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,en-US;q=0.7,en;q=0.3',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'ADRUM': 'isAjax:true',
            'Origin': 'https://www.ccee.org.br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.ccee.org.br/web/guest/acervo-ccee',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        # Define query parameters
        params = (
            ('p_p_id', 'org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm'),
            ('p_p_lifecycle', '2'),
            ('p_p_state', 'normal'),
            ('p_p_mode', 'view'),
            ('p_p_cacheability', 'cacheLevelPage'),
            ('_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_param1', 'Value1'),
        )

        # Define POST data
        data = {
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_resultadosPagina': '50',
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_keyword': deck,
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_numberPage': '0',
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_initialDate': dtInicial_str,
            '_org_ccee_acervo_portlet_CCEEAcervoPortlet_INSTANCE_tixm_finalDate': dtFinal_str
        }

        # Make POST request with retries
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'https://www.ccee.org.br/web/guest/acervo-ccee',
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=10
                )
                response.raise_for_status()  # Raise exception for bad status codes
                break
            except (requests.RequestException, requests.Timeout) as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch data after {max_retries} attempts: {str(e)}")

        # Parse JSON response
        try:
            data = response.json()
        except ValueError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")

        # Create DataFrame and filter
        df_produtos = pd.DataFrame(data.get('results', []))
        if df_produtos.empty:
            raise ValueError("No results found in the response.")

        df_produto = df_produtos[df_produtos['nomeDocumentoList'].str.contains(file_name, case=False, na=False)]
        if df_produto.empty:
            raise ValueError(f"No files found matching '{file_name}'.")

        # Get the URL of the first matching file
        url = df_produto['url'].iloc[0]

        # Ensure the directory exists
        os.makedirs(path, exist_ok=True)

        # Download the file
        file_name_safe = url.split("/")[-2].replace("/", "_")  # Sanitize filename
        path_full = os.path.join(path, file_name_safe)

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                with open(path_full, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Download completed: {path_full}")
                return path_full
            except (requests.RequestException, requests.Timeout) as e:
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to download file after {max_retries} attempts: {str(e)}")

    except Exception as e:
        logger.error(f"Error in get_decks_ccee: {str(e)}")
        raise RuntimeError(f"Failed to process request: {str(e)}")

    return None

if __name__ == '__main__':
    try:
        result = get_decks_ccee(
            path=constants.PATH_ARQUIVOS_TEMP,
            deck='decomp',
            file_name='Deck de Preços - Decomp'
        )
        if result:
            print(f"Successfully downloaded file to: {result}")
        else:
            print("Download failed.")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
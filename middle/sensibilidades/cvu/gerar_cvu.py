import datetime
import requests
import pandas as pd
from utils import constants
from utils.auth import get_auth_header



def get_cvu_trusted(
    tipo_cvu: str,
    data_atualizacao: datetime.datetime
):
    URL_API_RAIZEN = f'{constants.BASE_URL}/api/v2'

    df_cvu = pd.DataFrame()
    response = requests.get(
        params = {
            'dt_atualizacao': data_atualizacao,
            'tipo_cvu': tipo_cvu
        },
        url = f"{URL_API_RAIZEN}/decks/cvu",
        headers=get_auth_header()
    )
    answer = response.json()
    df_cvu = pd.DataFrame(answer)
    
    df_cvu['dt_atualizacao'] = pd.to_datetime(
        df_cvu['dt_atualizacao']
    ).dt.strftime('%Y-%m-%d')

    df_cvu[df_cvu['dt_atualizacao'] == pd.to_datetime(
        data_atualizacao
    ).strftime('%Y-%m-%d')]
        
    df_cvu.dropna(subset=['vl_cvu'], inplace=True)
    df_cvu.drop_duplicates(['cd_usina', 'ano_horizonte'], keep='last', inplace=True)
    return df_cvu
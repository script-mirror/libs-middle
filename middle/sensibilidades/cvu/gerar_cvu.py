import pdb  # noqa: F401
import re
import os
import glob
import datetime
import requests
import pandas as pd
from ...utils import Constants, get_auth_header, extract_zip, setup_logger
from ...utils.auth import get_auth_header
from ..cvu import (
    atualizar_cvu_clast_estrutural,
    atualizar_cvu_clast_conjuntural,
    atualizar_cvu_dadger_decomp,
)
from ...prospec import(
    get_ids_estudos,
    download_estudo,
    upload_estudo,
)
logger = setup_logger()
constants = Constants()


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


def atualizar_cvu_clast_newave(fontes_to_search=None, dt_atualizacao=None, ids_to_modify=None):
    
    for tipo_cvu in fontes_to_search:
        tipo_cvu = tipo_cvu.replace('CCEE_', '')
        
        logger.info(f"Updating CVU in CLAST files for NEWAVE studies: {tipo_cvu}")
        logger.info(f"Date of update: {dt_atualizacao}")
        logger.info(f"IDs to modify: {ids_to_modify}")
        
        paths_modified = []
        tag = [f'CVU {datetime.datetime.now().strftime("%d/%m %H:%M")}']
        if not ids_to_modify:
            ids_to_modify = get_ids_estudos()

        df_cvu = get_cvu_trusted(
            tipo_cvu=tipo_cvu,
            data_atualizacao=dt_atualizacao
        )
        
        for id_estudo in ids_to_modify:
            logger.info(f"Modificando estudo {id_estudo}")

            zip_content = download_estudo(id_estudo)['content']
            extracted_zip_estudo = extract_zip(
                zip_content,
                "/tmp"
            )
            
            estudo_contem_newave = [
                nome for nome in os.listdir(extracted_zip_estudo) 
                if os.path.isdir(os.path.join(extracted_zip_estudo, nome)) 
                and nome.startswith("NW")
            ]
            if not estudo_contem_newave:
                logger.info(f"Estudo {id_estudo} nao possui Newave")
                continue

            clast_to_modify = glob.glob(
                os.path.join(
                    extracted_zip_estudo,
                    "**",
                    "*clast*"
                ),
                recursive=True)
            arquivos_filtrados = [
                arquivo for arquivo in clast_to_modify if not re.search(
                    r'\.0+$', arquivo)]
            if arquivos_filtrados == []:
                logger.warning(
                    f"Não foi encontrado nenhum arquivo clast no estudo {id_estudo}")
                continue
                
            if tipo_cvu.split("_")[0] == 'conjuntural':
                paths_modified += atualizar_cvu_clast_conjuntural(
                    arquivos_filtrados,
                    df_cvu,
                )
            elif tipo_cvu == 'estrutural' or tipo_cvu == 'merchant':
                paths_modified += atualizar_cvu_clast_estrutural(
                    arquivos_filtrados,
                    df_cvu,
                )

            if paths_modified:
                # upload_estudo(id_estudo, paths_modified, tag)
                os.remove(extracted_zip_estudo)
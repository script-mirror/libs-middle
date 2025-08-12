import requests
import datetime
from middle.utils import (
    setup_logger, Constants, get_auth_header
)
logger = setup_logger()
constants = Constants()

def get_carga_decomp(data_produto: datetime.date | None = None):
    params = {}
    if data_produto:
        params['dataProduto'] = data_produto.strftime('%Y-%m-%d')
    res = requests.get(
        constants.BASE_URL + '/api/v2/decks/carga-decomp',
        params=params,
        headers=get_auth_header()
    )
    if res.status_code != 200:
        logger.error(f"Erro {res.status_code} ao buscar carga: {res.text}")
        res.raise_for_status()
    return res.json()

def converter_carga_atualizacao(carga: list):
    """
    Converte dados de carga do formato de entrada para o formato de saída esperado.
    
    Args:
        carga: Lista de dicionários com dados de carga
        
    Returns:
        dict: Dicionário no formato esperado com valor_p1, valor_p2, valor_p3
    """
    logger.info(f"Iniciando conversão de carga com {len(carga) if carga else 0} itens")
    
    if not carga:
        logger.warning("Lista de carga vazia, retornando estrutura vazia")
        return {"valor_p1": {}, "valor_p2": {}, "valor_p3": {}}
    
    patamar_map = {
        "pesado": "valor_p1",
        "medio": "valor_p2", 
        "leve": "valor_p3"
    }
    
    submercado_map = {
        "SE": "1",
        "S": "2", 
        "NE": "3",
        "N": "4"
    }
    
    semanas_operativas = sorted(set(item["semana_operativa"] for item in carga), reverse=True)
    logger.info(f"Semanas operativas encontradas: {semanas_operativas}")
    
    semana_to_num = {semana: str(i + 1) for i, semana in enumerate(semanas_operativas)}
    logger.debug(f"Mapeamento de semanas: {semana_to_num}")
    
    resultado = {"valor_p1": {}, "valor_p2": {}, "valor_p3": {}}
    items_processados = 0
    items_ignorados = 0
    
    for item in carga:
        patamar_key = patamar_map.get(item["patamar"])
        if not patamar_key:
            logger.warning(f"Patamar '{item['patamar']}' não reconhecido, item ignorado")
            items_ignorados += 1
            continue
            
        semana_num = semana_to_num[item["semana_operativa"]]
        submercado_num = submercado_map.get(item["submercado"].upper())
        
        if not submercado_num:
            logger.warning(f"Submercado '{item['submercado']}' não reconhecido, item ignorado")
            items_ignorados += 1
            continue
            
        if semana_num not in resultado[patamar_key]:
            resultado[patamar_key][semana_num] = {}
            
        resultado[patamar_key][semana_num][submercado_num] = int(item["carga"])
        items_processados += 1
        logger.debug(f"Processado: {item['patamar']} - Semana {semana_num} - Submercado {submercado_num} - Carga {item['carga']}")
    
    logger.info(f"Conversão concluída: {items_processados} itens processados, {items_ignorados} itens ignorados")
    return resultado
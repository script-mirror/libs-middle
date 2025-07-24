from typing import List


def cvu_input_generator(raw_cvu: List[dict], weeks: int) -> dict:
    """
    Converte uma lista de dicionários de CVU para o formato adequado.

    Args:
        raw_cvu (List[dict]): Lista de dicionários contendo 'cd_usina' e 'vl_cvu'
        weeks (int): Número de semanas para gerar os valores

    Returns:
        dict: Dicionário no formato:
            {
                'ct': {
                    'cvu': {
                        "<cd_usina>": {"1": <vl_cvu>, "2": <vl_cvu>, ..., "n": <vl_cvu>}
                    }
                }
            }
    """
    result = {'ct': {'cvu': {}}}
    for item in raw_cvu:
        cd_usina = str(item["cd_usina"])
        vl_cvu = item["vl_cvu"]
        result['ct']['cvu'][cd_usina] = {str(i): vl_cvu for i in range(1, weeks + 1)}
    return result

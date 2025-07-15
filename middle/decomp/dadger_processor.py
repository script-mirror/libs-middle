import os
import re
import codecs
import datetime
import pandas as pd
from typing import Dict, List, Tuple, Any, IO
from .constants import info_blocos
from .logger_config import setup_logger

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

logger = None


def leitura_dadger(
    file_path: str
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[int, List[str]]]]:
    global logger
    if logger is None:
        logger = setup_logger(os.path.join(BASE_PATH, 'output', 'log', f"dadger_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    logger.info(f"Starting to read file: {file_path}")

    try:
        file = open(file_path, 'r', encoding='latin-1')
        arquivo = file.readlines()
        file.close()
        logger.debug(f"Successfully read {len(arquivo)} "
                     f"lines from {file_path}")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

    coment: List[str] = []
    comentarios: Dict[str, Dict[int, List[str]]] = {}
    blocos: Dict[str, List[Any]] = {}
    for i_line in range(len(arquivo)):
        line = arquivo[i_line]
        if line[0] == '&':
            coment.append(line)
            logger.debug(f"Found comment line at index {i_line}")
        elif line[0].strip() == '':
            logger.debug(f"Skipping empty line at index {i_line}")
            continue
        else:
            mnemonico = line.split()[0]
            if mnemonico not in info_blocos:
                error_msg = f"Unknown mnemonic {mnemonico} at line {i_line}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            infos_linha = re.split(info_blocos[mnemonico]['regex'], line)
            if len(infos_linha) < 2:
                error_msg = (f"Invalid line format for mnemonic {mnemonico} at"
                             f" line {i_line}")
                logger.error(error_msg)
                raise ValueError(error_msg)

            if mnemonico not in blocos:
                blocos[mnemonico] = []
                comentarios[mnemonico] = {}
                logger.debug(f"Initialized new block for mnemonic {mnemonico}")

            if len(coment) > 0:
                comentarios[mnemonico][len(blocos[mnemonico])] = coment
                logger.debug(f"Stored {len(coment)} comments for {mnemonico}")
                coment = []

            # ultimo termo da lista e o que sobra da expressao regex (/n)
            blocos[mnemonico].append(infos_linha[1:-2])
            logger.debug(f"Added data to block {mnemonico}")

    if len(coment) > 0:
        comentarios[mnemonico][len(blocos[mnemonico])] = coment
        logger.debug(f"Stored final {len(coment)} comments for {mnemonico}")

    df_dadger: Dict[str, pd.DataFrame] = {}
    for mnemonico in blocos:
        try:
            df_dadger[mnemonico] = pd.DataFrame(
                blocos[mnemonico], columns=info_blocos[mnemonico]['campos'])
            logger.debug(f"Created DataFrame for mnemonic {mnemonico} "
                         f"with {len(df_dadger[mnemonico])} rows")
        except Exception as e:
            logger.error("Error creating DataFrame for mnemonic "
                         f"{mnemonico}: {str(e)}")
            raise

    logger.info("File reading completed successfully")
    return df_dadger, comentarios


def escrever_bloco_restricoes(
    file_out: IO[str],
    df_dadger: Dict[str, pd.DataFrame],
    mnemonico_restricao: str,
    submnemonicos_restricao: List[str],
    comentarios: Dict[str, Dict[int, List[str]]]
) -> None:
    global logger
    if logger is None:
        logger = setup_logger(os.path.join(BASE_PATH, 'output', 'log', f"dadger_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))

    logger.debug(f"Writing restrictions block for {mnemonico_restricao}")

    try:
        if mnemonico_restricao == 'HE':
            for index, row in df_dadger[mnemonico_restricao].iterrows():
                if index in comentarios[mnemonico_restricao]:
                    for coment in comentarios[mnemonico_restricao][index]:
                        file_out.write(coment)
                        logger.debug(
                            f"Writing comment for HE at index {index}")
                file_out.write('{}\n'.format(
                    info_blocos[mnemonico_restricao]['formatacao'].format(
                        *row.values).strip()))
                logger.debug(f"Writing HE row at index {index}")

                restricoes_mesma_rhe = df_dadger[mnemonico_restricao].loc[
                    df_dadger[mnemonico_restricao]['id'] == row['id']]

                if row.name == restricoes_mesma_rhe.iloc[-1].name:
                    id_restr = int(row['id'])
                    for mnemon in ['CM']:
                        restricoes_mnemon = df_dadger[mnemon].loc[
                            df_dadger[mnemon]['id'].astype(
                                'int') == id_restr].drop_duplicates()
                        for index, row in restricoes_mnemon.iterrows():
                            if index in comentarios[mnemon]:
                                for coment in comentarios[mnemon][index]:
                                    file_out.write(coment)
                                    logger.debug(
                                        "Writing comment for CM "
                                        f"at index {index}")
                            formatacao = info_blocos[mnemon]['formatacao']
                            linha = formatacao.format(*row.values).strip()
                            file_out.write('{}\n'.format(linha))
                            logger.debug(f"Writing CM row at index {index}")

            if index+1 in comentarios[mnemon]:
                for coment in comentarios[mnemon][index+1]:
                    file_out.write(coment)
                    logger.debug(
                        f"Writing final comment for CM at index {index+1}")

        else:
            for index, row in df_dadger[mnemonico_restricao].iterrows():
                if index in comentarios[mnemonico_restricao]:
                    for coment in comentarios[mnemonico_restricao][index]:
                        file_out.write(coment)
                        logger.debug("Writing comment for "
                                     f"{mnemonico_restricao} at index {index}")
                file_out.write('{}\n'.format(
                    info_blocos[mnemonico_restricao]['formatacao'].format(
                        *row.values).strip()))
                logger.debug(
                    f"Writing {mnemonico_restricao} row at index {index}")
                id_restr = int(row['id'])

                for mnemon in submnemonicos_restricao:
                    restricoes_mnemon = df_dadger[mnemon].loc[
                        df_dadger[mnemon]['id'].astype(
                            'int') == id_restr]

                    for index, row in restricoes_mnemon.iterrows():
                        if index in comentarios[mnemon]:
                            for coment in comentarios[mnemon][index]:
                                file_out.write(coment)
                                logger.debug("Writing comment for "
                                             f"{mnemon} at index {index}")
                        file_out.write('{}\n'.format(
                            info_blocos[mnemon]['formatacao'].format(
                                *row.values).strip()))
                        logger.debug(f"Writing {mnemon} row at index {index}")
    except Exception as e:
        logger.error(f"Error writing restrictions block "
                     f"{mnemonico_restricao}: {str(e)}")
        raise


def escrever_dadger(
    df_dadger: Dict[str, pd.DataFrame],
    comentarios: Dict[str, Dict[int, List[str]]],
    file_path: str,
) -> str:
    global logger
    if logger is None:
        logger = setup_logger(os.path.join(BASE_PATH, 'output', 'log', f"dadger_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))

    logger.info(f"Starting to write dadger file: {file_path}")

    blocos_restricoes: Dict[str, List[str]] = {}
    blocos_restricoes['RE'] = ['LU', 'FU', 'FT', 'FI']
    blocos_restricoes['HQ'] = ['LQ', 'CQ']
    blocos_restricoes['HV'] = ['LV', 'CV']
    blocos_restricoes['HE'] = ['CM']

    bloco_dependentes: Dict[str, List[str]] = {}
    bloco_dependentes['VL'] = ['VU']

    blocos_infos_restricoes: List[str] = []
    for mnemonico_rest in blocos_restricoes:
        blocos_infos_restricoes += blocos_restricoes[mnemonico_rest]

    try:
        file_out = codecs.open(file_path, 'w+', 'utf-8')
        for mnemonico in df_dadger:
            if mnemonico in blocos_restricoes:
                logger.debug(f"Processing restriction block {mnemonico}")
                escrever_bloco_restricoes(
                    file_out, df_dadger, mnemonico,
                    blocos_restricoes[mnemonico], comentarios)

            elif mnemonico in blocos_infos_restricoes:
                logger.debug(f"Skipping block {mnemonico} "
                             f"(part of restrictions)")
                continue

            else:
                for index, row in df_dadger[mnemonico].iterrows():
                    if index in comentarios[mnemonico]:
                        for coment in comentarios[mnemonico][index]:
                            file_out.write(coment)
                            logger.debug(f"Writing comment for {mnemonico} "
                                         f"at index {index}")
                    formatacao = info_blocos[mnemonico]['formatacao']
                    linha = formatacao.format(*row.values).strip()
                    file_out.write('{}\n'.format(linha))
                    logger.debug(f"Writing {mnemonico} row at index {index}")

                    if mnemonico in bloco_dependentes:
                        for dep in bloco_dependentes[mnemonico]:
                            condition = (df_dadger[dep]['id'].astype('int') ==
                                         int(row['id']))
                            mnemon_depend = df_dadger[dep].loc[condition]
                            df_dadger[dep].drop(
                                mnemon_depend.index, inplace=True)
                            logger.debug(
                                f"Removed {len(mnemon_depend)} dependent rows "
                                f"for {dep}")

                            for index, row in mnemon_depend.iterrows():
                                if index in comentarios[dep]:
                                    for coment in comentarios[dep][index]:
                                        file_out.write(coment)
                                        logger.debug(
                                            f"Writing comment for dependent "
                                            f"{dep} at index {index}"
                                        )
                                formatacao = info_blocos[dep]['formatacao']
                                linha = formatacao.format(*row.values).strip()
                                file_out.write('{}\n'.format(linha))
                                logger.debug(
                                    f"Writing dependent {dep} row at index "
                                    f"{index}"
                                )
        file_out.close()
        logger.info(f"Successfully wrote to {file_path}")
        print(file_path)
        return file_path
    except Exception as e:
        logger.error(f"Error writing dadger file {file_path}: {str(e)}")
        raise


# Função para comparar os arquivos e encontrar alterações
def comparar_arquivos(
    original_path: str,
    impresso_path: str,
) -> None:
    global logger
    if logger is None:
        logger = setup_logger(os.path.join(BASE_PATH, 'output', 'log', f"dadger_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))

    logger.info(f"Comparando arquivos: original ({original_path})"
                f" e impresso ({impresso_path})")

    try:
        with open(original_path, 'r', encoding='latin-1') as f_original:
            linhas_original = f_original.readlines()

        with open(impresso_path, 'r', encoding='utf-8') as f_impresso:
            linhas_impresso = f_impresso.readlines()

        # Garantir que ambas as listas tenham o mesmo tamanho
        # (preenchendo com vazio se necessário)
        max_len = max(len(linhas_original), len(linhas_impresso))
        linhas_original.extend([''] * (max_len - len(linhas_original)))
        linhas_impresso.extend([''] * (max_len - len(linhas_impresso)))

        # Comparar linha por linha
        alteracoes: List[Tuple[int, str, str]] = []
        for i, (linha_orig, linha_imp) in enumerate(
                zip(linhas_original, linhas_impresso), start=1):
            if linha_orig.strip() != linha_imp.strip():
                alteracoes.append((i, linha_orig.strip(), linha_imp.strip()))

        # Logar as alterações encontradas
        if alteracoes:
            logger.info(f"Encontradas {len(alteracoes)} "
                        "alterações entre os arquivos")
            for num_linha, orig, imp in alteracoes:
                logger.info(f"Linha {num_linha}: Original: '{orig}'")
                logger.info(f"Linha {num_linha}: Impresso: '{imp}'")

        else:
            logger.info("Nenhuma alteração encontrada entre os arquivos")

    except Exception as e:
        logger.error(f"Erro ao comparar arquivos: {str(e)}")
        raise


if __name__ == '__main__':
    logger = setup_logger(os.path.join(BASE_PATH, 'output', 'log', f"dadger_main_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    try:
        path_dadger = os.path.abspath(r"dadger.rv2")
        logger.info(f"Main: Starting processing with input file {path_dadger}")
        df_dadger, comentarios = leitura_dadger(path_dadger)

        # Modificar mwmed_p1 onde ip=1 e sub=1 com logging
        condition = (df_dadger['DP']['ip'].astype(int) == 1) & (
            df_dadger['DP']['sub'].astype(int) == 1)
        old_value = df_dadger['DP'].loc[condition, 'mwmed_p1'].iloc[0]
        new_value = 1500.0
        df_dadger['DP'].loc[condition, 'mwmed_p1'] = new_value
        logger.info("Main: Changed mwmed_p1 for DP where ip=1 and sub=1 from"
                    f" {old_value} to {new_value}")

        output_path = 'dadger_lido.rv2'
        escrever_dadger(df_dadger, comentarios, output_path, logger)

        # Comparar os arquivos após a escrita
        comparar_arquivos(path_dadger, output_path, logger)

        logger.info("Main: Processing completed successfully")
    except Exception as e:
        logger.error(f"Main: Fatal error occurred: {str(e)}")
        raise

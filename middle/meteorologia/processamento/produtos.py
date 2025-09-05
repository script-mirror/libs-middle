from datetime import datetime
import geopandas as gpd
import requests
import os
import time
import pandas as pd
import numpy as np
from ..consts.constants import CONSTANTES
from middle.utils import Constants
import shutil
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
from middle.utils import get_auth_header
from middle.message.sender import send_whatsapp_message
import scipy.ndimage as nd
from ..plots.plots import plot_campos, plot_df_to_mapa, plot_graficos_2d, plot_chuva_acumulada
from ..utils.utils import (
    get_dado_cacheado,
    ensemble_mean,
    resample_variavel,
    get_inicializacao_fmt,
    ajustar_hora_utc,
    encontra_semanas_operativas,
    gerar_titulo,
    encontra_casos_frentes_xarray,
    interpola_ds,
    get_df_ons,
    calcula_media_bacia,
    converter_psat_para_cd_subbacia,
    open_hindcast_file,
    ajusta_lon_0_360,
    ajusta_acumulado_ds,
    ajusta_shp_json,
    get_prec_db,
    get_pontos_localidades,
    abrir_modelo_sem_vazios,
    formato_filename,
    painel_png
)

###################################################################################################################

class ConfigProdutosPrevisaoCurtoPrazo:

    def __init__(self, modelo, inicializacao, resolucao, data, output_path=Constants().PATH_DOWNLOAD_ARQUIVOS_METEOROLOGIA, days_time_delta=None, shapefiles=None, name_prefix=None):

        import geopandas as gpd

        self.modelo = modelo
        self.inicializacao = inicializacao
        self.resolucao = resolucao
        self.output_path = output_path
        self.shapefiles = {fp: gpd.read_file(fp) for fp in shapefiles} if shapefiles else {}
        self.name_prefix = name_prefix

        if days_time_delta:
            self.data = pd.to_datetime(data) - pd.Timedelta(days=days_time_delta)
        else:
            self.data = pd.to_datetime(data)

    # --- DOWNLOAD ---
    def download_files_models(self, variables=None, levels=None, steps=[i for i in range(0, 390, 6)], provedor_ecmwf_opendata='ecmwf',
                               model_ecmwf_opendata='ifs', file_size=1000, stream_ecmwf_opendata='oper', wait_members=False, last_member_file=None, 
                               modelo_last_member=None, type_ecmwf_opendata='fc', levtype_ecmwf_opendata='sfc', 
                               levlist_ecmwf_opendata=None, sub_region_as_gribfilter=False, baixa_arquivos=True, tamanho_min_bytes=45*1024*1024) -> None:

        # Formatação da data e inicialização
        data_fmt = self.data.strftime('%Y%m%d')
        inicializacao_fmt = str(self.inicializacao).zfill(2)
        resolucao = self.resolucao
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

        # Diretório para salvar os arquivos
        caminho_para_salvar = f'{output_path}/{modelo_fmt}{resolucao}/{data_fmt}{inicializacao_fmt}'
        os.makedirs(caminho_para_salvar, exist_ok=True)

        print(f'Processando dados:\n')
        print(f'Modelo: {modelo_fmt.upper()}')
        print(f'Resolução: {resolucao}')
        print(f'Rodada: {data_fmt}{inicializacao_fmt}')
        print(f'Prefixo do nome: {self.name_prefix if self.name_prefix else "Nenhum"}')
        print(f'Salvando em: {caminho_para_salvar}')

        print(f'\n************* INICIANDO DONWLOAD {data_fmt}{inicializacao_fmt} para o modelo {modelo_fmt.upper()} *************')

        if wait_members:
            while True:
                # caminho_arquivo = f'{caminho_para_salvar}/{last_member_file}'
                caminho_arquivo = f'{output_path}/{modelo_last_member}/{data_fmt}{inicializacao_fmt}/'
                files = sorted(os.listdir(caminho_arquivo))
                last_file = files[-1]

                if last_member_file in last_file: #os.path.exists(caminho_arquivo):
                    tamanho = os.path.getsize(caminho_arquivo + last_file)
                    if tamanho >= tamanho_min_bytes:
                        baixa_arquivos = False
                        break  # Arquivo existe e tem tamanho adequado
                    else:
                        print(f'O arquivo {last_member_file} existe, mas ainda está com {tamanho} bytes (aguardando {tamanho_min_bytes} bytes)...')
                else:
                    print(f'Aguardando arquivo {last_member_file} de membros do modelo {modelo_fmt} serem baixados...')

                time.sleep(10)

        if modelo_fmt == 'gfs':
            prefix_url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{resolucao}.pl?dir=%2F'
            prefixo_pgrb2 = 'pgrb2' if resolucao == '0p25' or resolucao == '1p00' else 'pgrb2full'
            prefix_modelo = f'gfs.{data_fmt}%2F{inicializacao_fmt}%2Fatmos&file=gfs.t{inicializacao_fmt}z.{prefixo_pgrb2}.{resolucao}.f'

        elif modelo_fmt == 'gefs' or modelo_fmt == 'gefs-estendido':
            prefix_url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_{resolucao}a.pl?dir=%2F'
            prefix_modelo = f'gefs.{data_fmt}%2F{inicializacao_fmt}%2Fatmos%2Fpgrb2ap5&file=geavg.t{inicializacao_fmt}z.pgrb2a.{resolucao}.f'

        # Baixando os arquivos
        if baixa_arquivos:

            if modelo_fmt in ['gfs', 'gefs', 'gefs-estendido']:

                # while True:
                #     todos_sucesso = True  # Flag para sair do while quando todos forem baixados corretamente

                #     for i in steps:
                #         filename = f'{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2' if self.name_prefix else f'{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                #         caminho_arquivo = f'{caminho_para_salvar}/{filename}'

                #         # Se o arquivo já existe e está com tamanho esperado, pula
                #         if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) >= file_size:
                #             print(f'✅ Arquivo {filename} já existe e está OK, pulando download...')
                #             continue

                #         url = f'{prefix_url}{prefix_modelo}{i:03d}{variables}{levels}'
                        
                #         if sub_region_as_gribfilter:
                #             url += sub_region_as_gribfilter

                #         file = requests.get(url, allow_redirects=True)
                #         if file.status_code == 200:
                #             with open(caminho_arquivo, 'wb') as f:
                #                 f.write(file.content)
                #         else:
                #             print(f'❌ Erro ao baixar {filename}: {file.status_code}, tentando novamente...')
                #             print(url)
                #             todos_sucesso = False
                #             time.sleep(5)
                #             break  # Sai do for e volta ao início do while

                #         # Verifica se o arquivo foi baixado corretamente
                #         if os.path.exists(caminho_arquivo):
                #             if os.path.getsize(caminho_arquivo) < file_size:
                #                 print(f'Arquivo {filename} está vazio/corrompido, removendo...')
                #                 os.remove(caminho_arquivo)
                #                 todos_sucesso = False
                #                 time.sleep(5)
                #                 break  # Sai do for e tenta de novo no while
                #             else:
                #                 print(f'✅ Arquivo {filename} baixado com sucesso!')
                #         else:
                #             print(f'❌ Arquivo {filename} não foi salvo corretamente, tentando novamente...')
                #             todos_sucesso = False
                #             time.sleep(5)
                #             break

                #     if todos_sucesso:
                #         break  # Sai do while quando tudo estiver certo

                while True:
                    todos_sucesso = True  # Flag para sair do while quando todos forem baixados corretamente

                    for i in steps:
                        filename = (
                            f'{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                            if self.name_prefix
                            else f'{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                        )
                        caminho_arquivo = f'{caminho_para_salvar}/{filename}'

                        # Se o arquivo já existe e está com tamanho esperado, pula sem printar
                        if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) >= file_size:
                            continue

                        # Só imprime aqui quando realmente for tentar baixar
                        print(f'⬇️ Baixando {filename} ...')

                        url = f'{prefix_url}{prefix_modelo}{i:03d}{variables}{levels}'
                        if sub_region_as_gribfilter:
                            url += sub_region_as_gribfilter

                        file = requests.get(url, allow_redirects=True)
                        if file.status_code == 200:
                            with open(caminho_arquivo, 'wb') as f:
                                f.write(file.content)
                        else:
                            print(f'❌ Erro ao baixar {filename}: {file.status_code}, tentando novamente...')
                            print(url)
                            todos_sucesso = False
                            time.sleep(5)
                            break  # Sai do for e volta ao início do while

                        # Verifica se o arquivo foi baixado corretamente
                        if os.path.exists(caminho_arquivo):
                            if os.path.getsize(caminho_arquivo) < file_size:
                                print(f'⚠️ Arquivo {filename} está vazio/corrompido, removendo...')
                                os.remove(caminho_arquivo)
                                todos_sucesso = False
                                time.sleep(5)
                                break  # Sai do for e tenta de novo no while
                            else:
                                print(f'✅ {filename} baixado com sucesso!')
                        else:
                            print(f'❌ Arquivo {filename} não foi salvo corretamente, tentando novamente...')
                            todos_sucesso = False
                            time.sleep(5)
                            break

                    if todos_sucesso:
                        break  # Sai do while quando tudo estiver certo

            elif 'ecmwf' in modelo_fmt:

                if modelo_fmt in ['ecmwf-ens-estendido', 'ecmwf-ens-estendido-membros']:

                    ftp_dir = Constants().PATH_FTP_ECMWF
                    dia_mes_ini = self.data.strftime('%m%d')
                    datafinal = self.data + pd.Timedelta(days=45)
                    date_range = pd.date_range(self.data, datafinal.strftime('%Y%m%d'), freq='D')
                    
                    for fcst_fmt, dates in enumerate(date_range):

                        dia_mes_prev = dates.strftime('%m%d')
                        fcst_fmt = str(fcst_fmt + 1).zfill(2)
                        print(f'Copiando ECMWF - Estendido {fcst_fmt}')

                        dest_file = f'{caminho_para_salvar}/{self.name_prefix}_ecmwf-est_{fcst_fmt}.grib2' if self.name_prefix else f'{caminho_para_salvar}/ecmwf-est_{fcst_fmt}.grib2'
                        src_file = f'{ftp_dir}/A1F{dia_mes_ini}0000{dia_mes_prev}____1'

                        # Loop com número máximo de tentativas
                        max_attempts = 100
                        attempt = 0

                        while not os.path.isfile(dest_file) and attempt < max_attempts:
                            try:
                                shutil.copyfile(src_file, dest_file)
                                break
                            except FileNotFoundError:
                                attempt += 1
                                print(f'Arquivo {src_file} não encontrado. Tentativa {attempt}/{max_attempts}')
                                time.sleep(10)
                            except Exception as e:
                                print(f'Erro ao copiar: {e}')
                                break  # sai do loop se for outro erro

                        if not os.path.isfile(dest_file):
                            print(f'Falha ao copiar {src_file} depois de {max_attempts} tentativas.')


                # elif modelo_fmt in ['ecmwf-mensal']:

                #     ftp_dir = Constants().PATH_FTP_ECMWF
                #     mes_fmt = self.data.strftime(f'%m')
                #     inicializacao_fmt = self.data.strftime(f'%m01')
                #     ultimo_arquivo = f'A1L{inicializacao_fmt}0000{mes_fmt}______1'

                #     while os.path.isfile(f'{ftp_dir}/{ultimo_arquivo}') == False:
                #         print(f'❌ Arquivo {ultimo_arquivo} não encontrado, tentando novamente...')
                #         time.sleep(5)

                #     if os.path.isfile(f'{ftp_dir}/{ultimo_arquivo}'):
                #         # Lista os arquivos que casam com o padrão
                #         padrao = os.path.join(ftp_dir, f"A1L{inicializacao_fmt}*")
                #         arquivos = glob.glob(padrao)

                #         # Copia todos
                #         for arquivo in arquivos:
                #             destino = f'{caminho_para_salvar}/{self.name_prefix}_{os.path.basename(arquivo)}' if self.name_prefix else f'{caminho_para_salvar}/{os.path.basename(arquivo)}'
                #             shutil.copy(arquivo, destino)
                #             print(f"Copiado: {arquivo} -> {destino}")

                else:

                    from ecmwf.opendata import Client
                    client = Client(provedor_ecmwf_opendata, model=model_ecmwf_opendata, resol=resolucao) 

                    while True:
                        todos_sucesso = True  # Flag para checar se todos os steps deram certo

                        for step in steps:

                            caminho_arquivo = f'{caminho_para_salvar}/{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{str(step).zfill(3)}.grib2'

                            if self.name_prefix:
                                caminho_arquivo = f'{caminho_para_salvar}/{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{str(step).zfill(3)}.grib2'

                            if os.path.exists(caminho_arquivo):
                                print(f'✅ Arquivo {caminho_arquivo} já existe, pulando download...')
                                continue

                            if levlist_ecmwf_opendata:
                                retrive = {
                                    'date': data_fmt,
                                    'time': self.inicializacao,
                                    'step': step,
                                    'stream': stream_ecmwf_opendata,
                                    'type': type_ecmwf_opendata,
                                    'levtype': levtype_ecmwf_opendata,
                                    'levelist': levlist_ecmwf_opendata,
                                    'param': variables,
                                    'target': caminho_arquivo,
                                }

                            else:
                                retrive = {
                                    'date': data_fmt,
                                    'time': self.inicializacao,
                                    'step': step,
                                    'stream': stream_ecmwf_opendata,
                                    'type': type_ecmwf_opendata,
                                    'levtype': levtype_ecmwf_opendata,
                                    'param': variables,
                                    'target': caminho_arquivo,
                                }

                            try:
                                client.retrieve(**retrive)

                            except Exception as e:
                                print(f'❌ Erro ao baixar ECMWF: {e}, tentando novamente...')
                                todos_sucesso = False
                                time.sleep(5)
                                break  # Sai do for e tenta novamente o while

                            print(f'✅ Arquivo {caminho_arquivo} baixado com sucesso!')

                        if todos_sucesso:
                            break  # Sai do while se tudo deu certo

            elif modelo_fmt == 'gefs-membros':
                prefix_url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_{resolucao}a.pl?dir=%2F'
                
                while True:
                    todos_sucesso = True  # Flag para sair do while quando todos forem baixados corretamente

                    for membros in range(0, 31):

                        if membros == 0:
                            modelo_name = f'gec{str(membros).zfill(2)}'
                        else:
                            modelo_name = f'gep{str(membros).zfill(2)}'

                        prefix_modelo = f'gefs.{data_fmt}%2F{inicializacao_fmt}%2Fatmos%2Fpgrb2ap5&file={modelo_name}.t{inicializacao_fmt}z.pgrb2a.{resolucao}.f'

                        for i in steps:
                            filename = f'{modelo_name}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2' if self.name_prefix is None else f'{self.name_prefix}_{modelo_name}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                            caminho_arquivo = f'{caminho_para_salvar}/{filename}'

                            # Se o arquivo já existe e está com tamanho esperado, pula
                            if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) >= file_size:
                                print(f'Arquivo {filename} já existe e está OK, pulando download...')
                                continue

                            url = f'{prefix_url}{prefix_modelo}{i:03d}{variables}{levels}'
                            file = requests.get(url, allow_redirects=True)
                            if file.status_code == 200:
                                with open(caminho_arquivo, 'wb') as f:
                                    f.write(file.content)
                            else:
                                print(f'Erro ao baixar {filename}: {file.status_code}, tentando novamente...')
                                todos_sucesso = False
                                time.sleep(5)
                                break  # Sai do for e volta ao início do while

                            # Verifica se o arquivo foi baixado corretamente
                            if os.path.exists(caminho_arquivo):
                                if os.path.getsize(caminho_arquivo) < file_size:
                                    print(f'Arquivo {filename} está vazio/corrompido, removendo...')
                                    os.remove(caminho_arquivo)
                                    todos_sucesso = False
                                    time.sleep(5)
                                    break  # Sai do for e tenta de novo no while
                                else:
                                    print(f'Arquivo {filename} baixado com sucesso!')
                            else:
                                print(f'Arquivo {filename} não foi salvo corretamente, tentando novamente...')
                                todos_sucesso = False
                                time.sleep(5)
                                break

                    if todos_sucesso:
                        break  # Sai do while quando tudo estiver certo

    # --- ABERTURA DOS DADOS ---
    def open_model_file(self, variavel: str, sel_area=False, ensemble_mean=False, cf_pf_members=False, arquivos_membros_diferentes=False, ajusta_acumulado=False, m_to_mm=False, ajusta_longitude=True, sel_12z=False, expand_isobaric_dims=False, membros_prefix=False):

        print(f'\n************* ABRINDO DADOS {variavel} DO MODELO {self.modelo.upper()} *************\n')
        import xarray as xr
        import pdb

        # Importando os tipos de variáveis do arquivo de constantes
        surface = CONSTANTES['tipos_variaveis']['surface']
        height_above_ground = CONSTANTES['tipos_variaveis']['height_above_ground']
        isobaric_inhPa = CONSTANTES['tipos_variaveis']['isobaric_inhPa']
        mean_sea = CONSTANTES['tipos_variaveis']['mean_sea']
        nominalTop = CONSTANTES['tipos_variaveis']['nominalTop']
        mensal_sazonal = CONSTANTES['tipos_variaveis']['mensal_sazonal']

        # Formatação da data e inicialização
        data_fmt = self.data.strftime('%Y%m%d')
        inicializacao_fmt = str(self.inicializacao).zfill(2)
        resolucao = self.resolucao
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower() if not membros_prefix else self.modelo.lower().replace('-membros', '')

        # Caminho para salvar
        caminho_para_salvar = f'{output_path}/{modelo_fmt}{resolucao}/{data_fmt}{inicializacao_fmt}'
        files = sorted(os.listdir(caminho_para_salvar))
        if self.name_prefix:
            files = [f'{caminho_para_salvar}/{f}' for f in files if f.endswith('.grib2') if self.name_prefix in f]  # Filtra pelo prefixo se existir

        else:
            files = [f'{caminho_para_salvar}/{f}' for f in files if f.endswith('.grib2')]

        if len(files) == 0:
            raise FileNotFoundError(f'Nenhum arquivo encontrado no diretório: {caminho_para_salvar}')
        
        # Definindo o backend_kwargs com base na variavel. Se ensemble model, terá pf e cf nos backend_kwargs
        if cf_pf_members:
            
            if variavel in surface:
                backend_kwargs_pf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'surface', 'dataType': 'pf'}, "indexpath": ""}
                backend_kwargs_cf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'surface', 'dataType': 'cf'}, "indexpath": ""}

            elif variavel in height_above_ground:
                backend_kwargs_pf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'heightAboveGround', 'dataType': 'pf'}, "indexpath": ""}
                backend_kwargs_cf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'heightAboveGround', 'dataType': 'cf'}, "indexpath": ""}
                            
            elif variavel in isobaric_inhPa:  # variaveis isobaricas
                backend_kwargs_pf = {"filter_by_keys": {'cfVarName': variavel, 'typeOfLevel': 'isobaricInhPa', 'dataType': 'pf'}, "indexpath": ""}
                backend_kwargs_cf = {"filter_by_keys": {'cfVarName': variavel, 'typeOfLevel': 'isobaricInhPa', 'dataType': 'cf'}, "indexpath": ""}

            elif variavel in mean_sea:
                backend_kwargs_pf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'meanSea', 'dataType': 'pf'}, "indexpath": ""}
                backend_kwargs_cf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'meanSea', 'dataType': 'cf'}, "indexpath": ""}

            elif variavel in nominalTop:
                backend_kwargs_pf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'nominalTop', 'dataType': 'pf'}, "indexpath": ""}
                backend_kwargs_cf = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'nominalTop', 'dataType': 'cf'}, "indexpath": ""}
                files = files[1:]
                
            else:
                raise ValueError(f'Variável {variavel} não reconhecida ou não implementada para ensemble model.')

            # Abrindo o arquivo com xarray
            pf = abrir_modelo_sem_vazios(files, backend_kwargs=backend_kwargs_pf)
            cf = abrir_modelo_sem_vazios(files, backend_kwargs=backend_kwargs_cf)
            ds = xr.concat([cf, pf], dim='number')            

        else:

            if variavel in surface:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'surface'}, "indexpath": ""}
            
            elif variavel in height_above_ground:

                if variavel in ['u100', 'v100']:
                    name = 'cfVarName'
                else:
                    name = 'shortName'

                backend_kwargs = {"filter_by_keys": {name: variavel, 'typeOfLevel': 'heightAboveGround'}, "indexpath": ""}

            elif variavel in isobaric_inhPa:  # variaveis isobaricas
                backend_kwargs = {"filter_by_keys": {'cfVarName': variavel, 'typeOfLevel': 'isobaricInhPa'}, "indexpath": ""}

            elif variavel in mean_sea:  # pressao ao nivel do mar
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'meanSea'}, "indexpath": ""}

            elif variavel in nominalTop:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'nominalTop'}, "indexpath": ""}
                # files = files[1:] # Remove o primeiro arquivo

            elif variavel in mensal_sazonal:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'dataType': 'em'}, "indexpath": ""}

            else:
                raise ValueError(f'Variável {variavel} não reconhecida ou não implementada.')
            
            if arquivos_membros_diferentes:

                ds_total = []
                        
                for membros in range(0, 31, 1):
                    membros_fmt = str(membros).zfill(2)

                    if membros == 0:
                        membro_name = 'gec'
                    else:
                        membro_name = 'gep'

                    path_to_files = [x for x in files if f'{membro_name}{membros_fmt}' in x]
                    prec_membro = abrir_modelo_sem_vazios(path_to_files, backend_kwargs=backend_kwargs)
                    # prec_membro = xr.open_mfdataset(path_to_files, engine='cfgrib', backend_kwargs=backend_kwargs, combine='nested', concat_dim='valid_time', decode_timedelta=True)
                    prec_membro['number'] = membros
                    ds_total.append(prec_membro)

                ds = xr.concat(ds_total, dim='number')

            else:

                ds = abrir_modelo_sem_vazios(files, backend_kwargs=backend_kwargs)
        
        # Renomeando lat para latitude e lon para longitude
        if 'lat' in ds.dims:
            ds = ds.rename({'lat': 'latitude'})

        if 'lon' in ds.dims:
            ds = ds.rename({'lon': 'longitude'})

        # Se step estiver nas dimensions, renomeia para valid_time
        if 'step' in ds.dims:
            ds = ds.swap_dims({'step': 'valid_time'})

        # Pega apenas a hora das 12z
        if sel_12z:
            ds = ds.isel(valid_time=ds.valid_time.dt.hour == 12)

        # Ajustando a longitude para 0 a 360
        if 'longitude' in ds.dims and ajusta_longitude:
           ds = ajusta_lon_0_360(ds)

        # Sortando as coordenadas
        ds = ds.sortby(['valid_time', 'latitude', 'longitude'])

        # Seleciona area especifica (America do Sul)
        if sel_area:
            ds = ds.sel(latitude=slice(-60, 20), longitude=slice(240, 360))    

        # Se for ensemble, faz a média ao longo da dimensão 'number'
        if ensemble_mean:
            if 'number' in ds.dims:
                ds = ds.mean(dim='number')

        # Ajusta acumulado de precipitação (nao necessariamente precisa ser feito, mas é uma opção geralmente apenas para o ECMWF)
        if ajusta_acumulado:
            ds = ajusta_acumulado_ds(ds, m_to_mm=False)

        # Ajusta a unidade de medida
        if m_to_mm and variavel == 'tp':
            # Converte de metros para milímetros
            ds['tp'] = ds['tp'] * 1000

        # torna isobaricHpa em dimensaon
        if expand_isobaric_dims:
            if "isobaricInhPa" not in ds.dims:
                ds = ds.expand_dims({"isobaricInhPa": [ds.isobaricInhPa.item()]})

        print(f'✅ Arquivo aberto com sucesso: {variavel} do modelo {self.modelo.upper()}\n')
        print(f'Dataset após ajustes:')
        print(ds)

        return ds

    # --- REMOVE ARQUIVOS
    def remove_files(self):
        """
        Remove os arquivos temporários baixados.
        """
        # Formatação da data e inicialização
        data_fmt = self.data.strftime('%Y%m%d')
        inicializacao_fmt = str(self.inicializacao).zfill(2)
        resolucao = self.resolucao
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

        # Diretório para salvar os arquivos
        caminho_para_salvar = f'{output_path}/{modelo_fmt}{resolucao}/{data_fmt}{inicializacao_fmt}'

        shutil.rmtree(caminho_para_salvar, ignore_errors=True)
        print(f'✅ Arquivos removidos com sucesso: {caminho_para_salvar}')

###################################################################################################################

class ConfigProdutosObservado:

    def __init__(self, modelo: str, data: datetime, output_path=Constants().PATH_DOWNLOAD_ARQUIVOS_MERGE):
        
        self.modelo = modelo
        self.data = pd.to_datetime(data)
        self.output_path = output_path

    # -- DOWNLOAD
    def download_files(self):
        """
        Faz o download dos arquivos para o modelo e data especificados.
        """

        # Formatação do modelo e data
        modelo_fmt = self.modelo.lower()

        # Formatação do caminho
        output_path = self.output_path

        # Formatando a data
        ano_fmt = self.data.strftime('%Y')
        mes_fmt = self.data.strftime('%m')
        dia_fmt = self.data.strftime('%d')

        # Caminho para salvar os arquivos
        caminho_para_salvar = f'{output_path}/' #{modelo_fmt}/'
        os.makedirs(caminho_para_salvar, exist_ok=True)

        if modelo_fmt == 'merge':
            urls = [f'http://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/DAILY/{ano_fmt}/{mes_fmt}/MERGE_CPTEC_{ano_fmt}{mes_fmt}{dia_fmt}.grib2']

        elif modelo_fmt == 'cpc':
            urls = [f'https://ftp.cpc.ncep.noaa.gov/precip/CPC_UNI_PRCP/GAUGE_GLB/RT/{ano_fmt}/PRCP_CU_GAUGE_V1.0GLB_0.50deg.lnx.{ano_fmt}{mes_fmt}{dia_fmt}.RT']

        elif modelo_fmt == 'samet':
            urls = [
                f'https://ftp.cptec.inpe.br/modelos/tempo/SAMeT/DAILY/TMAX/{ano_fmt}/{mes_fmt}/SAMeT_CPTEC_TMAX_{ano_fmt}{mes_fmt}{dia_fmt}.nc',
                f'https://ftp.cptec.inpe.br/modelos/tempo/SAMeT/DAILY/TMIN/{ano_fmt}/{mes_fmt}/SAMeT_CPTEC_TMIN_{ano_fmt}{mes_fmt}{dia_fmt}.nc',
                f'https://ftp.cptec.inpe.br/modelos/tempo/SAMeT/DAILY/TMED/{ano_fmt}/{mes_fmt}/SAMeT_CPTEC_TMED_{ano_fmt}{mes_fmt}{dia_fmt}.nc',
                ]

        for url in urls:

            filename = url.split('/')[-1]
            caminho_arquivo = f'{caminho_para_salvar}/{filename}'

            while True:

                try:

                    # Baixando o dado
                    file = requests.get(url, allow_redirects=True, verify=False)
                    
                    if file.status_code == 200:
                        with open(caminho_arquivo, 'wb') as f:
                            f.write(file.content)
                        print(f'✅ Arquivo {filename} baixado com sucesso!')
                        break  # Sai do while quando der certo
                    else:
                        print(f'❌ Erro ao baixar {filename}: {file.status_code}, tentando novamente...')
                        print(url)
                        time.sleep(5)
                
                except requests.RequestException as e:
                    print(f'⚠️ Erro de conexão ao baixar {filename}: {e}, tentando novamente...')
                    time.sleep(5)

        # Transformando CPC em NETCDF
        if modelo_fmt == 'cpc':

            nx, ny = 720, 360
            data = np.fromfile(caminho_arquivo, dtype="<f4")
            rain = data[:nx*ny].reshape(ny, nx)
            ds = xr.Dataset({"tp": (("lat","lon"), rain/10)}, coords={"lon": np.arange(0.25, 360, 0.5), "lat": np.arange(-89.75, 90, 0.5)})
            ds.to_netcdf(f'{caminho_para_salvar}/{filename.replace(".RT", ".nc")}')

    # --- ABERTURA DOS DADOS ---
    def open_model_file(self, todo_dir=False, unico=False, ajusta_nome=True, ajusta_longitude=True, apenas_mes_atual=False, variavel=None, ultimos_n_dias=False, n_dias=15):

        import xarray as xr
        import pdb

        print(f'\n************* ABRINDO DADOS {variavel} DO MODELO {self.modelo.upper()} *************\n')
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

        # Caminho para salvar os arquivos
        caminho_para_salvar = f'{output_path}/'
        files = os.listdir(caminho_para_salvar)

        if variavel is not None:
            files = [f for f in files if variavel in f or variavel.lower() in f.lower()]

        if files[-1].endswith('.grib2'):
            backend_kwargs={"indexpath": ""}
        
        else:
            backend_kwargs=None

        if apenas_mes_atual:
            data = self.data
            data_fmt = data.strftime('%Y%m')

            # Filtrando arquivos pela data
            files = [f'{caminho_para_salvar}/{f}' for f in files if data_fmt in f]
            ds = xr.open_mfdataset(files, combine='nested', concat_dim='time', backend_kwargs=backend_kwargs)

            # Troca time por valid_time
            ds = ds.swap_dims({'time': 'valid_time'})

        if todo_dir:
            files = [f'{caminho_para_salvar}/{f}' for f in files]
            ds = xr.open_mfdataset(files, combine='nested', concat_dim='time', backend_kwargs=backend_kwargs)

            # Troca time por valid_time
            ds = ds.swap_dims({'time': 'valid_time'})

        if unico:
            data_fmt = self.data.strftime('%Y%m%d')
            file = [f for f in files if data_fmt in f][0]
            ds = xr.open_dataset(f'{caminho_para_salvar}/{file}', backend_kwargs=backend_kwargs)

            # Cria dim valid_time e atribui o valor do time
            ds = ds.assign_coords(valid_time=ds.time)

            try:
                ds = ds.expand_dims('valid_time')

            except:
                ds = ds.swap_dims({'time': 'valid_time'})

        if ultimos_n_dias:
            files = files[-n_dias:]
            files = [f'{caminho_para_salvar}/{f}' for f in files]
            ds = xr.open_mfdataset(files, combine='nested', concat_dim='time', backend_kwargs=backend_kwargs)

        if ajusta_nome:
            if 'rdp' in ds.data_vars:
                ds = ds.rename({'rdp': 'tp'})

            if 'lon' in ds.dims:
                ds = ds.rename({'lon': 'longitude', 'lat': 'latitude'})

        # Ajustando a longitude para 0 a 360
        if 'longitude' in ds.dims and ajusta_longitude:
           ds = ajusta_lon_0_360(ds)

        return ds

###################################################################################################################

class GeraProdutosPrevisao:

    def __init__(self, produto_config_sf, tp_params=None, pl_params=None, shapefiles=None, produto_config_pl=None, modo_atual=True):

        self.produto_config_sf = produto_config_sf
        self.modelo_fmt = self.produto_config_sf.modelo
        self.output_path = self.produto_config_sf.output_path
        self.resolucao = self.produto_config_sf.resolucao
        self.data_fmt = f'{pd.to_datetime(self.produto_config_sf.data).strftime("%Y%m%d")}{str(self.produto_config_sf.inicializacao).zfill(2)}'
        self.tp_params = tp_params or {}
        self.pl_params = pl_params or {}
        self.shapefiles = shapefiles
        self.produto_config_pl = produto_config_pl
        self.qtdade_max_semanas = CONSTANTES['semanas_operativas'].get(self.modelo_fmt, 3)
        self.path_savefiguras = f'{Constants().PATH_SAVE_FIGS_METEOROLOGIA}/{self.modelo_fmt}/{self.data_fmt}'

        # Inicializando algumas variaveis
        self.us = None
        self.us_mean = None
        self.vs = None
        self.vs_mean = None
        self.tp = None
        self.tp_mean = None
        self.geop = None
        self.gh_mean = None
        self.t = None
        self.t_mean = None
        self.cond_ini = None
        self.pnmm_mean = None
        self.q_mean = None
        self.q = None
        self.t2m_mean = None
        self.t2m = None
        self.olr_mean = None
        self.olr = None
        self.us100 = None
        self.us100_mean = None
        self.vs100 = None
        self.vs100_mean = None

        self.freqs_map = {
            'sop': {
                'prefix_filename': 'semana',
                'prefix_title': 'Semana' 
            },

            '24h': {
                'prefix_filename': 'diario',
                'prefix_title': ''
            }
        }

        self.modo_atual = modo_atual
        self.figs_24h = ['prec_pnmm', '24h', 'jato_div200', 'vento_temp850', 'geop_vort500', 'geop500', 'ivt', 'vento_div850', 'total', '24h_biomassa']
        self.figs_semana = ['semanas_operativas']
        self.figs_6h = ['chuva_geop500_vento850']
        self.vento850_pnmm6h = ['pnmm_vento850']
        self.graficos_vento = ['graficos_vento']
        self.prob_acm = ['probabilidade_climatologia', 'probabilidade_limiar']
        self.semana_membros = ['desvpad']
        self.precip_grafs = ['graficos_precipitacao']
        self.psi_chi = ['psi']
        self.temp_geada = ['geada-inmet', 'geada-cana']
        self.graficos_temp = ['graficos_temperatura']
        self.graficos_vento = ['graficos_vento']
        self.olr = ['olr']
        self.mag_vento100 = ['mag_vento100']
        
    ###################################################################################################################

    # --- REMOVE ARQUIVOS BRUTOS
    def remove_files(self):
        """
        Remove os arquivos temporários baixados.
        """

        # Diretório para salvar os arquivos
        caminho_para_salvar = f'{self.output_path}/{self.modelo_fmt}{self.resolucao}/{self.data_fmt}'

        shutil.rmtree(caminho_para_salvar, ignore_errors=True)
        print(f'✅ Arquivos removidos com sucesso: {caminho_para_salvar}')

    ###################################################################################################################

    def _ajustar_tempo_e_titulo(self, ds_plot, tipo, semana, cond_ini=None, unico_tempo=False):

        tempo_ini = ajustar_hora_utc(pd.to_datetime(ds_plot.data_inicial.item()))
        tempo_fim = pd.to_datetime(ds_plot.data_final.item())
        cond_ini = cond_ini or get_inicializacao_fmt(ds_plot)

        return gerar_titulo(
            modelo=self.modelo_fmt,
            tipo=tipo,
            cond_ini=cond_ini,
            data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
            data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
            semana=semana,
            unico_tempo=unico_tempo
        )

    ###################################################################################################################

    def _carregar_tp_mean(self, ensemble=True):

        """Carrega e processa o campo tp apenas uma vez."""
        tp = get_dado_cacheado('tp', self.produto_config_sf, **self.tp_params)
        tp_mean = ensemble_mean(tp) if ensemble else tp.copy()
        cond_ini = get_inicializacao_fmt(tp_mean)
        return tp, tp_mean, cond_ini

    def _carregar_uv_mean(self):

        ''' Carrega e processa os campos u e v apenas uma vez. '''
        us = get_dado_cacheado('u', self.produto_config_pl, **self.pl_params)
        vs = get_dado_cacheado('v', self.produto_config_pl, **self.pl_params)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        cond_ini = get_inicializacao_fmt(us_mean)

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        return us, vs, us_mean, vs_mean, cond_ini

    def _carregar_uv100_mean(self):

        ''' Carrega e processa os campos u e v apenas uma vez. '''
        varname_u = '100u' if 'ecmwf' in self.modelo_fmt else 'u100'
        varname_v = '100v' if 'ecmwf' in self.modelo_fmt else 'v100'
        us = get_dado_cacheado(varname_u, self.produto_config_sf, **self.pl_params)
        vs = get_dado_cacheado(varname_v, self.produto_config_sf, **self.pl_params)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        cond_ini = get_inicializacao_fmt(us_mean)

        if '100u' in us.data_vars:
            us = us.rename({'100u': 'u100'})
            us_mean = us_mean.rename({'100u': 'u100'})
        if '100v' in vs.data_vars:
            vs = vs.rename({'100v': 'v100'})
            vs_mean = vs_mean.rename({'100v': 'v100'})

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        return us, vs, us_mean, vs_mean, cond_ini

    def _carregar_t_mean(self):
        t = get_dado_cacheado('t', self.produto_config_pl, **self.pl_params)
        t_mean = ensemble_mean(t)
        cond_ini = get_inicializacao_fmt(t_mean)

        if t_mean.longitude.min() >= 0:
            t_mean = t_mean.assign_coords(longitude=(((t_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        return t, t_mean, cond_ini

    def _carregar_t2m_mean(self):
        t = get_dado_cacheado('2t', self.produto_config_sf, **self.pl_params)
        t_mean = ensemble_mean(t)
        cond_ini = get_inicializacao_fmt(t_mean)

        return t, t_mean, cond_ini

    def _carregar_gh_mean(self):
        gh = get_dado_cacheado('gh', self.produto_config_pl, **self.pl_params)
        gh_mean = ensemble_mean(gh)
        cond_ini = get_inicializacao_fmt(gh_mean)
        return gh, gh_mean, cond_ini

    def _carregar_pnmm_mean(self):

        varname = 'msl' if 'ecmwf' in self.modelo_fmt else 'prmsl'
        pnmm = get_dado_cacheado(varname, self.produto_config_sf, **self.pl_params)
        pnmm_mean = ensemble_mean(pnmm)
        cond_ini = get_inicializacao_fmt(pnmm_mean)
        return pnmm, pnmm_mean, cond_ini

    def _carregar_q_mean(self):

        q = get_dado_cacheado('q', self.produto_config_pl, **self.pl_params)
        q_mean = ensemble_mean(q)
        cond_ini = get_inicializacao_fmt(q_mean)

        if q_mean.longitude.min() >= 0:
            q_mean = q_mean.assign_coords(longitude=(((q_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        return q, q_mean, cond_ini

    def _carregar_olr_mean(self):

        varname = 'ttr' if 'ecmwf' in self.modelo_fmt else 'sulwrf'
        olr = get_dado_cacheado(varname, self.produto_config_sf, **self.pl_params)
        olr_mean = ensemble_mean(olr)
        cond_ini = get_inicializacao_fmt(olr_mean)

        # if t_mean.longitude.min() >= 0:
        #     t_mean = t_mean.assign_coords(longitude=(((t_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        return olr, olr_mean, cond_ini

    ###################################################################################################################

    def _processar_precipitacao(self, modo, ensemble=True, plot_graf=True, 
                                salva_db=True, modelo_obs='merge', limiares_prob=[5, 10, 20, 30, 50, 70, 100], freq_prob='sop', 
                                timedelta=1, dif_total=True, dif_01_15d=False, dif_15_final=False, anomalia_sop=False,
                                var_anomalia='tp', level_anomalia=200, anomalia_mensal=False, regiao_estacao_chuvosa='sudeste', resample_freq='24h',
                                **kwargs):
        
        """
        modo: 24h, total, semanas_operativas, bacias_smap, probabilidade_limiar, diferenca, prec_pnmm'
        """


        qtdade_max_semanas = self.qtdade_max_semanas
        
        if self.modo_atual:

            if modo in self.figs_24h:
                path_save = '24-em-24-gifs'

            elif modo in self.figs_semana:
                path_save = 'semana-energ'

            elif modo in self.graficos_vento:
                path_save = 'uv100_grafs'

            elif modo in self.figs_6h:
                path_save = 'figs-6h'

            elif modo in self.prob_acm:
                path_save = 'prob-acm'

            elif modo in self.semana_membros:
                path_save = 'semana-energ-membros'

            elif modo in self.precip_grafs:
                path_save = 'precip_grafs'

            else:
                path_save = modo

        else:
            path_save = modo

        path_to_save = f'{self.path_savefiguras}/{path_save}' if modo not in ['estacao_chuvosa'] else self.path_savefiguras
        os.makedirs(path_to_save, exist_ok=True)

        try:

            print(f"Gerando mapa de precipitação ({modo})...")

            # Carrega e processa dado
            if self.tp_mean is None or self.cond_ini is None or self.tp is None:
                self.tp, self.tp_mean, self.cond_ini = self._carregar_tp_mean(ensemble=ensemble)

            if modo == '24h':
                tp_proc = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')
                
                for n_24h in tp_proc.tempo:
                    print(f'Processando {n_24h.item()}...')
                    tp_plot = tp_proc.sel(tempo=n_24h)

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.tp.time.values), tempo_ini, ds_tempo_final=self.tp.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                    titulo = self._ajustar_tempo_e_titulo(tp_plot, 'PREC24HRS', semana, self.cond_ini)

                    plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='chuva_ons',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, 'rain', n_24h.item()),
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == '24h_biomassa':
                tp_proc = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')
                
                for n_24h in tp_proc.tempo:
                    print(f'Processando {n_24h.item()}...')
                    tp_plot = tp_proc.sel(tempo=n_24h)

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.tp.time.values), tempo_ini, ds_tempo_final=self.tp.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                    titulo = self._ajustar_tempo_e_titulo(tp_plot, 'PREC24HRS', semana, self.cond_ini)

                    plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='chuva_ons',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, 'rain_bio_logo', n_24h.item()),
                        shapefiles=self.shapefiles,
                        plot_bacias=False,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'prec_pnmm':

                varname = 'msl' if 'ecmwf' in self.modelo_fmt else 'prmsl'

                # Tp
                tp_24h = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', resample_freq)

                # Pnmm
                if self.pnmm_mean is None:
                    _, self.pnmm_mean, _ = self._carregar_pnmm_mean()

                pnmm_24h = resample_variavel(self.pnmm_mean, self.modelo_fmt, varname, resample_freq, modo_agrupador='mean')

                for n_24h, p_24h in zip(tp_24h.tempo, pnmm_24h.tempo):

                    print(f'Processando {n_24h.item()}...')
                    tp_plot = tp_24h.sel(tempo=n_24h)
                    pnmm_plot = pnmm_24h.sel(tempo=p_24h)
                    pnmm_plot = nd.gaussian_filter(pnmm_plot[varname]*1e-2, sigma=2)

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.tp.time.values), tempo_ini, ds_tempo_final=self.tp.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            tp_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}PREC24, PNMM', semana, self.cond_ini,
                        )

                    else:
                        intervalo = tp_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = tp_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='chuva_ons',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'rain_pnmm_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_contour=pnmm_plot,
                        variavel_contour='pnmm',
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )                

            elif modo == 'total':
                
                tempo_ini = pd.to_datetime(self.tp_mean.valid_time.values[0])
                tempo_fim = pd.to_datetime(self.tp_mean.valid_time.values[-1])
                tp_plot = self.tp_mean.sum(dim='valid_time')

                titulo = gerar_titulo(
                    modelo=self.modelo_fmt,
                    tipo='Acumulado total',
                    cond_ini=self.cond_ini,
                    data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    sem_intervalo_semana=True
                )

                plot_campos(
                    ds=tp_plot['tp'],
                    variavel_plotagem='acumulado_total',
                    title=titulo,
                    filename=formato_filename(self.modelo_fmt, 'acumuladototal'),
                    shapefiles=self.shapefiles,
                    path_to_save=path_to_save,
                    **kwargs
                )

                # Acumulado com MERGE
                path_merge = '/WX2TB/Documentos/saidas-modelos-novo/mergegpm/data/mergegpm'
                ano_mes_atual = pd.to_datetime(self.tp.time.values).strftime('%Y%m')
                files = os.listdir(path_merge)

                files_to_use = [x for x in files if f'{ano_mes_atual}' in x if '.idx' not in x if 'tmp' not in x]
                files_to_use = sorted(files_to_use)

                if len(files_to_use) > 0:
                    files_to_use = [path_merge + '/' + x for x in files_to_use]
                    ds_obs = xr.open_mfdataset(files_to_use, engine='cfgrib', combine='nested', concat_dim='time', backend_kwargs={"indexpath": ""})
                    ds_obs = ds_obs.rename({'rdp': 'tp'})
                    ds_obs = ds_obs['tp']
                    tempo_ini = ds_obs.time[0].values
                    ultimo_tempo = ds_obs.time[-1]
                    ds_obs = ds_obs.sum(dim='time')
                    ds_obs = interpola_ds(ds_obs, self.tp).to_dataset()

                    # Dando o resample nos dados de chuva prevista
                    ds_resample = self.tp_mean.sel(valid_time=self.tp_mean.valid_time > ultimo_tempo).resample(valid_time='M').sum()

                    for index, time in enumerate(ds_resample.valid_time):
                        ds_resample_sel = ds_resample.sel(valid_time=time)
                        mes = pd.to_datetime(time.values).strftime('%b/%Y')

                        if time.dt.month == ds_obs.time.dt.month:
                            tipo=f'MERGE + Prev'
                            ds_acumulado = ds_obs['tp'] + ds_resample_sel['tp']
                            ds_acumulado = ds_acumulado.to_dataset()

                            if anomalia_mensal: 
                                if 'ecmwf' in self.modelo_fmt.lower():
                                    ds_clim = open_hindcast_file(var_anomalia, level_anomalia, inicio_mes=True)
                                    ds_clim = interpola_ds(ds_clim, ds_acumulado)

                                elif 'gefs' in self.modelo_fmt.lower():
                                    ds_clim = open_hindcast_file(var_anomalia, path_clim=Constants().PATH_HINDCAST_GEFS_EST, mesdia=pd.to_datetime(self.tp.time.data).strftime('%m%d'))
                                    ds_clim = interpola_ds(ds_clim, ds_acumulado)      

                                # Anos iniciais e finais da climatologia
                                ano_ini = pd.to_datetime(ds_clim.alvo_previsao[0].values).strftime('%Y')
                                ano_fim = pd.to_datetime(ds_clim.alvo_previsao[-1].values).strftime('%Y')

                        else:
                            tempo_ini = self.tp_mean.sel(valid_time=self.tp_mean.valid_time.dt.month == time.dt.month).valid_time[0].values
                            tipo=f'Acumulado total'
                            ds_acumulado = ds_resample_sel

                            if anomalia_mensal:    
                                if 'ecmwf' in self.modelo_fmt.lower():
                                    ds_clim = open_hindcast_file(var_anomalia, level_anomalia)
                                    ds_clim = interpola_ds(ds_clim, ds_acumulado)

                                elif 'gefs' in self.modelo_fmt.lower():
                                    ds_clim = open_hindcast_file(var_anomalia, path_clim=Constants().PATH_HINDCAST_GEFS_EST, mesdia=pd.to_datetime(self.tp.time.data).strftime('%m%d'))
                                    ds_clim = interpola_ds(ds_clim, ds_acumulado)      

                                # Anos iniciais e finais da climatologia
                                ano_ini = pd.to_datetime(ds_clim.alvo_previsao[0].values).strftime('%Y')
                                ano_fim = pd.to_datetime(ds_clim.alvo_previsao[-1].values).strftime('%Y')

                        tempo_fim = self.tp_mean.sel(valid_time=self.tp_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values
                        data_ini=pd.to_datetime(tempo_ini).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ ')
                        data_fim=pd.to_datetime(tempo_fim).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ ')

                        if anomalia_mensal:
                            inicio = pd.to_datetime(tempo_ini).strftime('%Y-%m-%d %H')
                            fim = pd.to_datetime(tempo_fim).strftime('%Y-%m-%d %H')
                            
                            t_clim_ini = inicio.replace(inicio[:4], ano_ini)
                            t_clim_fim = fim.replace(fim[:4], ano_fim)

                            # Sel nos tempos encontrados
                            ds_clim_sel = ds_clim.sel(alvo_previsao=slice(t_clim_ini, t_clim_fim)).sum(dim='alvo_previsao').sortby(['latitude'])

                            # Anomalia
                            ds_anomalia = ds_acumulado['tp'] - ds_clim_sel['tp']
                            ds_anomalia = ds_anomalia.to_dataset()

                            titulo = gerar_titulo(
                                modelo=self.modelo_fmt,
                                tipo=tipo,
                                cond_ini=self.cond_ini,
                                data_ini=data_ini,
                                data_fim=data_fim,
                                sem_intervalo_semana=True,
                                prefixo_negrito=True,
                                prefixo=f'para\\ {mes.title()}'
                            )

                            plot_campos(
                                ds=ds_anomalia['tp'],
                                variavel_plotagem='tp_anomalia',
                                title=titulo,
                                filename=formato_filename(self.modelo_fmt, 'anomaliaacumuladomensal', index),
                                shapefiles=self.shapefiles,
                                path_to_save=path_to_save,
                                **kwargs
                            )     

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt,
                            tipo=tipo,
                            cond_ini=self.cond_ini,
                            data_ini=data_ini,
                            data_fim=data_fim,
                            sem_intervalo_semana=True,
                            prefixo_negrito=True,
                            prefixo=f'para\\ {mes.title()}'
                        )

                        plot_campos(
                            ds=ds_acumulado['tp'],
                            variavel_plotagem='acumulado_total',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'acumuladototal', index),
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )              

            elif modo == 'semanas_operativas':

                tp_sop = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', 'sop', anomalia_sop=anomalia_sop, qtdade_max_semanas=qtdade_max_semanas, var_anomalia=var_anomalia, level_anomalia=level_anomalia)

                for n_semana in tp_sop.tempo:

                    print(f'Processando semana {n_semana.item()}...')
                    tp_plot = tp_sop.sel(tempo=n_semana)
                    intervalo = tp_plot.intervalo.item().replace(' ', '\ ')
                    days_of_week = tp_plot.days_of_weeks.item()

                    if ensemble:

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_semana.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                        )

                        plot_campos(
                            ds=tp_plot['tp'],
                            variavel_plotagem='chuva_ons' if not anomalia_sop else 'tp_anomalia', # 1semana_energ-r2025090300.png # 1_semana_energ_gfs.png 1_anom_semana_energ-r2025090300.png
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, f'semana_energ-r{self.data_fmt}', n_semana.item()) if not anomalia_sop else formato_filename(self.modelo_fmt, f'anom_semana_energ-r{self.data_fmt}', n_semana.item()),
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

                    else:

                        for membro in self.tp['number']:

                            titulo = gerar_titulo(
                                modelo=f'{self.modelo_fmt}-M{membro.item()}', tipo=f'Semana{n_semana.item()}',
                                cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                                semana_operativa=True
                            )

                            plot_campos(
                                ds=tp_plot['tp'].sel(number=membro),
                                variavel_plotagem='chuva_ons',
                                title=titulo,
                                filename=f'tp_sop_{self.modelo_fmt}_semana{n_semana.item()}_{membro.item()}',
                                shapefiles=self.shapefiles,
                                path_to_save=path_to_save,
                                **kwargs
                            )

                # Criando painel para enviar via wpp
                if ensemble:
                    path_painel = painel_png(path_figs=path_to_save, output_file=f'painel_semanas_operativas_{self.modelo_fmt}_{self.data_fmt}.png')
                    send_whatsapp_message(destinatario=Constants().WHATSAPP_METEOROLOGIA, mensagem=f'{self.modelo_fmt.upper()} {self.cond_ini}', arquivo=path_painel)
                    print(f'Removendo painel ... {path_painel}')
                    os.remove(path_painel)

            elif modo == 'bacias_smap':

                from datetime import datetime
                API_URL = Constants().API_URL_APIV2

                # Vou usar para pegar as informações das subbacias
                df_ons = get_df_ons()

                # Abrindo o json arrumado
                shp = ajusta_shp_json()

                # Adicionando alguns pontos que não estão no arquivo
                novas_subbacias = CONSTANTES['novas_subbacias']
                shp = pd.concat([shp, pd.DataFrame(novas_subbacias)], ignore_index=True)

                # Resample para 24h
                tp_24h = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')

                if ensemble:

                    chuva_media = []
                    
                    # Sem membros individuais
                    for lat, lon, bacia, codigo in zip(shp['lat'], shp['lon'], shp['nome'], shp['cod']):
                        chuva_media.append(calcula_media_bacia(tp_24h, lat, lon, bacia, codigo, shp))

                    # Concatenando os xarrays com a média nas bacias e transformando em um dataframe
                    ds_to_df = xr.concat(chuva_media, dim='id').to_dataframe().reset_index()
                    ds_to_df['modelo'] = self.modelo_fmt
                    ds_to_df = ds_to_df.rename(columns={'id': 'cod_psat', 'time': 'dt_rodada', 'data_final': 'dt_prevista', 'tp': 'vl_chuva'})
                    ds_to_df = ds_to_df[['cod_psat', 'dt_rodada', 'dt_prevista', 'modelo', 'vl_chuva']]
                    ds_to_df = ds_to_df.applymap(lambda x: 0 if isinstance(x, float) and x < 0 else x).round(2)
                    dt_rodada = list(set(ds_to_df['dt_rodada']))[0]
                    dt_rodada = dt_rodada.isoformat()
                    ds_to_df['dt_rodada'] = dt_rodada
                    ds_to_df['dt_prevista'] = pd.to_datetime(ds_to_df['dt_prevista'].values).strftime('%Y-%m-%d')
                    ds_to_df = converter_psat_para_cd_subbacia(ds_to_df)
                    print(ds_to_df)

                    if salva_db:
                        print('Salvando dados no db')
                        response = requests.post(f'{API_URL}/rodadas/chuva/previsao/modelos', verify=False, json=ds_to_df.to_dict('records'), headers=get_auth_header())
                        print(f'Código POST: {response.status_code}')

                    if plot_graf:
                        
                        # Bacias segmentadas
                        bacias_segmentadas = requests.get(f"{API_URL}/ons/bacias-segmentadas", verify=False, headers=get_auth_header())
                        bacias_segmentadas = pd.DataFrame(bacias_segmentadas.json()).rename(columns={"nome":"cod_psat", 'id': 'cd_subbacia'})

                        # Climatologia bacias
                        climatologia_bacias = requests.get(f"{API_URL}/meteorologia/climatologia-bacias", verify=False, headers=get_auth_header())
                        climatologia_bacias = pd.DataFrame(climatologia_bacias.json())
                        climatologia_bacias = climatologia_bacias.rename(columns={"bacia": "str_bacia"})
                        climatologia_bacias['time'] = pd.to_datetime(climatologia_bacias['time'].values)

                        # Submercados
                        submercados = bacias_segmentadas.merge(df_ons.rename(columns={"cd_bacia_mlt":"cd_bacia"}), on='cd_bacia', how='left')

                        ############################################################## OBSERVADO ##############################################################

                        dt_inicial = datetime.now().strftime('%Y-%m-01')
                        dt_final = datetime.now().strftime(f'%Y-%m-%d')
                        dt_inicial_db = pd.to_datetime(dt_inicial) - pd.Timedelta(days=1)
                        dt_final_db = pd.to_datetime(dt_final) - pd.Timedelta(days=1)

                        acumulado = None
                        date_ranges = pd.date_range(start=dt_inicial_db, end=dt_final_db, freq='D')

                        if modelo_obs == 'merge':
                            url = f'{API_URL}/rodadas/chuva/observada?dt_observada='
                        
                        else:
                            url = f'{API_URL}/rodadas/chuva/observada/psat?dt_observada='

                        # Acumulando entre os dias
                        for dt_observada in date_ranges:

                            observado = requests.get(f'{url}{dt_observada}', verify=False, headers=get_auth_header())

                            try:
                                if len(observado.json()) > 0:
                                    df_obs = pd.DataFrame(observado.json())
                                    df_obs['dt_observado'] = pd.to_datetime(df_obs['dt_observado']) + pd.Timedelta(days=1)
                                    chuva = df_obs['vl_chuva'].values
                                    acumulado = chuva + acumulado if acumulado is not None else chuva

                            except Exception as e:
                                print(f"Erro ao processar os dados para a data {dt_observada}: {e}")
                                dt_final = dt_observada
                                break
        
                        # Colocando os dados em um dataframe
                        df_obs['chuva_acumulada'] = acumulado
                        df_obs = df_obs.merge(df_ons, on='cd_subbacia', how='left')
                        df_merged = df_obs.rename(columns={'cd_bacia_mlt': 'cd_bacia'})
                        df_merged = pd.merge(df_merged, bacias_segmentadas)
                        df_merged.drop(columns='nome_bacia', inplace=True)
                        df_merged = df_merged.rename(columns={'cd_bacia': 'nome_bacia'})

                        # Média por bacia
                        df_observado = df_merged.groupby(['str_bacia'])['chuva_acumulada'].mean().reset_index()

                        # Colocando os dados em um dataframe
                        df_prev = ds_to_df.merge(df_ons, on='cd_subbacia', how='left')
                        df_prev['dt_prevista'] = pd.to_datetime(df_prev['dt_prevista'])
                        meses = df_prev['dt_prevista'].dt.month.unique()

                        for index, mes in enumerate(meses):

                            mes_fmt_svg = pd.to_datetime(mes, format='%m').strftime('%B')
                            
                            df_prev_plot = df_prev[df_prev['dt_prevista'].dt.month == mes]
                            dt_inicial_prev = pd.to_datetime(df_prev_plot['dt_prevista'].min()).strftime('%d/%m')
                            df_final_prev = pd.to_datetime(df_prev_plot['dt_prevista'].max()).strftime('%d/%m')
                            df_merged = df_prev_plot.rename(columns={'cd_bacia_mlt': 'cd_bacia'})
                            df_merged = pd.merge(df_merged, bacias_segmentadas)
                            df_merged.drop(columns='nome_bacia', inplace=True)
                            df_merged = df_merged.rename(columns={'cd_bacia': 'nome_bacia'})
                            
                            # Média por bacia
                            df_merged = df_merged.groupby(['str_bacia', 'dt_prevista'])['vl_chuva'].mean().reset_index()
                            df_merged = df_merged.groupby(['str_bacia'])['vl_chuva'].sum().reset_index()

                            if mes == pd.to_datetime(dt_final).month:
                                # Merge com os dados observados
                                df_merged = df_merged.merge(df_observado, on='str_bacia', how='left')

                            climatologia = climatologia_bacias[climatologia_bacias['time'].dt.month == mes]
                            df_climatologia_mean = climatologia.groupby('str_bacia', as_index=False).mean()
                            df_merged = df_merged.merge(df_climatologia_mean[['str_bacia', 'climatologia']], on='str_bacia', how='left')

                            # Filtra apenas bacias de interesse
                            bacias_para_plotar = [
                                'JACUÍ', 'URUGUAI', 'IGUAÇU', 'PARANAPANEMA (S)', 'BAIXO PARANÁ', 'ALTO PARANÁ',
                                'PARANAPANEMA', 'TIETÊ', 'GRANDE', 'PARANAÍBA',
                                'TOCANTINS (SE)', 'AMAZONAS (SE)', 'SÃO FRANCISCO (SE)', 'SÃO FRANCISCO (NE)',
                                'XINGU', 'AMAZONAS (N)', 'TOCANTINS (N)',
                            ]

                            df_merged['submercado'] = df_merged['str_bacia'].apply(lambda x: submercados[submercados['str_bacia'] == x]['nome_submercado'].values[0] if x in submercados['str_bacia'].values else None)
                            df_merged = df_merged[df_merged['str_bacia'].isin(bacias_para_plotar)]
                            df_merged["str_bacia"] = pd.Categorical(df_merged["str_bacia"], categories=bacias_para_plotar, ordered=True)
                            df_merged = df_merged.sort_values("str_bacia").reset_index(drop=True)

                            plot_chuva_acumulada(
                                df_merged=df_merged,
                                mes=mes,
                                dt_inicial=pd.to_datetime(dt_inicial, format='%Y-%m-01'),
                                dt_final=pd.to_datetime(dt_final),
                                dt_inicial_prev=dt_inicial_prev,
                                df_final_prev=df_final_prev,
                                modelo_obs=modelo_obs,
                                modelo_prev=self.modelo_fmt,
                                dt_rodada=pd.to_datetime(dt_rodada).strftime('%Y-%m-%d-%Hz'),
                                path_to_save=path_to_save,
                                index=index,
                                mes_fmt_svg=mes_fmt_svg,
                                com_climatologia=True
                            )

                            path_painel = painel_png(path_figs=path_to_save, output_file=f'painel_bacias_smap_{self.modelo_fmt}_{self.data_fmt}.png', str_contain='chuva_acumulada')
                            send_whatsapp_message(destinatario=Constants().WHATSAPP_METEOROLOGIA, mensagem=f'Chuva total bacia {self.modelo_fmt.upper()} {self.cond_ini}', arquivo=path_painel)
                            print(f'Removendo painel ... {path_painel}')
                            os.remove(path_painel)

                else:

                    df_total = []
                    
                    # Itera por membro
                    for membro in tp_24h.number:
                        
                        chuva_media = []
                        tp_24h_membro = tp_24h.sel(number=membro)
                        
                        for lat, lon, bacia, codigo in zip(shp['lat'], shp['lon'], shp['nome'], shp['cod']):
                            chuva_media.append(calcula_media_bacia(tp_24h_membro, lat, lon, bacia, codigo, shp))
                        
                        # Concatenando os xarrays com a média nas bacias e transformando em um dataframe
                        ds_to_df = xr.concat(chuva_media, dim='id').to_dataframe().reset_index()
                        ds_to_df['modelo'] = self.modelo_fmt
                        ds_to_df = ds_to_df.rename(columns={'id': 'cod_psat', 'time': 'dt_rodada', 'data_final': 'dt_prevista', 'tp': 'vl_chuva'})
                        ds_to_df = ds_to_df[['cod_psat', 'dt_rodada', 'dt_prevista', 'modelo', 'vl_chuva']]
                        ds_to_df = ds_to_df.applymap(lambda x: 0 if isinstance(x, float) and x < 0 else x).round(2)
                        dt_rodada = list(set(ds_to_df['dt_rodada']))[0]
                        dt_rodada = dt_rodada.isoformat()
                        ds_to_df['dt_rodada'] = dt_rodada
                        ds_to_df['dt_prevista'] = pd.to_datetime(ds_to_df['dt_prevista'].values).strftime('%Y-%m-%d')
                        ds_to_df = converter_psat_para_cd_subbacia(ds_to_df)
                        ds_to_df['membro'] = f'{membro.item()}'

                        print('Membro:', membro.item())
                        print(ds_to_df)

                        tp_24h_membro.close()
                        df_total.append(ds_to_df)

                    if salva_db:
                        # Concatenando em um unico dataframe
                        df_total = pd.concat(df_total)
                        print('Salvando dados no db')
                        response = requests.post(f'{API_URL}rodadas/chuva/previsao/membros', verify=False, json=df_total.to_dict('records'), headers=get_auth_header())
                        print(f'Código POST: {response.status_code}')

            elif modo == 'probabilidade_climatologia':

                tp_sop = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', freq=freq_prob, qtdade_max_semanas=qtdade_max_semanas, prob_semana=True)
                
                for n_semana in tp_sop.tempo:

                    print(f'Processando semana {n_semana.item()}...')
                    tp_plot = tp_sop.sel(tempo=n_semana)
                    intervalo = tp_plot.intervalo.item().replace(' ', '\ ')
                    days_of_week = tp_plot.days_of_weeks.item()
                    ds_prob_acima = xr.where(tp_plot['tp'] > 0, 1, 0)
                    ds_prob_abaixo = xr.where(tp_plot['tp'] < 0, 1, 0)
                    ds_probs = [ds_prob_acima, ds_prob_abaixo]

                    for index, ds_prob in enumerate(ds_probs):

                        soma = ds_prob.sum(dim='number')
                        prob = soma/len(ds_prob.number)
                        prob = prob*100

                        if index == 0:
                            tipo = 'acima'

                        elif index == 1:
                            tipo = 'abaixo'

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Prob {tipo} clim. Semana{n_semana.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                        )

                        plot_campos(
                            ds=prob,
                            variavel_plotagem='probabilidade',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, f'{tipo}-probclimatologia', f'{n_semana.item()}{index}'),
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

            elif modo == 'probabilidade_limiar':

                tp_sop = resample_variavel(self.tp, self.modelo_fmt, 'tp', freq=freq_prob, qtdade_max_semanas=qtdade_max_semanas)

                for limiar in limiares_prob:

                    for n in tp_sop['tempo']:

                        print(f'Processando {n.item()}...')
                        tp_plot = tp_sop.sel(tempo=n)
                        intervalo = tp_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = tp_plot.days_of_weeks.item()

                        tp_plot = tp_plot - limiar
                        tp_plot = xr.where(tp_plot['tp'] > 0, 1, 0)
                        tp_plot = tp_plot.sum(dim='number')
                        tp_plot = tp_plot/len(self.tp.number)
                        tp_plot = tp_plot*100

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'{self.freqs_map[freq_prob]["prefix_title"]}{n.item()} Prob. > {limiar} mm',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                        )

                        plot_campos(
                            ds=tp_plot,
                            variavel_plotagem='probabilidade',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, f'probabilidade{limiar}_{freq_prob}', n.item()),
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

            elif modo == 'diferenca':

                # Arquivo atual
                ds_mean = self.tp_mean.copy()
                variavel = 'tp'

                # Abrindo o arquivo anterior (precisa ter sido previamente salvo)
                data_anterior = pd.to_datetime(ds_mean.time.values) - pd.Timedelta(days=timedelta)
                data_anterior_fmt = data_anterior.strftime('%Y%m%d%H')
                ds_anterior = xr.open_dataset(f'{CONSTANTES["path_save_netcdf"]}/{self.modelo_fmt}_{variavel}_{data_anterior_fmt}.nc')
                ds_anterior = ajusta_lon_0_360(ds_anterior)
                ds_anterior = ensemble_mean(ds_anterior)
            
                if 'step' in ds_anterior.dims:
                    ds_anterior = ds_anterior.swap_dims({'step': 'valid_time'})

                ds_anterior = ajusta_acumulado_ds(ds_anterior, m_to_mm=True) if 'ecmwf' in self.modelo_fmt else ds_anterior

                # Listas para plot
                difs = []
                dates = []
                tipos_dif = []

                if dif_total:

                    # Diferença total
                    ti = ds_mean['valid_time'].values[0]
                    tf = ds_anterior['valid_time'].values[-1]

                    # Acumulando
                    ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                    ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                    # Ds diferença
                    ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                    difs.append(ds_diferenca)
                    dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                    tipos_dif.append('Total')

                if dif_01_15d:
                    # Diferença dos dias 1 ao 15
                    ti = ds_mean['valid_time'].values[0]
                    tf = pd.to_datetime(ti) + pd.Timedelta(days=15)

                    # Acumulando
                    ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                    ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                    # Ds diferença
                    ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                    difs.append(ds_diferenca)
                    dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                    tipos_dif.append('15D')

                if dif_15_final:
                    # Diferença dos dias 15 ao restante
                    ti = pd.to_datetime(ds_mean['valid_time'].values[0]) + pd.Timedelta(days=15)
                    tf = ds_anterior['valid_time'].values[-1]

                    # Acumulando
                    ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                    ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                    # Ds diferença
                    ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                    difs.append(ds_diferenca)
                    dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                    tipos_dif.append('15D-Final')

                for index, (dif, date, tipo_dif) in enumerate(zip(difs, dates, tipos_dif)):

                    cond_ini = f'[{self.cond_ini}] - [{data_anterior.strftime("%d/%m/%Y %H UTC")}]'

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, sem_intervalo_semana=True, tipo=f'Diferença {tipo_dif}', cond_ini=cond_ini,
                        data_ini=date[0].strftime('%d/%m/%Y').replace(' ', '\\ '),
                        data_fim=date[1].strftime('%d/%m/%Y').replace(' ', '\\ '),
                    )

                    plot_campos(
                        ds=dif,
                        variavel_plotagem='diferenca',
                        title=titulo,
                        shapefiles=self.shapefiles,
                        filename=formato_filename(self.modelo_fmt, 'dif', index),
                        path_to_save=path_to_save,
                        **kwargs
                    )

                path_painel = painel_png(path_figs=path_to_save, output_file=f'painel_semanas_operativas_{self.modelo_fmt}_{self.data_fmt}.png')
                send_whatsapp_message(destinatario=Constants().WHATSAPP_METEOROLOGIA, mensagem=f'Diferença {self.modelo_fmt.upper()} {self.cond_ini}', arquivo=path_painel)
                print(f'Removendo painel ... {path_painel}')
                os.remove(path_painel)

            elif modo == 'desvpad':

                tp_sop = resample_variavel(self.tp, self.modelo_fmt, 'tp', freq=freq_prob, qtdade_max_semanas=qtdade_max_semanas)

                for n in tp_sop['tempo']:

                    print(f'Processando {n.item()}...')
                    tp_plot = tp_sop.sel(tempo=n).std(dim='number')
                    intervalo = tp_plot.intervalo.item().replace(' ', '\ ')
                    days_of_week = tp_plot.days_of_weeks.item()

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=f'{self.freqs_map[freq_prob]["prefix_title"]}{n.item()} Desvio Padrão',
                        cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                        semana_operativa=True
                    )

                    plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='desvpad',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'desviopadrao_{freq_prob}', n.item()),
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'estacao_chuvosa':

                if regiao_estacao_chuvosa == 'sudeste':
                    lati = -15
                    latf = -25
                    loni = 307.5
                    lonf = 320
                
                elif regiao_estacao_chuvosa == 'norte':
                    lati = -2
                    latf = -6
                    loni = 360-56
                    lonf = 360-46.4

                # Selecionando a região da estação chuvosa
                tp_estacao = self.tp_mean.sel(latitude=slice(latf, lati), longitude=slice(loni, lonf))

                # Aplicando a mascara sobre o oceano
                ds_mask = xr.open_dataset('/projetos/arquivos/meteorologia/land.nc').isel(time=0).isel(nbnds=0)
                ds_mask = ds_mask.rename({'lat': 'latitude', 'lon': 'longitude'})
                ds_mask = ds_mask.interp(latitude=tp_estacao.latitude, longitude=tp_estacao.longitude)
                tp_estacao = tp_estacao['tp']*ds_mask['land']
                tp_estacao.name = 'tp'

                # Calculando a média
                ds_mean = tp_estacao.mean(('latitude', 'longitude')).to_dataframe().reset_index()   
                ds_mean['hr_rodada'] = pd.to_datetime(self.tp_mean['time'].values).hour
                ds_mean['dt_rodada'] = pd.to_datetime(self.tp_mean['time'].values).strftime('%Y-%m-%d')
                ds_mean['valid_time'] = ds_mean["valid_time"].astype(str)
                ds_mean['str_modelo'] = self.modelo_fmt
                ds_mean = ds_mean[['valid_time', 'dt_rodada', 'hr_rodada', 'tp', 'str_modelo']]
                ds_mean = ds_mean.rename({'valid_time': 'dt_prevista', 'tp': 'vl_chuva'}, axis=1)
                ds_mean['regiao'] = regiao_estacao_chuvosa

                # Tirando o primeiro tempo do ec estendido (acumulado de 12 horas)
                if 'ecmwf' in self.modelo_fmt:
                    ds_mean = ds_mean[1:]

                print('Salvando dados no db')
                API_URL = Constants().API_URL_APIV2
                response = requests.post(f'{API_URL}/meteorologia/estacao-chuvosa-prev', verify=False, json=ds_mean.to_dict('records'), headers=get_auth_header())
                print(f'Código POST: {response.status_code}')

            elif modo == 'graficos_precipitacao':

                target_lon, target_lat, _ = get_pontos_localidades()
                tp_proc = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')
                tp_no_ponto = tp_proc.sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe().reset_index()
                tp_no_ponto['data_fmt'] = tp_no_ponto['data_final'].dt.strftime('%d/%m')

                for id in tp_no_ponto['id'].unique():

                    print(f'Gráficos chuva ID: {id}')

                    tp_plot = tp_no_ponto[tp_no_ponto['id'] == id]
                    titulo = f"{CONSTANTES['city_dict'][id]}\n{self.modelo_fmt.upper()} - PRECH24HRS - Condição Inicial: {self.cond_ini}"
                    filename = f'{path_to_save}/{id}'
                    plot_graficos_2d(df=tp_plot, tipo='prec24h', titulo=titulo, filename=filename)

        except Exception as e:
            print(f'Erro ao gerar precipitação ({modo}): {e}')

    def _processar_varsdinamicas(self, modo, anomalia_frentes=False, resample_freq='24h', anomalia_sop=False, var_anomalia='gh', level_anomalia=500, anomalia_mensal=False,**kwargs):

        qtdade_max_semanas = self.qtdade_max_semanas
        if self.modo_atual:

            if modo in self.figs_24h:
                path_save = '24-em-24-gifs'

            elif modo in self.figs_semana:
                path_save = 'semana-energ'

            elif modo in self.graficos_vento:
                path_save = 'uv100_grafs'

            elif modo in self.figs_6h:
                path_save = 'figs-6h'

            elif modo in self.prob_acm:
                path_save = 'prob-acm'

            elif modo in self.semana_membros:
                path_save = 'semana-energ-membros'

            elif modo in self.precip_grafs:
                path_save = 'precip_grafs'

            elif modo in self.psi_chi:
                path_to_save = 'psi_chi'

            elif modo in self.graficos_temp:
                path_save = 'temp_grafs'

            elif modo in self.olr:
                path_save = 'semana-energ-olr'

            elif modo in self.mag_vento100:
                path_save = 'semana-energ-uv100m'

            elif modo in self.temp_geada:
                path_save = 'temp_geada'

            elif modo in self.vento850_pnmm6h:
                path_save = 'vento850_pnmm6h'

            else:
                path_save = modo

        else:
            path_save = modo

        path_to_save = f'{self.path_savefiguras}/{path_save}'
        os.makedirs(path_to_save, exist_ok=True)

        try:

            print(f"Gerando mapa de variaveis dinâmicas ({modo})...")

            if modo == 'jato_div200':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                level_divergencia = 200

                us_24h = resample_variavel(self.us_mean.sel(isobaricInhPa=level_divergencia), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u')
                vs_24h = resample_variavel(self.vs_mean.sel(isobaricInhPa=level_divergencia), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v')

                for n_24h in us_24h.tempo:

                    print(f'Processando {n_24h.item()}...')
                    us_plot = us_24h.sel(tempo=n_24h)
                    vs_plot = vs_24h.sel(tempo=n_24h)
                    vento_jato = (us_plot['u']**2 + vs_plot['v']**2)**0.5
                    divergencia = mpcalc.divergence(us_plot['u'], vs_plot['v']) * 1e5

                    ds_streamplot = xr.Dataset({
                        'u': us_plot['u'],
                        'v': vs_plot['v'],
                        'divergencia': divergencia,
                        'jato': vento_jato
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Jato {level_divergencia}hPa', semana, self.cond_ini,
                        )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Vento e Jato {level_divergencia}hPa - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_streamplot['jato'],
                        variavel_plotagem='wind200',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'vento200_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        variavel_streamplot='wind200',
                        ds_streamplot=ds_streamplot,
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )
            
            elif modo == 'vento_temp850':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                if self.t_mean is None:
                    _, self.t_mean, _ = self._carregar_t_mean()
                
                level_temp = 850
                
                us_24h_850 = resample_variavel(self.us_mean.sel(isobaricInhPa=level_temp), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                vs_24h_850 = resample_variavel(self.vs_mean.sel(isobaricInhPa=level_temp), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                t850_24h = resample_variavel(self.t_mean.sel(isobaricInhPa=level_temp), self.modelo_fmt, 't', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in us_24h_850.tempo:

                    print(f'Processando {n_24h.item()}...')
                    us_plot = us_24h_850.sel(tempo=n_24h)
                    vs_plot = vs_24h_850.sel(tempo=n_24h)
                    t850_plot = t850_24h.sel(tempo=n_24h)

                    ds_quiver = xr.Dataset({
                        'u': us_plot['u'],
                        'v': vs_plot['v'],
                        't850': t850_plot['t']
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Temp. em {level_temp}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Vento e Temp. em {level_temp}hPa - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_quiver['t850'] - 273.15,  # Kelvin para Celsius
                        variavel_plotagem='temp850',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'vento_temp850_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_quiver=ds_quiver,
                        variavel_quiver='wind850',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'geop_vort500':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                if self.gh_mean is None:
                    self.geop, self.geop_mean, _ = self._carregar_gh_mean()

                level_geop = 500

                # Resample para 24 horas
                us_24h_500 = resample_variavel(self.us_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                vs_24h_500 = resample_variavel(self.vs_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                geop_500 = resample_variavel(self.geop_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'gh', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in geop_500.tempo:

                    print(f'Processando {n_24h.item()}...')
                    geop_ = geop_500.sel(tempo=n_24h)
                    geop_plot = nd.gaussian_filter(geop_['gh'], sigma=3)
                    u_plot = us_24h_500.sel(tempo=n_24h) * units.meter_per_second
                    v_plot = vs_24h_500.sel(tempo=n_24h) * units.meter_per_second
                    vorticidade = mpcalc.vorticity(u_plot['u'], v_plot['v']) * 1e6
                    vorticidade = nd.gaussian_filter(vorticidade, sigma=3)

                    ds_plot = xr.Dataset({
                        'gh': (('latitude', 'longitude'), geop_plot),
                        'vorticidade': (('latitude', 'longitude'), vorticidade),
                        'u': u_plot['u'],
                        'v': v_plot['v']
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(geop_.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(geop_.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]
                        titulo = self._ajustar_tempo_e_titulo(geop_, f'{self.freqs_map[resample_freq]["prefix_title"]}Vort. e Geop. {level_geop}hPa', semana, self.cond_ini )

                    else:
                        intervalo = geop_.intervalo.item().replace(' ', '\ ')
                        days_of_week = geop_.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Vort. e Geop. {level_geop}hPa - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_plot['vorticidade'],
                        variavel_plotagem='vorticidade',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'vort_geo500_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_contour=ds_plot['gh']/10,
                        variavel_contour='gh_500',
                        plot_bacias=False,
                        color_contour='black',
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'frentes':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                if self.t_mean is None:
                    _, self.t_mean, self.cond_ini = self._carregar_t_mean()

                if self.pnmm_mean is None:
                    _, self.pnmm_mean, self.cond_ini = self._carregar_pnmm_mean()
                
                # Gerando mapas das frente frias previstas
                pnmm_sel = self.pnmm_mean.assign_coords(longitude=(((self.us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude').sel(latitude=slice(-90, 0)).resample(valid_time='D').mean(dim='valid_time')
                vwnd_sel = self.vs_mean.sortby('latitude').sel(isobaricInhPa=925).sel(latitude=slice(-90, 0)).resample(valid_time='D').mean(dim='valid_time')
                air_sel = self.t_mean.sortby('latitude').sel(isobaricInhPa=925).sel(latitude=slice(-90, 0)).resample(valid_time='D').mean(dim='valid_time')           

                for index, mes in enumerate(list(set(pnmm_sel.valid_time.dt.month.values))):

                    mes_fmt = str(mes).zfill(2)

                    ds_mensal_slp = pnmm_sel.sel(valid_time=pnmm_sel.valid_time.dt.month == mes)
                    ds_mensal_vwnd = vwnd_sel.sel(valid_time=vwnd_sel.valid_time.dt.month == mes)
                    ds_mensal_air = air_sel.sel(valid_time=air_sel.valid_time.dt.month == mes)

                    ds_frentes = encontra_casos_frentes_xarray(ds_mensal_slp, ds_mensal_vwnd, ds_mensal_air, varname='msl' if 'ecmwf' in self.modelo_fmt else 'prmsl')

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, sem_intervalo_semana=True, tipo=f'Casos de frentes frias', cond_ini=self.cond_ini,
                        data_ini=pd.to_datetime(ds_mensal_slp.valid_time.min().values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        data_fim=pd.to_datetime(ds_mensal_slp.valid_time.max().values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    )

                    plot_campos(
                        ds=ds_frentes,
                        variavel_plotagem='frentes',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'frentes_{mes_fmt}', index),   
                        ds_contour=ds_frentes,
                        variavel_contour='frentes',
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

                    if anomalia_frentes:
                    
                        # Agora o mapa de anomalia
                        ds_climatologia = xr.open_dataset(f'{CONSTANTES["path_reanalise_ncepI"]}/climatologia_{mes_fmt}.nc')

                        # Renomeando lat para latitude e lon para longitude
                        ds_climatologia = ds_climatologia.rename({'lat':'latitude', 'lon':'longitude', '__xarray_dataarray_variable__':'climatologia'})

                        # Transformando a longitude para 0 e 360 se necessário
                        if (ds_frentes.longitude < 0).any():
                            ds_frentes = ds_frentes.assign_coords(longitude=(ds_frentes.longitude % 360)).sortby('longitude').sortby('latitude')

                        # Interpolando
                        ds_climatologia = interpola_ds(ds_climatologia, ds_frentes)

                        # Calculando a anomalia
                        anomalia = ds_frentes - (ds_climatologia['climatologia']/30)*len(ds_mensal_slp.valid_time)          

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, sem_intervalo_semana=True, tipo=f'Anomalia de frentes frias', cond_ini=self.cond_ini,
                            data_ini=pd.to_datetime(ds_mensal_slp.valid_time.min().values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            data_fim=pd.to_datetime(ds_mensal_slp.valid_time.max().values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        )

                        plot_campos(
                            ds=anomalia,
                            variavel_plotagem='frentes_anomalia',
                            title=titulo,
                            filename=f'anomalia_frentes_{self.modelo_fmt}',
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

            elif modo == 'geop500':

                if self.gh_mean is None:
                    self.geop, self.geop_mean, self.cond_ini = self._carregar_gh_mean()
                
                level_geop = 500

                if not anomalia_sop:
                    geop_500 = resample_variavel(self.geop_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'gh', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia=var_anomalia, level_anomalia=level_anomalia)

                else:
                    geop_500 = resample_variavel(self.geop_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'gh', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia=var_anomalia, level_anomalia=level_anomalia)
                    geop_500_contour = resample_variavel(self.geop_mean.sel(isobaricInhPa=level_geop), self.modelo_fmt, 'gh', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=False, var_anomalia=var_anomalia, level_anomalia=level_anomalia)
                
                for n_24h in geop_500.tempo:
                    print(f'Processando {n_24h.item()}...')
                    geop_plot = geop_500.sel(tempo=n_24h)

                    if anomalia_sop:
                        geop_plot_contour = geop_500_contour.sel(tempo=n_24h)

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(geop_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.geop.time.values), tempo_ini, ds_tempo_final=self.geop.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                        titulo = self._ajustar_tempo_e_titulo(
                            geop_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Geopotencial {level_geop}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = geop_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = geop_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Geopotencial {level_geop}hPa - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=geop_plot['gh']/10,
                        variavel_plotagem='geop_500' if not anomalia_sop else 'geop_500_anomalia',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'altgeop500_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()) if not anomalia_sop else formato_filename(self.modelo_fmt, f'altgeop500_anomalia_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),                        
                        ds_contour=geop_plot['gh']/10 if not anomalia_sop else geop_plot_contour['gh']/10,
                        variavel_contour='gh_500',
                        color_contour='black' if anomalia_sop else 'white',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

                if anomalia_mensal:
                    # Dando o resample nos dados de chuva prevista
                    ds_resample = self.geop_mean.resample(valid_time='M').mean()

                    if 'ecmwf' in self.modelo_fmt.lower():
                        ds_clim = open_hindcast_file(var_anomalia, level_anomalia)
                        ds_clim = interpola_ds(ds_clim, ds_resample)

                    elif 'gefs' in self.modelo_fmt.lower():
                        ds_clim = open_hindcast_file(var_anomalia, path_clim=Constants().PATH_HINDCAST_GEFS_EST, mesdia=pd.to_datetime(self.tp.time.data).strftime('%m%d'))
                        ds_clim = interpola_ds(ds_clim, ds_resample) 

                    # Anos iniciais e finais da climatologia
                    ano_ini = pd.to_datetime(ds_clim.alvo_previsao[0].values).strftime('%Y')
                    ano_fim = pd.to_datetime(ds_clim.alvo_previsao[-1].values).strftime('%Y')

                    for index, time in enumerate(ds_resample.valid_time):

                        # Selecionando o mês correspondente
                        ds_resample_sel = ds_resample.sel(valid_time=time)

                        # Selecionando o mês correspondente
                        mes = pd.to_datetime(time.values).strftime('%b/%Y').title()

                        # Selando o tempo na climatologia
                        tempoini = pd.to_datetime(self.geop_mean.sel(valid_time=self.geop_mean.valid_time.dt.month == time.dt.month).valid_time[0].values).strftime('%Y-%m-%d %H')
                        tempo_fim = pd.to_datetime(self.geop_mean.sel(valid_time=self.geop_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values).strftime('%Y-%m-%d %H')
                        t_clim_ini = tempoini.replace(tempoini[:4], ano_ini)
                        t_clim_fim = tempo_fim.replace(tempo_fim[:4], ano_fim)
                        ds_clim_sel = ds_clim.sel(alvo_previsao=slice(t_clim_ini, t_clim_fim)).mean(dim='alvo_previsao').sortby(['latitude'])
                    
                        # Anomalia
                        ds_anomalia = ds_resample_sel['gh'] - ds_clim_sel['gh']
                        ds_anomalia = ds_anomalia.to_dataset().isel(isobaricInhPa=0)

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt,
                            tipo=f'Média {mes}',
                            cond_ini=self.cond_ini,
                            data_ini=pd.to_datetime(self.geop_mean.sel(valid_time=self.geop_mean.valid_time.dt.month == time.dt.month).valid_time[0].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            data_fim=pd.to_datetime(self.geop_mean.sel(valid_time=self.geop_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            sem_intervalo_semana=True
                        )

                        plot_campos(
                            ds=ds_anomalia['gh'],
                            variavel_plotagem='geop_500_anomalia',
                            title=titulo,
                            filename=f'{index}_gh_anomalia_mensal_{self.modelo_fmt}',
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )  

            elif modo == 'ivt':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                if self.gh_mean is None:
                    self.geop, self.geop_mean, _ = self._carregar_gh_mean()

                if self.q_mean is None:
                    self.q, self.q_mean, _ = self._carregar_q_mean()

                # Resample para 24 horas
                gh_24h = resample_variavel(self.geop_mean.sel(isobaricInhPa=700), self.modelo_fmt, 'gh', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                qs_24h = resample_variavel(self.q_mean.sel(isobaricInhPa=slice(1000, 300)), self.modelo_fmt, 'q', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                us_24h = resample_variavel(self.us_mean.sel(isobaricInhPa=slice(1000, 300)), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                vs_24h = resample_variavel(self.vs_mean.sel(isobaricInhPa=slice(1000, 300)), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)

                # Calculando o fluxo zonal e meridional de umidade espec
                qu = qs_24h['q'] * us_24h['u']
                qv = qs_24h['q'] * vs_24h['v']

                # Integrando na vertical 300 - 1000hPa
                QU = qu.integrate('isobaricInhPa')*(-1/10)
                QV = qv.integrate('isobaricInhPa')*(-1/10)  

                # Interpolando o vento
                n_interp = 2.5
                QU_interp = QU.interp(longitude=np.arange(QU.longitude.min().values, QU.longitude.max().values, n_interp), latitude=np.arange(QU.latitude.min().values, QU.latitude.max().values, n_interp))
                QV_interp = QV.interp(longitude=np.arange(QV.longitude.min().values, QV.longitude.max().values, n_interp), latitude=np.arange(QV.latitude.min().values, QV.latitude.max().values, n_interp))

                # Calculando o IVT
                IVT = np.sqrt(QU**2 + QV**2)

                # Plotando
                for n_24h in gh_24h.tempo:

                    print(f'Processando {n_24h.item()}...')

                    gh_plot = gh_24h.sel(tempo=n_24h)
                    ivt_plot = IVT.sel(tempo=n_24h)
                    qu_plot = QU_interp.sel(tempo=n_24h)
                    qv_plot = QV_interp.sel(tempo=n_24h)

                    ds_quiver = xr.Dataset({
                        'ivt': ivt_plot,
                        'qu': qu_plot,
                        'qv': qv_plot,
                        'gh_700': gh_plot['gh']/10  # Convertendo de m para dam
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(gh_plot.data_inicial.item()))
                        tempo_fim = pd.to_datetime(gh_plot.data_final.item())
                        semana = encontra_semanas_operativas(pd.to_datetime(self.geop.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]
                        titulo = gerar_titulo(
                                modelo=self.modelo_fmt, tipo='Geop 700hPa e TIWV', cond_ini=self.cond_ini,
                                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                semana=semana
                            )

                    else:
                        intervalo = gh_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = gh_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Geop 700hPa e TIWV - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_quiver['ivt']*100,
                        variavel_plotagem='ivt',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'ivt_geop700_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_quiver=ds_quiver,
                        variavel_quiver='ivt',
                        ds_contour=ds_quiver['gh_700'],
                        variavel_contour='gh_700',
                        plot_bacias=False,
                        color_contour='black',
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'vento_div850':

                level_divergencia = 850
                
                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                us_24h_850 = resample_variavel(self.us_mean.sel(isobaricInhPa=level_divergencia), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)
                vs_24h_850 = resample_variavel(self.vs_mean.sel(isobaricInhPa=level_divergencia), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in us_24h_850.tempo:

                    print(f'Processando {n_24h.item()}...')
                    us_plot = us_24h_850.sel(tempo=n_24h)
                    vs_plot = vs_24h_850.sel(tempo=n_24h)
                    divergencia = mpcalc.divergence(us_plot['u'], vs_plot['v']) * 1e5

                    ds_streamplot = xr.Dataset({
                        'u': us_plot['u'],
                        'v': vs_plot['v'],
                        'divergencia': divergencia
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]
                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Div. {level_divergencia}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Vento e Div. {level_divergencia}hPa - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_streamplot['divergencia'],
                        variavel_plotagem='divergencia850',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'vento850_div850_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_streamplot=ds_streamplot,
                        variavel_streamplot='wind850',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'chuva_geop500_vento850':

                level_vento = 850
                level_geop = 500
                
                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()
                    
                if self.gh_mean is None:
                    self.geop, self.geop_mean, self.cond_ini = self._carregar_gh_mean()

                if self.tp_mean is None or self.cond_ini is None or self.tp is None:
                    self.tp, self.tp_mean, self.cond_ini = self._carregar_tp_mean()

                for index, n_24h in enumerate(self.tp_mean.valid_time):

                    print(f'Processando {index}...')

                    us_plot = self.us_mean.sel(valid_time=n_24h)
                    vs_plot = self.vs_mean.sel(valid_time=n_24h)
                    gh_plot = self.geop_mean.sel(valid_time=n_24h).assign_coords(longitude=(((self.us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
                    tp_plot = self.tp_mean.sel(valid_time=n_24h).assign_coords(longitude=(((self.us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

                    ds_quiver = xr.Dataset({
                        'u': us_plot['u'].sel(isobaricInhPa=level_vento).drop_vars('isobaricInhPa'), 
                        'v': vs_plot['v'].sel(isobaricInhPa=level_vento).drop_vars('isobaricInhPa'), 
                        'geop_500': gh_plot['gh'].sel(isobaricInhPa=level_geop).drop_vars('isobaricInhPa') / 10,
                        'tp': tp_plot['tp']
                    })

                    tempo_ini = pd.to_datetime(n_24h.item())
                    semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=f'Prec6h, Geo{level_geop}hPa, Vento{level_vento}hPa', cond_ini=self.cond_ini,
                        data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        semana=semana, unico_tempo=True
                    )

                    plot_campos(ds=ds_quiver['tp'], 
                                variavel_plotagem='wind_prec_geop', 
                                title=titulo, 
                                filename=formato_filename(self.modelo_fmt, 'chuva_geop500_vento850', index),
                                plot_bacias=False, ds_quiver=ds_quiver, 
                                variavel_quiver='wind850', 
                                ds_contour=ds_quiver['geop_500'], 
                                variavel_contour='gh_500', 
                                color_contour='black',
                                shapefiles=self.shapefiles,
                                path_to_save=path_to_save,
                                **kwargs
                                )

            elif modo == 'anomalia_psi':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                us_mean = ajusta_lon_0_360(self.us_mean)
                vs_mean = ajusta_lon_0_360(self.vs_mean)

                us_24h_200 = resample_variavel(us_mean.sel(isobaricInhPa=200), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u')
                vs_24h_200 = resample_variavel(vs_mean.sel(isobaricInhPa=200), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v')

                us_24h_850 = resample_variavel(us_mean.sel(isobaricInhPa=850), self.modelo_fmt, 'u', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u')
                vs_24h_850 = resample_variavel(vs_mean.sel(isobaricInhPa=850), self.modelo_fmt, 'v', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v')

                psi_clim200 = open_hindcast_file('psi200').rename({"time": "valid_time"})
                psi_clim850 = open_hindcast_file('psi850').rename({"time": "valid_time"})
                chi_clim200 = open_hindcast_file('chi200').rename({"time": "valid_time"})
                chi_clim850 = open_hindcast_file('chi850').rename({"time": "valid_time"})

                ano_ini = pd.to_datetime(psi_clim200.valid_time[0].values).strftime('%Y')
                ano_fim = pd.to_datetime(psi_clim200.valid_time[-1].values).strftime('%Y')

                if resample_freq == '24h':

                    for n_24h in us_24h_200.tempo:

                        u200_plot = us_24h_200.sel(tempo=n_24h)
                        v200_plot = vs_24h_200.sel(tempo=n_24h)
                        u850_plot = us_24h_850.sel(tempo=n_24h)
                        v850_plot = vs_24h_850.sel(tempo=n_24h)
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(u200_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=2), modelo=self.modelo_fmt)[0]

                        data_inicial = pd.to_datetime(n_24h.data_inicial.values).strftime('%Y-%m-%d')
                        data_final = pd.to_datetime(n_24h.data_final.values).strftime('%Y-%m-%d')
                        intervalo1 = data_inicial.replace(data_inicial[:4], ano_ini)
                        intervalo2 = data_final.replace(data_final[:4], ano_ini)

                        u200_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        v200_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        u850_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        v850_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}

                        u200_plot.drop_vars(["data_inicial", "data_final"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u200_semana.nc')
                        v200_plot.drop_vars(["data_inicial", "data_final"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v200_semana.nc')

                        u850_plot.drop_vars(["data_inicial", "data_final"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u850_semana.nc')
                        v850_plot.drop_vars(["data_inicial", "data_final"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v850_semana.nc')

                        # Grads parar calcular PSI e CHI e gerar um .nc
                        os.system(f'/usr/local/grads-2.0.2.oga.2/Contents/opengrads -lbcx {Constants().PATH_ARQUIVOS_TEMP}/gera_psi_chi.gs')

                        # Anomalia psi e chi
                        ds_psi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi200.nc')
                        ds_psi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi850.nc')

                        ds_chi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi200.nc')
                        ds_chi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi850.nc')

                        psi_clim200_plot = psi_clim200.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        psi_clim850_plot = psi_clim850.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        chi_clim200_plot = chi_clim200.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        chi_clim850_plot = chi_clim850.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')

                        anomalia_psi200 = ds_psi200_prev['psi200'] - psi_clim200_plot['psi']
                        anomalia_psi850 = ds_psi850_prev['psi850'] - psi_clim850_plot['psi']

                        anomalia_chi200 = ds_chi200_prev['chi200'] - chi_clim200_plot['chi']
                        anomalia_chi850 = ds_chi850_prev['chi850'] - chi_clim850_plot['chi']

                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lat').mean(dim='lon')
                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lon')

                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lat').mean(dim='lon')
                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lon')

                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lat').mean(dim='lon')
                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lon')

                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lat').mean(dim='lon')
                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lon')

                        anomalia_psi200 = anomalia_psi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_psi850 = anomalia_psi850.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi200 = anomalia_chi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi850 = anomalia_chi850.rename({"lat": "latitude", "lon": "longitude"})

                        # Plot 24h
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(u200_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=2), modelo=self.modelo_fmt)[0]

                        # PSI
                        titulo = self._ajustar_tempo_e_titulo(
                            u200_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}PSI 200/850', semana, self.cond_ini,
                        )

                        plot_campos(
                            ds=anomalia_psi200/1e6,
                            variavel_plotagem='psi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'psi_diario', index),
                            ds_contour=anomalia_psi850/1e6,
                            variavel_contour='psi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

                        # CHI
                        titulo = self._ajustar_tempo_e_titulo(
                            u200_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}CHI 200/850', semana, self.cond_ini,
                        )

                        plot_campos(
                            ds=anomalia_chi200/1e6,
                            variavel_plotagem='chi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'chi_diario', index),
                            ds_contour=anomalia_chi850/1e6,
                            variavel_contour='chi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )
                        
                elif resample_freq == 'sop':
                    
                    semana_encontrada, tempos_iniciais, tempos_finais, num_semana, dates_range, intervalos_fmt, days_of_weeks = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), 
                                                                                                                                                            pd.to_datetime(self.us.time.values), 
                                                                                                                                                            ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), 
                                                                                                                                                            modelo=self.modelo_fmt,
                                                                                                                                                            qtdade_max_semanas=qtdade_max_semanas
                                                                                                                                                            )

                    for index, n_semana in enumerate(us_24h_200.tempo):

                        u200_plot = us_24h_200.sel(tempo=n_semana)
                        v200_plot = vs_24h_200.sel(tempo=n_semana)
                        u850_plot = us_24h_850.sel(tempo=n_semana)
                        v850_plot = vs_24h_850.sel(tempo=n_semana)

                        data_inicial = pd.to_datetime(intervalos_fmt[index][0]).strftime('%Y-%m-%d')
                        data_final = pd.to_datetime(intervalos_fmt[index][1]).strftime('%Y-%m-%d')
                        intervalo1 = data_inicial.replace(data_inicial[:4], ano_ini)
                        intervalo2 = data_final.replace(data_final[:4], ano_ini)

                        intervalo = u200_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = u200_plot.days_of_weeks.item()     

                        u200_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        v200_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        u850_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        v850_plot['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}

                        u200_plot.drop_vars(["intervalo", "days_of_weeks"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u200_semana.nc')
                        v200_plot.drop_vars(["intervalo", "days_of_weeks"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v200_semana.nc')

                        u850_plot.drop_vars(["intervalo", "days_of_weeks"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u850_semana.nc')
                        v850_plot.drop_vars(["intervalo", "days_of_weeks"]).to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v850_semana.nc')

                        # Grads parar calcular PSI e CHI e gerar um .nc
                        os.system(f'/usr/local/grads-2.0.2.oga.2/Contents/opengrads -lbcx {Constants().PATH_ARQUIVOS_TEMP}/gera_psi_chi.gs')

                        # Anomalia psi e chi
                        ds_psi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi200.nc')
                        ds_psi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi850.nc')

                        ds_chi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi200.nc')
                        ds_chi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi850.nc')

                        psi_clim200_plot = psi_clim200.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        psi_clim850_plot = psi_clim850.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        chi_clim200_plot = chi_clim200.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')
                        chi_clim850_plot = chi_clim850.sel(valid_time=slice(intervalo1, intervalo2)).mean(dim='valid_time')

                        anomalia_psi200 = ds_psi200_prev['psi200'] - psi_clim200_plot['psi']
                        anomalia_psi850 = ds_psi850_prev['psi850'] - psi_clim850_plot['psi']

                        anomalia_chi200 = ds_chi200_prev['chi200'] - chi_clim200_plot['chi']
                        anomalia_chi850 = ds_chi850_prev['chi850'] - chi_clim850_plot['chi']

                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lat').mean(dim='lon')
                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lon')

                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lat').mean(dim='lon')
                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lon')

                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lat').mean(dim='lon')
                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lon')

                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lat').mean(dim='lon')
                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lon')

                        anomalia_psi200 = anomalia_psi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_psi850 = anomalia_psi850.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi200 = anomalia_chi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi850 = anomalia_chi850.rename({"lat": "latitude", "lon": "longitude"})

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Anom PSI 200 (shaded) e PSI 850 (lines) - Semana{n_semana.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                        )

                        plot_campos(
                            ds=anomalia_psi200/1e6,
                            variavel_plotagem='psi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'psi_semanal', index),
                            ds_contour=anomalia_psi850/1e6,
                            variavel_contour='psi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )
                            
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Anom CHI 200 (shaded) e CHI 850 (lines) - Semana{n_semana.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                                semana_operativa=True
                        )

                        plot_campos(
                            ds=anomalia_chi200/1e6,
                            variavel_plotagem='chi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'chi_semanal', index),
                            ds_contour=anomalia_chi850/1e6,
                            variavel_contour='chi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

                if anomalia_mensal:

                    us_mean_resample = us_mean.resample(valid_time='M').mean()
                    vs_mean_resample = vs_mean.resample(valid_time='M').mean()

                    for index, time in enumerate(us_mean_resample.valid_time):

                        # Selecionando o mês correspondente
                        mes = pd.to_datetime(time.values).strftime('%b/%Y').title()

                        # Selecionando o mês correspondente
                        us_mean_resample_sel_200 = us_mean_resample.sel(valid_time=time).sel(isobaricInhPa=200)
                        vs_mean_resample_sel_200 = vs_mean_resample.sel(valid_time=time).sel(isobaricInhPa=200)
                        us_mean_resample_sel_850 = us_mean_resample.sel(valid_time=time).sel(isobaricInhPa=850)
                        vs_mean_resample_sel_850 = vs_mean_resample.sel(valid_time=time).sel(isobaricInhPa=850)
                        
                        us_mean_resample_sel_200['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        vs_mean_resample_sel_200['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        us_mean_resample_sel_850['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}
                        vs_mean_resample_sel_850['longitude'].attrs = {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude", "stored_direction": "increasing"}

                        us_mean_resample_sel_200.to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u200_semana.nc')
                        vs_mean_resample_sel_200.to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v200_semana.nc')
                        us_mean_resample_sel_850.to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/u850_semana.nc')
                        vs_mean_resample_sel_850.to_netcdf(f'{Constants().PATH_ARQUIVOS_TEMP}/v850_semana.nc')

                        # Grads parar calcular PSI e CHI e gerar um .nc
                        os.system(f'/usr/local/grads-2.0.2.oga.2/Contents/opengrads -lbcx {Constants().PATH_ARQUIVOS_TEMP}/gera_psi_chi.gs')

                        # Selando o tempo na climatologia
                        tempoini = pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[0].values).strftime('%Y-%m-%d %H')
                        tempo_fim = pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values).strftime('%Y-%m-%d %H')
                        t_clim_ini = tempoini.replace(tempoini[:4], ano_ini)
                        t_clim_fim = tempo_fim.replace(tempo_fim[:4], ano_fim)
                        psi_clim200_sel = psi_clim200.sel(valid_time=slice(t_clim_ini, t_clim_fim)).mean(dim='valid_time').sortby(['lat'])
                        psi_clim850_sel = psi_clim850.sel(valid_time=slice(t_clim_ini, t_clim_fim)).mean(dim='valid_time').sortby(['lat'])
                        chi_clim200_sel = chi_clim200.sel(valid_time=slice(t_clim_ini, t_clim_fim)).mean(dim='valid_time').sortby(['lat'])
                        chi_clim850_sel = chi_clim850.sel(valid_time=slice(t_clim_ini, t_clim_fim)).mean(dim='valid_time').sortby(['lat'])

                        # Anomalia psi e chi
                        ds_psi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi200.nc')
                        ds_psi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/psi850.nc')

                        ds_chi200_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi200.nc')
                        ds_chi850_prev = xr.open_dataset(f'{Constants().PATH_ARQUIVOS_TEMP}/chi850.nc')

                        anomalia_psi200 = ds_psi200_prev['psi200'] - psi_clim200_sel['psi']
                        anomalia_psi850 = ds_psi850_prev['psi850'] - psi_clim850_sel['psi']

                        anomalia_chi200 = ds_chi200_prev['chi200'] - chi_clim200_sel['chi']
                        anomalia_chi850 = ds_chi850_prev['chi850'] - chi_clim850_sel['chi']

                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lat').mean(dim='lon')
                        anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lon')

                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lat').mean(dim='lon')
                        anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lon')

                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lat').mean(dim='lon')
                        anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lon')

                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lat').mean(dim='lon')
                        anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lon')

                        anomalia_psi200 = anomalia_psi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_psi850 = anomalia_psi850.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi200 = anomalia_chi200.rename({"lat": "latitude", "lon": "longitude"})
                        anomalia_chi850 = anomalia_chi850.rename({"lat": "latitude", "lon": "longitude"})

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt,
                            tipo=f'PSI200/850 Média {mes}',
                            cond_ini=self.cond_ini,
                            data_ini=pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[0].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            data_fim=pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            sem_intervalo_semana=True
                        )

                        plot_campos(
                            ds=anomalia_psi200/1e6,
                            variavel_plotagem='psi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'psi_mensal', index),
                            ds_contour=anomalia_psi850/1e6,
                            variavel_contour='psi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt,
                            tipo=f'CHI200/850 Média {mes}',
                            cond_ini=self.cond_ini,
                            data_ini=pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[0].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            data_fim=pd.to_datetime(self.us_mean.sel(valid_time=self.us_mean.valid_time.dt.month == time.dt.month).valid_time[-1].values).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            sem_intervalo_semana=True
                        )

                        plot_campos(
                            ds=anomalia_chi200/1e6,
                            variavel_plotagem='chi',
                            title=titulo,
                            filename=formato_filename(self.modelo_fmt, 'chi_mensal', index),
                            ds_contour=anomalia_chi850/1e6,
                            variavel_contour='chi',
                            color_contour='black',
                            plot_bacias=False,
                            shapefiles=self.shapefiles,
                            path_to_save=path_to_save,
                            **kwargs
                        )

            elif modo == 'geada-inmet':

                if self.t2m_mean is None:
                    _, self.t2m_mean, self.cond_ini = self._carregar_t2m_mean()

                t2m_24h = resample_variavel(self.t2m_mean, self.modelo_fmt, 't2m', resample_freq, modo_agrupador='min', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in t2m_24h.tempo:
                    print(f'Processando {n_24h.item()}...')
                    t2m_24h_plot = t2m_24h.sel(tempo=n_24h)  
                    t2m_24h_plot = t2m_24h_plot-273.15
                    t2m_24h_plot = -1*t2m_24h_plot

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(t2m_24h_plot.data_inicial.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.t2m_mean.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.t2m_mean.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt, qtdade_max_semanas=qtdade_max_semanas)[0]
                    titulo = self._ajustar_tempo_e_titulo(t2m_24h_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Geada - INMET', semana, self.cond_ini)
                
                    plot_campos(
                        ds=t2m_24h_plot['t2m'],
                        variavel_plotagem='geada-inmet',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'geada_inmet_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'geada-cana':

                if self.t2m_mean is None:
                    _, self.t2m_mean, _ = self._carregar_t2m_mean()

                t2m_24h = resample_variavel(self.t2m_mean, self.modelo_fmt, 't2m', resample_freq, modo_agrupador='min', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in t2m_24h.tempo:
                    print(f'Processando {n_24h.item()}...')
                    t2m_24h_plot = t2m_24h.sel(tempo=n_24h)  
                    t2m_24h_plot = t2m_24h_plot-273.15
                    t2m_24h_plot = -1*t2m_24h_plot

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(t2m_24h_plot.data_inicial.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.t2m_mean.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.t2m_mean.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt, qtdade_max_semanas=qtdade_max_semanas)[0]
                    titulo = self._ajustar_tempo_e_titulo(t2m_24h_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Geada - CANA', semana, self.cond_ini)
                
                    plot_campos(
                        ds=t2m_24h_plot['t2m'],
                        variavel_plotagem='geada-cana',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'geada_cana_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'olr':

                if self.olr_mean is None:
                    _, self.olr_mean, self.cond_ini = self._carregar_olr_mean()

                varname = 'ttr' if 'ecmwf' in self.modelo_fmt else 'sulwrf'
                var_24h = resample_variavel(self.olr_mean, self.modelo_fmt, varname, resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in var_24h.tempo:
                    print(f'Processando {n_24h.item()}...')
                    var_24h_plot = var_24h.sel(tempo=n_24h)  # Seleciona o tempo atual

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(var_24h_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.olr_mean.time.values), tempo_ini, ds_tempo_final=self.olr_mean.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            var_24h_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}OLR', semana, self.cond_ini,
                        )

                    else:
                        intervalo = var_24h_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = var_24h_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'OLR - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=var_24h_plot[varname],
                        variavel_plotagem='olr',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'olr_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        ds_contour=var_24h_plot[varname],
                        variavel_contour='olr',
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'mag_vento100':

                if self.us100_mean is None or self.vs100_mean is None or self.cond_ini is None:
                    self.us100, self.vs100, self.us100_mean, self.vs100_mean, self.cond_ini = self._carregar_uv100_mean()

                us_24h = resample_variavel(self.us100_mean, self.modelo_fmt, 'u100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u')
                vs_24h = resample_variavel(self.vs100_mean, self.modelo_fmt, 'v100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v')

                for n_24h in us_24h.tempo:

                    print(f'Processando {n_24h.item()}...')
                    us_plot = us_24h.sel(tempo=n_24h)
                    vs_plot = vs_24h.sel(tempo=n_24h)
                    magnitude = np.sqrt(us_plot['u100']**2 + vs_plot['v100']**2)

                    ds_quiver = xr.Dataset({
                        'u': us_plot['u100'],
                        'v': vs_plot['v100'],
                        'magnitude': magnitude
                    })

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us100.time.values), tempo_ini, ds_tempo_final=self.us100.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e magnitude em 100m', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Vento e magnitude em 100m - Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=magnitude,
                        variavel_plotagem='mag_vento100',
                        title=titulo,
                        filename=formato_filename(self.modelo_fmt, f'magvento100_{self.freqs_map[resample_freq]["prefix_filename"]}', n_24h.item()),
                        ds_quiver=ds_quiver,
                        variavel_quiver='wind850',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'graficos_temperatura':

                if self.t2m_mean is None:
                    _, self.t2m_mean, self.cond_ini = self._carregar_t2m_mean()

                # Ajustando a coordenada de tempo para o BR
                t2m_brt = self.t2m_mean.assign_coords(valid_time=self.t2m_mean.valid_time - np.timedelta64(3,'h'))

                # Máximo e minimos diários
                t2m_max = t2m_brt.resample(valid_time='D').max() - 273.15
                t2m_min = t2m_brt.resample(valid_time='D').min() - 273.15
                t2m_med = t2m_brt.resample(valid_time='D').mean() - 273.15

                # Selecionado os próximos 15 dias
                t2max = t2m_max.sel(valid_time=slice(t2m_max.time - np.timedelta64(self.t2m_mean.time.dt.hour.item(), 'D'), t2m_max.time + np.timedelta64(15,'D')))
                t2min = t2m_min.sel(valid_time=slice(t2m_min.time - np.timedelta64(self.t2m_mean.time.dt.hour.item(), 'D'), t2m_min.time + np.timedelta64(15,'D')))
                t2med = t2m_med.sel(valid_time=slice(t2m_med.time - np.timedelta64(self.t2m_mean.time.dt.hour.item(), 'D'), t2m_med.time + np.timedelta64(15,'D')))

                # Pegando os pontos
                target_lon, target_lat, pontos = get_pontos_localidades()
                t2max_no_ponto = t2max.sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe()
                t2min_no_ponto = t2min.sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe()
                t2med_no_ponto = t2med.sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe()
                t2max_no_ponto = t2max_no_ponto.reset_index('valid_time')
                t2min_no_ponto = t2min_no_ponto.reset_index('valid_time')
                t2med_no_ponto = t2med_no_ponto.reset_index('valid_time')
                t2max_no_ponto['type'] = 'previsão'
                t2min_no_ponto['type'] = 'previsão'
                t2med_no_ponto['type'] = 'previsão'
                t2max_no_ponto['mes'] = t2max_no_ponto['valid_time'].dt.month
                t2min_no_ponto['mes'] = t2min_no_ponto['valid_time'].dt.month
                t2med_no_ponto['mes'] = t2med_no_ponto['valid_time'].dt.month
                colunas_para_usar = ['valid_time', 't2m', 'type', 'mes']
                t2max_no_ponto = t2max_no_ponto[colunas_para_usar].reset_index()
                t2min_no_ponto = t2min_no_ponto[colunas_para_usar].reset_index()
                t2med_no_ponto = t2med_no_ponto[colunas_para_usar].reset_index()

                # Lendo o csv observado dos ultimos 2 meses
                mes_atual = str(self.t2m_mean.time.dt.month.item()).zfill(2)
                ano_atual = str(self.t2m_mean.time.dt.year.item()).zfill(4)
                mes_anterior = (pd.to_datetime(self.t2m_mean.time.item()) - pd.DateOffset(months=1)).strftime('%m')
                ano_anterior = (pd.to_datetime(self.t2m_mean.time.item()) - pd.DateOffset(months=1)).strftime('%Y')

                obs_tmax_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMAX_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})
                obs_tmin_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMIN_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})
                obs_tmed_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMED_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})
                obs_tmax_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMAX_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})
                obs_tmin_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMIN_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})
                obs_tmed_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMED_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat', 'valid_time'], errors='ignore').rename(columns={'time': 'valid_time'})

                obs_tmax = pd.concat([obs_tmax_anterior, obs_tmax_atual], ignore_index=True)
                obs_tmin = pd.concat([obs_tmin_anterior, obs_tmin_atual], ignore_index=True)
                obs_tmed = pd.concat([obs_tmed_anterior, obs_tmed_atual], ignore_index=True)
                obs_tmax['type'] = 'observado'
                obs_tmin['type'] = 'observado'
                obs_tmed['type'] = 'observado'
                obs_tmax['valid_time'] = pd.to_datetime(obs_tmax['valid_time'])
                obs_tmin['valid_time'] = pd.to_datetime(obs_tmin['valid_time'])
                obs_tmed['valid_time'] = pd.to_datetime(obs_tmed['valid_time'])
                ultimos_15_dias = pd.date_range(
                    start=(pd.to_datetime(self.t2m_mean.time.item()) - pd.DateOffset(days=15)).floor("D"),
                    end=pd.to_datetime(self.t2m_mean.time.item()).floor("D"),
                    freq="D"
                )
                obs_tmax = obs_tmax[obs_tmax['valid_time'].isin(ultimos_15_dias)]
                obs_tmin = obs_tmin[obs_tmin['valid_time'].isin(ultimos_15_dias)]
                obs_tmed = obs_tmed[obs_tmed['valid_time'].isin(ultimos_15_dias)]
                obs_tmax['mes'] = obs_tmax['valid_time'].dt.month
                obs_tmin['mes'] = obs_tmin['valid_time'].dt.month
                obs_tmed['mes'] = obs_tmed['valid_time'].dt.month
                
                # Juntando com a previsao
                t2max_no_ponto = pd.concat([obs_tmax.rename(columns={'tmax': 't2m'}), t2max_no_ponto], axis=0)
                t2min_no_ponto = pd.concat([obs_tmin.rename(columns={'tmin': 't2m'}), t2min_no_ponto], axis=0)
                t2med_no_ponto = pd.concat([obs_tmed.rename(columns={'tmed': 't2m'}), t2med_no_ponto], axis=0)

                # Abrindo os arquivos de climatologia
                clim_tmax = pd.read_csv(f'{Constants().PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL}/tmax_cidades.txt', sep=' ', names=np.arange(1,13))
                clim_tmin = pd.read_csv(f'{Constants().PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL}/tmin_cidades.txt', sep=' ', names=np.arange(1,13))
                clim_tmed = pd.read_csv(f'{Constants().PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL}/tmed_cidades.txt', sep=' ', names=np.arange(1,13))
                clim_tmax['id'] = pontos['id']
                clim_tmax = clim_tmax.melt(id_vars='id', value_name='t2m_clim', var_name='month')
                clim_tmin['id'] = pontos['id']
                clim_tmin = clim_tmin.melt(id_vars='id', value_name='t2m_clim', var_name='month')
                clim_tmed['id'] = pontos['id']
                clim_tmed = clim_tmed.melt(id_vars='id', value_name='t2m_clim', var_name='month')

                # Juntar pelo id e mês
                t2max_no_ponto = t2max_no_ponto.reset_index().merge(clim_tmax, left_on=["id", "mes"], right_on=["id", "month"], how="left")
                t2min_no_ponto = t2min_no_ponto.reset_index().merge(clim_tmin, left_on=["id", "mes"], right_on=["id", "month"], how="left")
                t2med_no_ponto = t2med_no_ponto.reset_index().merge(clim_tmed, left_on=["id", "mes"], right_on=["id", "month"], how="left")
                t2max_no_ponto['valid_time_fmt'] = t2max_no_ponto['valid_time'].dt.strftime('%d/%m')
                t2min_no_ponto['valid_time_fmt'] = t2min_no_ponto['valid_time'].dt.strftime('%d/%m')
                t2med_no_ponto['valid_time_fmt'] = t2med_no_ponto['valid_time'].dt.strftime('%d/%m')

                # Agrupar no submercado e calcular a temperatura por peso
                df_submercado = CONSTANTES['city_peso']
                t2med_no_ponto_submercado = t2med_no_ponto[t2med_no_ponto['id'].isin(df_submercado['id'])]
                t2med_no_ponto_submercado['peso'] = t2med_no_ponto_submercado['id'].map(df_submercado.set_index('id')['weights'])
                t2med_no_ponto_submercado['regiao'] = t2med_no_ponto_submercado['id'].map(df_submercado.set_index('id')['region'])
                t2med_no_ponto_submercado['t2m_peso'] = t2med_no_ponto_submercado['t2m'] * t2med_no_ponto_submercado['peso']
                t2med_no_ponto_submercado['t2m_clim_peso'] = t2med_no_ponto_submercado['t2m_clim'] * t2med_no_ponto_submercado['peso']
                t2med_no_ponto_submercado = t2med_no_ponto_submercado.groupby(['regiao', 'valid_time', 'type'])[['t2m_peso', 't2m_clim_peso']].sum().reset_index()
                t2med_no_ponto_submercado['valid_time_fmt'] = t2med_no_ponto_submercado['valid_time'].dt.strftime('%d/%m')

                # Grafico por id
                for id in t2max_no_ponto['id'].unique():

                    print(f'Gráficos temperatura ID: {id}')

                    dados_t2max = t2max_no_ponto[t2max_no_ponto['id'] == id]
                    dados_t2min = t2min_no_ponto[t2min_no_ponto['id'] == id]

                    titulo = f"{CONSTANTES['city_dict'][id]}\n{self.modelo_fmt.upper()} - {self.cond_ini}"
                    filename = f'{path_to_save}/{id}'
                    plot_graficos_2d(df=dados_t2max, tipo='tmax_tmin', df_tmin=dados_t2min, titulo=titulo, filename=filename)
                    
                    path_to_save_geada = f'{self.path_savefiguras}/geadas_grafs'
                    os.makedirs(path_to_save_geada, exist_ok=True)
                    filename = f'{path_to_save_geada}/{id}_geada'
                    plot_graficos_2d(df=dados_t2min, tipo='geada', titulo=titulo, filename=filename)

                # Grafico por submercado
                for submercado in t2med_no_ponto_submercado['regiao'].unique():

                    print(f'Gráficos temperatura Submercado: {submercado}')

                    dados_submercado = t2med_no_ponto_submercado[t2med_no_ponto_submercado['regiao'] == submercado].rename(columns={'t2m_peso': 't2m', 't2m_clim_peso': 't2m_clim'})

                    titulo = f"{submercado}\n{self.modelo_fmt.upper()} - {self.cond_ini}"
                    filename = f'{path_to_save}/{submercado}'
                    plot_graficos_2d(df=dados_submercado, tipo='submercado', titulo=titulo, filename=filename)

                    path_to_save_csv = f'/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/csv_temperatura/{self.modelo_fmt}'
                    dados_submercado = dados_submercado.rename(columns={'t2m_peso': 't2m_w', 't2m_clim_peso': 't2m_clim_w'})
                    dados_submercado.to_csv(f'{path_to_save_csv}/{self.modelo_fmt}_{submercado}_{self.data_fmt}.csv')

            elif modo == 'graficos_vento':

                if self.us100_mean is None or self.vs100_mean is None or self.cond_ini is None:
                    self.us100, self.vs100, self.us100_mean, self.vs100_mean, self.cond_ini = self._carregar_uv100_mean()

                us_24h = resample_variavel(self.us100_mean, self.modelo_fmt, 'u100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u')
                vs_24h = resample_variavel(self.vs100_mean, self.modelo_fmt, 'v100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v')

                AREAS = {

                'LITORAL_NORTE' : [-2, -4.5, -41.5, -38],
                'LITORAL_NE_NORTE' : [-4.5, -7.5, -38.5, -34.5],
                'LITORAL_NE_SUL' : [-8.5, -11.5, -38.5, -35],
                'BAHIA' : [-6, -15, -43, -40],

                }

                # Climatologia do vento
                uv100_clim = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_UV100}/monthly_clim_uv100.nc')

                for index, area in enumerate(AREAS):

                    latini = AREAS.get(area)[0]
                    latfim = AREAS.get(area)[1]
                    lonini = AREAS.get(area)[2]
                    lonfim = AREAS.get(area)[3]

                    area_u = us_24h.sel(latitude=slice(latfim, latini), longitude=slice(lonini, lonfim)).mean(dim='longitude').mean(dim='latitude')
                    area_v = vs_24h.sel(latitude=slice(latfim, latini), longitude=slice(lonini, lonfim)).mean(dim='longitude').mean(dim='latitude')

                    # Climatologia
                    clim_sel = uv100_clim.sel(month=self.us100.valid_time.dt.month)
                    clim_sel = clim_sel.sel(latitude=slice(latini, latfim), longitude=slice(lonini, lonfim))
                    clim_sel_u = resample_variavel(clim_sel, self.modelo_fmt, 'u100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='u').mean(dim='longitude').mean(dim='latitude')
                    clim_sel_v = resample_variavel(clim_sel, self.modelo_fmt, 'v100', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, anomalia_sop=anomalia_sop, var_anomalia='v').mean(dim='longitude').mean(dim='latitude')

                    # Previsao
                    u_med_area = area_u['u100'].values
                    v_med_area = area_v['v100'].values
                    magnitude = np.sqrt(u_med_area**2 + v_med_area**2)

                    # Climatologia
                    u_med_area_clim = clim_sel_u['u100'].values
                    v_med_area_clim = clim_sel_v['v100'].values
                    magnitude_clim = np.sqrt(u_med_area_clim**2 + v_med_area_clim**2)

                    # Tempos para montar o dataframe
                    valid_times = clim_sel_u.data_final.dt.strftime('%d/%m').values

                    # montando o df
                    df = pd.DataFrame({
                        'data': valid_times,
                        'magnitude': magnitude,
                        'magnitude_clim': magnitude_clim,
                        'Climatologia': magnitude_clim
                        
                    })

                    # path_to_save_csv = f'/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/csv_eolica/{self.modelo_fmt}'
                    # df.to_csv(f'{path_to_save_csv}/{self.modelo_fmt}_{area}_{self.data_fmt}_diario.csv')

                    # Titulo do plot
                    titulo = f'{self.modelo_fmt.upper()} - Magnitude do vento a 100m - {area.replace("_", " ")}\nCondição Inicial: {self.cond_ini} \u2022 Climatologia ERA5 [1991-2020]'
                    filename = f'{path_to_save}/mag_vento100_{area}'
                    plot_graficos_2d(df=df, tipo='vento', titulo=titulo, filename=filename)

                    # if index > 0:
                    #     df_temp = pd.concat([df, df_temp], axis=1)

                    # else:
                    #     df_temp = df

                # colunas = [x for x in df_temp.columns if 'Climatologia' not in x]
                # df_media = pd.DataFrame(df_temp[colunas].mean(axis=1), columns=list(set(colunas)))
                # df_media['Climatologia'] = df_temp['Climatologia'].mean(axis=1)
                # df_media.to_csv(f'{path_to_save_csv}/{self.modelo_fmt}_MEDIANORDESTE_{self.data_fmt}_diario.csv')

            elif modo == 'pnmm_vento850':

                varname = 'msl' if 'ecmwf' in self.modelo_fmt else 'prmsl'

                # Pnmm
                if self.pnmm_mean is None:
                    _, self.pnmm_mean, _ = self._carregar_pnmm_mean()

                # Apenas para combar com o vento     
                if self.pnmm_mean.longitude.min() >= 0:
                    pnmm_mean = self.pnmm_mean.assign_coords(longitude=(((self.pnmm_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

                # Vento
                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                for index, n_24h in enumerate(pnmm_mean.valid_time):

                    print(f'Processando {index}...')

                    us_plot = self.us_mean.sel(valid_time=n_24h)
                    vs_plot = self.vs_mean.sel(valid_time=n_24h)
                    pnmm_plot = pnmm_mean.sel(valid_time=n_24h)

                    ds_quiver = xr.Dataset({
                        'u': us_plot['u'].sel(isobaricInhPa=850).drop_vars('isobaricInhPa'), 
                        'v': vs_plot['v'].sel(isobaricInhPa=850).drop_vars('isobaricInhPa'), 
                        'pnmm_plot': pnmm_plot[varname]*1e-2
                    })

                    tempo_ini = pd.to_datetime(n_24h.item())
                    print(ds_quiver)
                    print(tempo_ini)
                    semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=pd.to_datetime(self.us.valid_time[-1].values) + pd.Timedelta(days=1), modelo=self.modelo_fmt)[0]
                    print(semana)

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=f'PNMM, Vento850hPa', cond_ini=self.cond_ini,
                        data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        semana=semana, unico_tempo=True
                    )

                    plot_campos(ds=ds_quiver['pnmm_plot'], 
                                variavel_plotagem='pnmm_vento', 
                                title=titulo, 
                                filename=formato_filename(self.modelo_fmt, 'pnmm_vento850', index),
                                plot_bacias=False, ds_quiver=ds_quiver, 
                                variavel_quiver='wind850', 
                                ds_contour=ds_quiver['pnmm_plot'], 
                                variavel_contour='pnmm', 
                                color_contour='black',
                                shapefiles=self.shapefiles,
                                path_to_save=path_to_save,
                                with_norm=True,
                                **kwargs
                                )         

            elif modo == 'indices-itcz':

                limiar = 235
                lon_range=(326, 335)

                if self.olr_mean is None:
                    _, self.olr_mean, self.cond_ini = self._carregar_olr_mean()

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                if self.tp_mean is None or self.cond_ini is None or self.tp is None:
                    self.tp, self.tp_mean, self.cond_ini = self._carregar_tp_mean()

                varname_olr = 'ttr' if 'ecmwf' in self.modelo_fmt else 'sulwrf'

                # Colocando vento em 0 a 360
                ds_vento = ajusta_lon_0_360(self.vs_mean, 'longitude').sel(isobaricInhPa=925)
                ds_vento['abs_vwnd'] = np.abs(ds_vento['v'])

                ds_chuva = self.tp_mean
                ds_olr = ajusta_lon_0_360(self.olr_mean, 'longitude')

                # pegando apenas os dias completos, 12 nao precisa pq tem todos os dias
                inicializacao = pd.to_datetime(ds_chuva.time.values)
                if inicializacao.hour == 0:
                    ds_chuva = ds_chuva.isel(valid_time=slice(None, -2))
                elif inicializacao.hour == 6:
                    ds_chuva = ds_chuva.isel(valid_time=slice(None, -3))
                elif inicializacao.hour == 18:
                    ds_chuva = ds_chuva.isel(valid_time=slice(None, -1))

                ds_olr_crop = ds_olr.sel(valid_time=ds_chuva.valid_time)
                ds_vento = ds_vento.sel(valid_time=ds_chuva.valid_time)

                # transformando em diario das 12 as 12
                tempos = ds_olr_crop.valid_time
                delta_t = 13
                tempos_shifted = tempos - pd.Timedelta(hours=delta_t)

                ds_chuva['valid_time'] = tempos_shifted
                ds_chuva = ds_chuva.sel(valid_time=ds_chuva.valid_time>=inicializacao).resample(valid_time='D').sum()
                ds_chuva['valid_time'] = ds_chuva['valid_time'] + pd.Timedelta(days=1) 

                ds_olr_crop['valid_time'] = tempos_shifted
                ds_olr_crop = ds_olr_crop.sel(valid_time=ds_olr_crop.valid_time>=inicializacao).resample(valid_time='D').mean()
                ds_olr_crop['valid_time'] = ds_olr_crop['valid_time'] + pd.Timedelta(days=1) 

                ds_vento['valid_time'] = tempos_shifted
                ds_vento = ds_vento.sel(valid_time=ds_vento.valid_time>=inicializacao).resample(valid_time='D').mean()
                ds_vento['valid_time'] = ds_vento['valid_time'] + pd.Timedelta(days=1) 

                # Inicializando listas que vão guardar os resultados
                lats_min = []
                lats_max = []
                lats_menor_olr = []
                lats_menor_vento = []
                intensidades_chuva = []
                intensidades_olr = []
                tempos_fmt = []
                latitudes_media_vento_olr = []

                # Iterando sobre cada tempo fornecido
                tempos = ds_chuva['valid_time'].values
                for t in tempos:

                    achou_banda = False

                    for lon_ref in range(lon_range[0], lon_range[1] + 1):

                        ds_olr_mask = xr.where(ds_olr_crop[varname_olr] < limiar, ds_olr_crop[varname_olr], np.nan)
                        ds_olr_mask_longitude_ref = ds_olr_mask.sel(longitude=lon_ref).sel(valid_time=t).sel(latitude=slice(-5.5, 13.5))

                        # Para o vento
                        ds_vento_crop = ds_vento.sel(longitude=lon_ref, method='nearest').sel(valid_time=t)

                        # Banda da ITCZ pela OLR
                        valid_latitudes = ds_olr_mask_longitude_ref.dropna(dim="latitude").latitude

                        if valid_latitudes.sizes["latitude"] != 0:
                            achou_banda = True

                            # Latitude inicial 
                            lat_min = valid_latitudes.min().item()

                            # Latitude final
                            lat_max = valid_latitudes.max().item()

                            # Valor da latitude da menor OLR na banda
                            latitude_min_olr = ds_olr_mask_longitude_ref.argmin(dim='latitude')
                            latitude_min_value = ds_olr_mask_longitude_ref['latitude'].isel(latitude=latitude_min_olr.values)

                            # Intensidade 
                            prec_intensidade = ds_chuva.sel(latitude=slice(lat_min, lat_max)).sel(valid_time=t).sel(longitude=lon_ref, method='nearest')
                            intensidade_chuva = prec_intensidade['tp'].mean(dim='latitude')
                            ds_olr_intensidade = ds_olr_mask_longitude_ref.sel(latitude=slice(lat_min, lat_max))
                            intensidade = ds_olr_intensidade.mean(dim='latitude')

                            # Determinar para o vento na banda
                            ds_vento_crop = ds_vento_crop.sel(latitude=slice(lat_min, lat_max))
                            indice_lat_vento_min = ds_vento_crop['abs_vwnd'].argmin(dim='latitude')
                            latitude_min_vento_value = ds_vento_crop['latitude'].isel(latitude=indice_lat_vento_min.values).item()

                            # Valor médio entre a ITCZolr e a ITCZvwnd
                            latitude_media_vento_olr = np.mean([latitude_min_vento_value, latitude_min_value])

                            # Adicionando os valores calculados às listas
                            lats_min.append(lat_min)
                            lats_max.append(lat_max)
                            lats_menor_olr.append(latitude_min_value.item())
                            intensidades_chuva.append(intensidade_chuva.values)
                            intensidades_olr.append(intensidade.values)
                            lats_menor_vento.append(latitude_min_vento_value)
                            tempos_fmt.append(t)
                            latitudes_media_vento_olr.append(latitude_media_vento_olr)

                            break

                    if not achou_banda:
                        print(f'Não achou a banda para o tempo {t}')
                        latitude_min_value = np.nan
                        latitude_media_vento_olr = np.nan
                        lat_min = np.nan
                        lat_max = np.nan
                        intensidade = np.nan
                        intensidade_chuva = np.nan
                        latitude_min_vento_value = np.nan

                        # Adicionando os valores calculados às listas
                        lats_min.append(lat_min)
                        lats_max.append(lat_max)
                        lats_menor_olr.append(latitude_min_value)
                        intensidades_olr.append(intensidade)
                        intensidades_chuva.append(intensidade_chuva)
                        lats_menor_vento.append(latitude_min_vento_value)
                        tempos_fmt.append(t)
                        latitudes_media_vento_olr.append(latitude_media_vento_olr)
                
                # Criando o DataFrame final
                df_resultado = pd.DataFrame({
                    'tempo': tempos_fmt,
                    'lats_min': lats_min,
                    'lats_max': lats_max,
                    'lats_menor_olr': lats_menor_olr,
                    'lats_menor_vento': lats_menor_vento,
                    'lats_media_vento_olr': latitudes_media_vento_olr,
                    'intensidades_olr': intensidades_olr,
                    'intensidades_chuva': intensidades_chuva, 
                })

                df_resultado['largura'] = df_resultado['lats_max'] - df_resultado['lats_min']
                df_resultado.rename({'tempo': 'dt_prevista'}, axis=1, inplace=True)
                df_resultado.fillna(999, inplace=True) # coloca 999 para conseguir subir no banco
                df_resultado['str_modelo'] = self.modelo_fmt.lower()
                df_resultado['dt_prevista'] = df_resultado['dt_prevista'].dt.strftime('%Y-%m-%d')
                df_resultado["intensidades_olr"] = df_resultado["intensidades_olr"].astype(float)
                df_resultado["intensidades_chuva"] = df_resultado["intensidades_chuva"].astype(float)
                df_resultado['dt_rodada'] = inicializacao.strftime('%Y-%m-%d')
                df_resultado['hr_rodada'] = inicializacao.hour

                # Adicionando ao db
                response = requests.post(f'{Constants().API_URL_APIV2}/meteorologia/indices-itcz-previstos', verify=False, json=df_resultado.to_dict('records'), headers=get_auth_header()) 
                if response.status_code == 200:
                    print('Indices da ITCZ inseridos no banco com sucesso!')

        except Exception as e:
            print(f'Erro ao gerar variaveis dinâmicas ({modo}): {e}')

    def _processar_chuva_db(self, **kwargs):

        try:

            tp_prev = get_prec_db(self.modelo_fmt, pd.to_datetime(self.produto_config_sf.data).strftime('%Y-%m-%d'), str(self.produto_config_sf.inicializacao).zfill(2))
            cond_ini = f"{self.produto_config_sf.data.strftime('%d/%m/%Y')} {str(self.produto_config_sf.inicializacao).zfill(2)} UTC"
            tp_prev['dt_prevista'] = pd.to_datetime(tp_prev['dt_prevista'])
            df_prev = tp_prev.groupby(['dt_prevista', 'semana', 'geometry', 'nome_bacia'])['vl_chuva'].mean().reset_index()

            plot_semana = kwargs.get('plot_semana', False)
            acumulado_total = kwargs.get('acumulado_total', False)
            prec_24h = kwargs.get('prec_24h', False)

            if plot_semana:
                semana_encontrada, tempos_iniciais, tempos_finais, num_semana, dates_range, intervalos_fmt, days_of_weeks = encontra_semanas_operativas(self.produto_config_sf.data, 
                                                                self.produto_config_sf.data, 
                                                                qtdade_max_semanas=3, 
                                                                ds_tempo_final=tp_prev['dt_prevista'].max(),
                                                                modelo='pconjunto-ons',
                                                                )

                path_to_save = f'{self.path_savefiguras}/semanas_operativas'
                variavel_plotagem = 'chuva_ons_geodataframe'
                os.makedirs(path_to_save, exist_ok=True)
                
                for index, semana in enumerate(tp_prev['semana'].unique()):
                    dados_plot = df_prev[df_prev['semana'] == semana]
                    dados_plot = dados_plot.groupby(['geometry', 'nome_bacia'])['vl_chuva'].sum().reset_index()
                    ini = ajustar_hora_utc(pd.to_datetime(intervalos_fmt[index][0])).strftime("%d/%m/%Y %H UTC").replace(" ", "\\ ")
                    fim = ajustar_hora_utc(pd.to_datetime(intervalos_fmt[index][1])).strftime("%d/%m/%Y %H UTC").replace(" ", "\\ ")
                    intervalo = f"{ini}\ até\ {fim}"

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=f'Semana{semana}',
                        cond_ini=cond_ini, intervalo=intervalo, days_of_week=days_of_weeks[index],
                        semana_operativa=True
                    )

                    dados_plot = gpd.GeoDataFrame(dados_plot, geometry="geometry", crs="EPSG:4326")
                    plot_df_to_mapa(dados_plot, 
                                    path_to_save=path_to_save,
                                    titulo=titulo, 
                                    shapefiles=self.shapefiles, 
                                    variavel_plotagem=variavel_plotagem,
                                    column_plot='vl_chuva', _type='bruto', filename=f'tp_total_{self.modelo_fmt}')

            if acumulado_total:

                path_to_save = f'{self.path_savefiguras}/total'
                os.makedirs(path_to_save, exist_ok=True)
                variavel_plotagem = 'acumulado_total_geodataframe'

                dados_plot = df_prev.groupby(['geometry', 'nome_bacia'])['vl_chuva'].sum().reset_index()
                
                ini = ajustar_hora_utc(pd.to_datetime(tp_prev['dt_prevista'].min()))
                fim = ajustar_hora_utc(pd.to_datetime(tp_prev['dt_prevista'].max()))

                titulo = gerar_titulo(
                    modelo=self.modelo_fmt,
                    tipo='Acumulado total',
                    cond_ini=cond_ini,
                    data_ini=ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    data_fim=fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    sem_intervalo_semana=True
                )

                dados_plot = gpd.GeoDataFrame(dados_plot, geometry="geometry", crs="EPSG:4326")
                plot_df_to_mapa(dados_plot, 
                                path_to_save=path_to_save,
                                titulo=titulo, 
                                shapefiles=self.shapefiles, 
                                variavel_plotagem=variavel_plotagem,
                                column_plot='vl_chuva', _type='bruto', filename=f'tp_total_{self.modelo_fmt}')

            if prec_24h:

                path_to_save = f'{self.path_savefiguras}/24h'
                variavel_plotagem = 'chuva_ons_geodataframe'
                os.makedirs(path_to_save, exist_ok=True)
                
                for index, dt_prevista in enumerate(df_prev['dt_prevista'].unique()):

                    dados_plot = df_prev[df_prev['dt_prevista'] == dt_prevista]
                    dados_plot = dados_plot.groupby(['geometry', 'nome_bacia'])['vl_chuva'].sum().reset_index()

                    semana_encontrada, tempos_iniciais, tempos_finais, num_semana, dates_range, intervalos_fmt, days_of_weeks = encontra_semanas_operativas(self.produto_config_sf.data, 
                                                                    dt_prevista, 
                                                                    qtdade_max_semanas=3, 
                                                                    ds_tempo_final=tp_prev['dt_prevista'].max() + pd.Timedelta(days=1),
                                                                    modelo='pconjunto-ons',
                                                                    )


                    ini = pd.to_datetime(dt_prevista - pd.Timedelta(hours=12)).strftime("%d/%m/%Y %H UTC").replace(" ", "\\ ")
                    fim = pd.to_datetime(dt_prevista + pd.Timedelta(hours=12)).strftime("%d/%m/%Y %H UTC").replace(" ", "\\ ")
                    titulo = gerar_titulo(
                                modelo=self.modelo_fmt,
                                tipo='PREC24HRS',
                                cond_ini=cond_ini,
                                data_ini=ini,
                                data_fim=fim,
                                semana=semana_encontrada,
                    )

                    dados_plot = gpd.GeoDataFrame(dados_plot, geometry="geometry", crs="EPSG:4326")
                    plot_df_to_mapa(dados_plot, 
                                    path_to_save=path_to_save,
                                    titulo=titulo, 
                                    shapefiles=self.shapefiles, 
                                    variavel_plotagem=variavel_plotagem,
                                    column_plot='vl_chuva', _type='bruto', filename=f'tp_24h_{self.modelo_fmt}_{index}')

        except Exception as e:
            print(f'Erro ao gerar mapas db: {e}')

    ###################################################################################################################

    def gerar_prec24h(self, **kwargs):
        self._processar_precipitacao('24h', **kwargs)

    def gerar_prec24h_biomassa(self, **kwargs):
        self._processar_precipitacao('24h_biomassa', **kwargs)

    def gerar_acumulado_total(self, **kwargs):
        self._processar_precipitacao('total', **kwargs)

    def gerar_semanas_operativas(self, **kwargs):
        self._processar_precipitacao('semanas_operativas', **kwargs)

    def gerar_media_bacia_smap(self, **kwargs):
        self._processar_precipitacao('bacias_smap', **kwargs)

    def gerar_probabilidade_climatologia(self, **kwargs):
        self._processar_precipitacao('probabilidade_climatologia', **kwargs)

    def gerar_probabilidade_limiar(self, **kwargs):
        self._processar_precipitacao('probabilidade_limiar', **kwargs)

    def gerar_desvpad(self, **kwargs):
        self._processar_precipitacao('desvpad', **kwargs)

    def gerar_diferenca_tp(self, **kwargs):
        self._processar_precipitacao('diferenca', **kwargs)

    def gerar_prec_pnmm(self, **kwargs):
        self._processar_precipitacao('prec_pnmm', **kwargs)

    def gerar_estacao_chuvosa(self, **kwargs):
        self._processar_precipitacao('estacao_chuvosa', **kwargs)

    def gerar_jato_div200(self, **kwargs):
        self._processar_varsdinamicas('jato_div200', **kwargs)

    def gerar_vento_temp850(self, **kwargs):
        self._processar_varsdinamicas('vento_temp850', **kwargs)

    def gerar_geop_vort500(self, **kwargs):
        self._processar_varsdinamicas('geop_vort500', **kwargs)

    def gerar_frentes_frias(self, **kwargs):
        self._processar_varsdinamicas('frentes', **kwargs)

    def gerar_geop500(self, **kwargs):
        self._processar_varsdinamicas('geop500', **kwargs)

    def gerar_ivt(self, **kwargs):
        self._processar_varsdinamicas('ivt', **kwargs)

    def gerar_vento_div850(self, **kwargs):
        self._processar_varsdinamicas('vento_div850', **kwargs)

    def gerar_chuva_geop500_vento850(self, **kwargs):
        self._processar_varsdinamicas('chuva_geop500_vento850', **kwargs)

    def gerar_pnmm_vento850(self, **kwargs):
        self._processar_varsdinamicas('pnmm_vento850', **kwargs)

    def gerar_psi(self, **kwargs):
        self._processar_varsdinamicas('anomalia_psi', **kwargs)

    def gerar_geada_inmet(self, **kwargs):
        self._processar_varsdinamicas('geada-inmet', **kwargs)

    def gerar_geada_cana(self, **kwargs):
        self._processar_varsdinamicas('geada-cana', **kwargs)

    def gerar_olr(self, **kwargs):
        self._processar_varsdinamicas('olr', **kwargs)

    def gerar_mag_vento100(self, **kwargs):
        self._processar_varsdinamicas('mag_vento100', **kwargs)

    def gerar_graficos_temp(self, **kwargs):
        self._processar_varsdinamicas('graficos_temperatura', **kwargs)

    def gerar_graficos_chuva(self, **kwargs):
        self._processar_precipitacao('graficos_precipitacao', **kwargs)

    def gerar_graficos_v100(self, **kwargs):
        self._processar_varsdinamicas('graficos_vento', **kwargs)

    def gerar_prec_db(self, **kwargs):
        self._processar_chuva_db(**kwargs)

    def gerar_indices_itcz(self, **kwargs):
        self._processar_varsdinamicas('indices-itcz', **kwargs)

    ###################################################################################################################

    def salva_netcdf(self, variavel: str, ensemble=True):

        try:

            if variavel == 'tp':
                tp = get_dado_cacheado('tp', self.produto_config_sf, **self.tp_params)
                ds = ensemble_mean(tp) if ensemble else tp.copy()

            else:
                print('Ainda implementando')
                return

            # Salvando o dataset como NetCDF
            path_save = CONSTANTES["path_save_netcdf"]
            os.makedirs(path_save, exist_ok=True)
            cond_ini = get_inicializacao_fmt(ds, format='%Y%m%d%H')
            ds[variavel].to_netcdf(f'{path_save}/{self.modelo_fmt}_{variavel}_{cond_ini}.nc')

            print(f'NetCDF salvo com sucesso: {path_save}/{self.modelo_fmt}_{variavel}_{cond_ini}.nc')

        except Exception as e:
           print(f'Erro ao salvar NetCDF: {e}')

    def gerar_diferencas(self, timedelta=1, variavel='tp', dif_total=True, dif_01_15d=False, dif_15_final=False, **kwargs):

        try:

            print('Gerando mapa de diferença total ...')
            path_to_save = f'{self.path_savefiguras}/diferenca'

            # Arquivo atual
            ds = get_dado_cacheado(variavel, self.produto_config_sf, **self.tp_params)
            ds_mean = ensemble_mean(ds)
            cond_ini = get_inicializacao_fmt(ds_mean)

            # Abrindo o arquivo anterior (precisa ter sido previamente salvo)
            data_anterior = pd.to_datetime(ds_mean.time.values) - pd.Timedelta(days=timedelta)
            data_anterior_fmt = data_anterior.strftime('%Y%m%d%H')
            ds_anterior = xr.open_dataset(f'{CONSTANTES["path_save_netcdf"]}/{self.modelo_fmt}_{variavel}_{data_anterior_fmt}.nc')

            # Listas para plot
            difs = []
            dates = []
            tipos_dif = []

            if dif_total:
                # Diferença total
                ti = ds_mean['valid_time'].values[0]
                tf = ds_anterior['valid_time'].values[-1]

                # Acumulando
                ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                # Ds diferença
                ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                difs.append(ds_diferenca)
                dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                tipos_dif.append('Total')

            if dif_01_15d:
                # Diferença dos dias 1 ao 15
                ti = ds_mean['valid_time'].values[0]
                tf = pd.to_datetime(ti) + pd.Timedelta(days=15)

                # Acumulando
                ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                # Ds diferença
                ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                difs.append(ds_diferenca)
                dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                tipos_dif.append('15D')

            if dif_15_final:
                # Diferença dos dias 15 ao restante
                ti = pd.to_datetime(ds_mean['valid_time'].values[0]) + pd.Timedelta(days=15)
                tf = ds_anterior['valid_time'].values[-1]

                # Acumulando
                ds_acumulado = ds_mean.sel(valid_time=slice(ti, tf)).sum('valid_time')
                ds_acumulado_anterior = ds_anterior.sel(valid_time=slice(ti, tf)).sum('valid_time')

                # Ds diferença
                ds_diferenca = ds_acumulado[variavel] - ds_acumulado_anterior[variavel]
                difs.append(ds_diferenca)
                dates.append([pd.to_datetime(ti), pd.to_datetime(tf)])
                tipos_dif.append('15D-Final')

            for index, (dif, date, tipo_dif) in enumerate(zip(difs, dates, tipos_dif)):

                titulo = gerar_titulo(
                    modelo=self.modelo_fmt, sem_intervalo_semana=True, tipo=f'Diferença {tipo_dif}', cond_ini=cond_ini,
                    data_ini=date[0].strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    data_fim=date[1].strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                )

                plot_campos(
                    ds=dif,
                    variavel_plotagem='diferenca',
                    title=titulo,
                    shapefiles=self.shapefiles,
                    filename=f'{index}_dif_{self.modelo_fmt}_{date[0].strftime("%Y%m%d%H")}_{date[1].strftime("%Y%m%d%H")}_{tipo_dif}',
                    path_to_save=path_to_save,
                    **kwargs
                )

        except Exception as e:
            print(f'Erro ao gerar diferenças: {e}')

    ###################################################################################################################

###################################################################################################################

class GeraProdutosObservacao:

    def __init__(self, produto_config, shapefiles=None):
        
        self.produto_config = produto_config
        self.shapefiles = shapefiles
        self.modelo_fmt = self.produto_config.modelo
        self.data = pd.to_datetime(self.produto_config.data) + pd.Timedelta(hours=12)

        if self.modelo_fmt == 'merge':
            self.modelo_fmt = self.modelo_fmt + 'gpm'

        # Inicializando variáveis
        self.tp = None
        self.cond_ini = None
        self.tmax = None
        self.tmin = None
        self.tmed = None

    ###################################################################################################################

    def _carregar_tp_mean(self, **kwargs):

        """Carrega e processa o campo tp apenas uma vez."""
        # tp = get_dado_cacheado(**kwargs)
        tp = self.produto_config.open_model_file(**kwargs)
        cond_ini = get_inicializacao_fmt(tp)

        if isinstance(cond_ini, str):
            cond_ini = [cond_ini]

        return tp, cond_ini
    
    def _carregar_t_mean(self, **kwargs):

        """Carrega e processa o campo t apenas uma vez.""" 
        t = self.produto_config.open_model_file(**kwargs)
        cond_ini = get_inicializacao_fmt(t)

        if isinstance(cond_ini, str):
            cond_ini = [cond_ini]

        return t, cond_ini

    ###################################################################################################################

    def _processar_precipitacao(self, modo, tipo_plot='tp_db', N_dias=9, **kwargs):

        print(f'Processando precipitação no modo: {modo}')

        # try:

        if modo == '24h':

            self.tp, self.cond_ini = self._carregar_tp_mean(unico=True)

            for index, n in enumerate(self.tp['valid_time']):

                if len(self.cond_ini) > 0:
                    cond_ini = self.cond_ini[index]
                else:
                    cond_ini = self.cond_ini

                print(f'Processando {index}')

                tp_plot = self.tp.sel(valid_time=n)
                tempo_ini = pd.to_datetime(n.item()) - pd.Timedelta(days=1)
                tempo_fim = pd.to_datetime(n.item())

                titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo='PREC24HRS', cond_ini=cond_ini,
                        data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        sem_intervalo_semana=True, condicao_inicial='Data arquivo'
                    )

                plot_campos(
                    ds=tp_plot['tp'],
                    variavel_plotagem='chuva_ons',
                    title=titulo,
                    filename=f'mergegpm_rain_{tempo_fim.strftime("%Y%m%d")}',
                    path_to_save='/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/mergegpm/gpm_diario',
                    shapefiles=self.shapefiles,
                    **kwargs
                )

        elif modo == 'acumulado_mensal':

            from calendar import monthrange
            path_to_save = Constants().PATH_DOWNLOAD_ARQUIVOS_MERGE

            self.tp, self.cond_ini = self._carregar_tp_mean(apenas_mes_atual=True)
            self.tp = self.tp.sortby("valid_time")
            self.tp = self.tp.sel(valid_time=self.tp.valid_time <= self.data)
            print(self.tp)

            # if len(self.cond_ini) > 0:
            #     cond_ini = self.cond_ini[-1]

            # else:
            cond_ini = self.data.strftime('%d/%m/%Y')

            # Acumulando no mes
            tp_plot_acc = self.tp.resample(valid_time='1M').sum().isel(valid_time=0)

            tempo_ini = pd.to_datetime(self.tp['valid_time'].values[0]) - pd.Timedelta(days=1)
            tempo_fim = pd.to_datetime(self.tp['valid_time'].values[-1])

            # Abrindo a climatologia
            if self.modelo_fmt == 'mergegpm':
                path_clim = Constants().PATH_CLIMATOLOGIA_MERGE
                mes = pd.to_datetime(self.tp['valid_time'].values[0]).strftime('%b').lower()
                tp_plot_clim = xr.open_dataset(f'{path_clim}/MERGE_CPTEC_acum_{mes}.nc').isel(time=0)
                tp_plot_clim = tp_plot_clim.rename({'precacum': 'tp'})
            
            # Anomalia total
            tp_plot_anomalia_total = tp_plot_acc['tp'].values - tp_plot_clim['tp'].values 

            # Anomalia parcial
            dias_no_mes = monthrange(pd.to_datetime(self.tp['valid_time'][0].item()).year, pd.to_datetime(self.tp['valid_time'][0].item()).month)[1]
            tp_plot_anomalia_parcial = tp_plot_acc['tp'].values - (tp_plot_clim['tp'].values/dias_no_mes)*len(self.tp['valid_time'])

            # Porcentagem da anomalia
            tp_plot_anomalia_percentual = (tp_plot_acc['tp'].values / tp_plot_clim['tp'].values) * 100

            # Porcentagem da anomalia parcial
            tp_plot_anomalia_percentual_parcial = (tp_plot_acc['tp'].values / ((tp_plot_clim['tp'].values/dias_no_mes)*len(self.tp['valid_time']))) * 100

            # Criando um xarray para colocar as anomalias
            ds_total = xr.Dataset(
                {
                    "acumulado_ate": tp_plot_acc["tp"],
                    "anomalia_total": (("latitude", "longitude"), tp_plot_anomalia_total),
                    "anomalia_parcial": (("latitude", "longitude"), tp_plot_anomalia_parcial),
                    "pct_climatologia": (("latitude", "longitude"), tp_plot_anomalia_percentual),
                    "pct_climatologia_parcial": (("latitude", "longitude"), tp_plot_anomalia_percentual_parcial),
                }
            )
            
            for data_var in ds_total.data_vars:

                print(f'Processando {data_var}')

                if data_var == 'acumulado_ate':
                    tipo = 'Acumulado total'
                    variavel_plotagem = 'chuva_ons'

                elif data_var == 'anomalia_total':
                    tipo = 'Anomalia total'
                    variavel_plotagem = 'tp_anomalia'

                elif data_var == 'anomalia_parcial':
                    tipo = 'Anomalia parcial'
                    variavel_plotagem = 'tp_anomalia'

                elif data_var == 'pct_climatologia':
                    tipo = '% da climatologia'
                    variavel_plotagem = 'pct_climatologia'

                elif data_var == 'pct_climatologia_parcial':
                    tipo = '% da climatologia parcial'
                    variavel_plotagem = 'pct_climatologia'

                titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=tipo, cond_ini=cond_ini,
                        data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        sem_intervalo_semana=True, condicao_inicial='Data arquivo'
                )

                plot_campos(
                    ds=ds_total[data_var],
                    variavel_plotagem=variavel_plotagem,
                    title=titulo,
                    path_to_save='/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/mergegpm/gpm_clim',
                    filename=f'mergegpm_{data_var}_{tempo_fim.strftime("%Y%m%d")}_{tempo_fim.strftime("%b%Y")}', # mergegpm_acumulado_ate_20250827_Aug2025.png
                    shapefiles=self.shapefiles,
                    **kwargs
                )

        elif modo == 'dif_prev':

            self.tp, self.cond_ini = self._carregar_tp_mean(unico=True)

            # Dia atual 
            cond_ini = pd.to_datetime(self.cond_ini, format='%d/%m/%Y %H UTC')[0]

            # Dias para trás
            date_range = pd.date_range(end=cond_ini - pd.Timedelta(hours=36), periods=N_dias)

            for index, n_dia in enumerate(date_range[::-1]):

                dateprev = n_dia.strftime('%Y%m%d%H')

                for modelo_prev in ['gfs', 'ecmwf', 'ecmwf-ens', 'gefs', 'pconjunto-ons', 'ecmwf-aifs']:

                    try:

                        print(f'Abrindo arquivo de previsão: {modelo_prev} e {dateprev}')

                        if tipo_plot == 'tp_db':

                            tp_prev = get_prec_db(modelo_prev, n_dia.strftime('%Y-%m-%d'), str(n_dia.hour).zfill(2))
                            tp_prev['dt_prevista'] = pd.to_datetime(tp_prev['dt_prevista'])
                            tp_obs = get_prec_db(self.modelo_fmt, (cond_ini - pd.Timedelta(days=1)).strftime('%Y-%m-%d'))
                            tp_obs['dt_observado'] = pd.to_datetime(tp_obs['dt_observado']) + pd.Timedelta(days=1)
                            tp_prev = tp_prev[tp_prev['dt_prevista'] == tp_obs['dt_observado'].unique()[0]]
                            tp_prev = tp_prev.rename(columns={'dt_prevista': 'dt_observado'})
                            tp_prev = tp_prev[['dt_observado', 'vl_chuva', 'geometry']]
                            dif = tp_obs.merge(tp_prev, on='geometry')
                            dif['dif'] = dif['vl_chuva_y'] - dif['vl_chuva_x'] # previsao - observado

                            tempo_ini = tp_obs['dt_observado'].unique()[0] - pd.Timedelta(hours=12)
                            tempo_fim = tp_obs['dt_observado'].unique()[0] + pd.Timedelta(hours=12)

                            titulo = gerar_titulo(
                                modelo=f'{modelo_prev} - {self.modelo_fmt}',
                                tipo='Dif. de precipitação',
                                cond_ini=n_dia.strftime('%d/%m/%Y %H UTC'),
                                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                sem_intervalo_semana=True,
                                condicao_inicial=f'Prev {modelo_prev.replace("pconjunto", "pconj").upper()}'
                            )

                            plot_df_to_mapa(dif, 
                                            titulo=titulo, 
                                            shapefiles=self.shapefiles, 
                                            filename=f'dif_{modelo_prev}-gpm_{n_dia.strftime("%Y%m%d%H")}_f{cond_ini.strftime("%Y%m%d%H")}', 
                                            path_to_save='/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/dif_gpm',
                                            )

                        elif tipo_plot == 'tp_netcdf':

                            # Abrindo o arquivo de previsao
                            tp_prev = xr.open_dataset(f'{CONSTANTES["path_save_netcdf"]}/{modelo_prev}_tp_{dateprev}.nc')
                            tp_prev = resample_variavel(tp_prev, modelo_prev, 'tp', '24h').isel(tempo=index)
                            tp_prev = interpola_ds(tp_prev, self.tp)

                            # Calculando a diferença
                            dif = tp_prev['tp'] - self.tp['tp'].sel(valid_time=cond_ini)
                            
                            tempo_ini = dif.data_inicial - pd.Timedelta(hours=6)
                            tempo_fim = dif.data_final
                            tempo_ini = pd.to_datetime(tempo_ini.item())
                            tempo_fim = pd.to_datetime(tempo_fim.item())

                            titulo = gerar_titulo(
                                    modelo=f'{modelo_prev.upper()} - {self.modelo_fmt.upper()}', tipo='Dif. de precipitação', cond_ini=n_dia.strftime('%d/%m/%Y %H UTC'),
                                    data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                    data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                    sem_intervalo_semana=True, condicao_inicial=f'Prev {modelo_prev.upper()}'
                            )

                            plot_campos(
                                ds=dif,
                                variavel_plotagem='dif_prev',
                                title=titulo,
                                filename=f'dif_{modelo_prev}-{self.modelo_fmt}_{n_dia.strftime("%Y%m%d%H")}_f{cond_ini.strftime("%Y%m%d%H")}',
                                path_to_save='/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/dif_gpm',
                                shapefiles=self.shapefiles,
                                **kwargs
                            )

                    except Exception as e:
                        print(f'Erro ao processar {modelo_prev} - {n_dia}: {e}')

        elif modo == 'bacias_smap':

            from datetime import datetime
            API_URL = Constants().API_URL_APIV2

            # Vou usar para pegar as informações das subbacias
            df_ons = get_df_ons()

            # Abrindo o json arrumado
            shp = ajusta_shp_json()

            # Adicionando alguns pontos que não estão no arquivo
            novas_subbacias = CONSTANTES['novas_subbacias']
            shp = pd.concat([shp, pd.DataFrame(novas_subbacias)], ignore_index=True)

            # Abrindo arquivo
            self.tp, self.cond_ini = self._carregar_tp_mean(unico=True)

            chuva_media = []
            
            # Sem membros individuais
            for lat, lon, bacia, codigo in zip(shp['lat'], shp['lon'], shp['nome'], shp['cod']):
                chuva_media.append(calcula_media_bacia(self.tp, lat, lon, bacia, codigo, shp))

            # Concatenando os xarrays com a média nas bacias e transformando em um dataframe
            ds_to_df = xr.concat(chuva_media, dim='id').to_dataframe().reset_index()
            ds_to_df = ds_to_df.rename(columns={'id': 'cod_psat', 'time': 'dt_observado', 'tp': 'vl_chuva'})
            ds_to_df = ds_to_df.applymap(lambda x: 0 if isinstance(x, float) and x < 0 else x).round(2)
            dt_observado = pd.to_datetime(ds_to_df['dt_observado']) - pd.Timedelta(hours=36)
            dt_observado = list(set(dt_observado))[0]
            dt_observado = dt_observado.isoformat()
            ds_to_df = converter_psat_para_cd_subbacia(ds_to_df)
            ds_to_df = ds_to_df[['cd_subbacia', 'dt_observado', 'vl_chuva']]
            ds_to_df['dt_observado'] = dt_observado
            print(ds_to_df)

            salva_db = kwargs.get('salva_db', False)
    
            if salva_db:
                print('Salvando dados no db')
                response = requests.post(f'{API_URL}/rodadas/chuva/observada', verify=False, json=ds_to_df.to_dict('records'), headers=get_auth_header())
                print(f'Código POST: {response.status_code}')

        # except Exception as e:
        #    print(f'Erro ao processar {modo}: {e}')

    def _processar_temperatura(self, modo, **kwargs):

        try:

            if modo == 'temp_diario':

                self.tmax, self.cond_ini = self._carregar_t_mean(unico=True, variavel='tmax')
                self.tmin, self.cond_ini = self._carregar_t_mean(unico=True, variavel='tmin')
                self.tmed, self.cond_ini = self._carregar_t_mean(unico=True, variavel='tmed')

                # Climatologia para a anomalia
                mes = pd.to_datetime(self.tmax.time.values[0]).strftime('%m')
                ds_clim_tmin = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmin/SAMeT_CPTEC_TMIN_mean_{mes}.nc', decode_times=False).isel(time=0)
                ds_clim_tmax = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmax/SAMeT_CPTEC_TMAX_mean_{mes}.nc', decode_times=False).isel(time=0)
                ds_clim_tmed = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmed/SAMeT_CPTEC_TMED_mean_{mes}.nc', decode_times=False).isel(time=0)

                ds_clim_tmin = ajusta_lon_0_360(ds_clim_tmin.rename({'lon': 'longitude', 'lat': 'latitude'}))
                ds_clim_tmax = ajusta_lon_0_360(ds_clim_tmax.rename({'lon': 'longitude', 'lat': 'latitude'}))
                ds_clim_tmed = ajusta_lon_0_360(ds_clim_tmed.rename({'lon': 'longitude', 'lat': 'latitude'}))

                # Calculando a anomalia
                anomalia_tmin = self.tmin['tmin'] - ds_clim_tmin['tmin']
                anomalia_tmax = self.tmax['tmax'] - ds_clim_tmax['tmax']
                anomalia_tmed = self.tmed['tmed'] - ds_clim_tmed['tmed']

                # Juntando todos 
                ds_temp = xr.merge([self.tmax.drop_vars('nobs'), self.tmin.drop_vars('nobs'), self.tmed.drop_vars('nobs'), anomalia_tmin.to_dataset().rename({'tmin': 'anomalia_tmin'}), anomalia_tmax.to_dataset().rename({'tmax': 'anomalia_tmax'}), anomalia_tmed.to_dataset().rename({'tmed': 'anomalia_tmed'})])

                for index, valid_time in enumerate(ds_temp['valid_time']):

                    if len(self.cond_ini) > 0:
                        cond_ini = self.cond_ini[index]
                    else:
                        cond_ini = self.cond_ini

                    for data_var in ds_temp.data_vars:
                        
                        titulo = gerar_titulo(
                                modelo=self.modelo_fmt, tipo=f'Temperatura SaMET {data_var.upper()}', cond_ini=cond_ini,
                                data_ini=pd.to_datetime(valid_time.item()).strftime('%d/%m/%Y').replace(' ', '\\ '),
                                unico_tempo=True, condicao_inicial='Data arquivo'
                            )

                        plot_campos(
                            ds=ds_temp.sel(valid_time=valid_time)[data_var],
                            variavel_plotagem='temp850' if 'anomalia' not in data_var else 'temp_anomalia',
                            title=titulo,
                            filename=f'{data_var}_{self.modelo_fmt}_{pd.to_datetime(valid_time.item()).strftime("%Y%m%d")}',
                            shapefiles=self.shapefiles,
                            plot_bacias=False,
                            path_to_save=f'{Constants().PATH_SAVE_FIGS_METEOROLOGIA}/figs_samet',
                            **kwargs
                        )

            elif modo == 'temp_mensal':

                self.tmax, self.cond_ini = self._carregar_t_mean(apenas_mes_atual=True, variavel='tmax')
                self.tmin, self.cond_ini = self._carregar_t_mean(apenas_mes_atual=True, variavel='tmin')
                self.tmed, self.cond_ini = self._carregar_t_mean(apenas_mes_atual=True, variavel='tmed')

                # Gerar um csv mensal
                target_lon, target_lat, pontos = get_pontos_localidades()
                t2max_no_ponto = self.tmax['tmax'].sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe().reset_index('valid_time').dropna()
                t2min_no_ponto = self.tmin['tmin'].sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe().reset_index('valid_time').dropna()
                t2med_no_ponto = self.tmed['tmed'].sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe().reset_index('valid_time').dropna()

                # Ajustando os labels
                t2max_no_ponto = t2max_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                t2min_no_ponto = t2min_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                t2med_no_ponto = t2med_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'})

                print(f'gerando csv...')
                os.makedirs(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files', exist_ok=True)
                YEAR = pd.to_datetime(self.tmax.time.values[0]).strftime('%Y')
                MONTH = pd.to_datetime(self.tmax.time.values[0]).strftime('%m')
                t2med_no_ponto.to_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMED_{YEAR}{MONTH}.csv')
                t2max_no_ponto.to_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMAX_{YEAR}{MONTH}.csv')
                t2min_no_ponto.to_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMIN_{YEAR}{MONTH}.csv')

                # Climatologia para a anomalia
                mes = pd.to_datetime(self.tmax.time.values[0]).strftime('%m')
                ds_clim_tmin = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmin/SAMeT_CPTEC_TMIN_mean_{mes}.nc', decode_times=False).isel(time=0)
                ds_clim_tmax = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmax/SAMeT_CPTEC_TMAX_mean_{mes}.nc', decode_times=False).isel(time=0)
                ds_clim_tmed = xr.open_dataset(f'{Constants().PATH_CLIMATOLOGIA_SAMET}/tmed/SAMeT_CPTEC_TMED_mean_{mes}.nc', decode_times=False).isel(time=0)

                ds_clim_tmin = ajusta_lon_0_360(ds_clim_tmin.rename({'lon': 'longitude', 'lat': 'latitude'}))
                ds_clim_tmax = ajusta_lon_0_360(ds_clim_tmax.rename({'lon': 'longitude', 'lat': 'latitude'}))
                ds_clim_tmed = ajusta_lon_0_360(ds_clim_tmed.rename({'lon': 'longitude', 'lat': 'latitude'}))            

                # Calculando a anomalia
                anomalia_tmin = self.tmin['tmin'].resample(time='1M').mean().isel(time=0) - ds_clim_tmin['tmin']
                anomalia_tmax = self.tmax['tmax'].resample(time='1M').mean().isel(time=0) - ds_clim_tmax['tmax']
                anomalia_tmed = self.tmed['tmed'].resample(time='1M').mean().isel(time=0) - ds_clim_tmed['tmed']

                # Juntando todos 
                ds_temp = xr.merge([self.tmin['tmin'].resample(time='1M').mean().isel(time=0), self.tmed['tmed'].resample(time='1M').mean().isel(time=0), self.tmax['tmax'].resample(time='1M').mean().isel(time=0), anomalia_tmin.to_dataset().rename({'tmin': 'anomalia_tmin'}), anomalia_tmax.to_dataset().rename({'tmax': 'anomalia_tmax'}), anomalia_tmed.to_dataset().rename({'tmed': 'anomalia_tmed'})])

                tempo_ini = pd.to_datetime(self.cond_ini[0], format='%d/%m/%Y %H UTC')
                tempo_fim = pd.to_datetime(self.cond_ini[-1], format='%d/%m/%Y %H UTC')

                for data_var in ds_temp.data_vars:

                    titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo={data_var.upper()}, cond_ini=self.cond_ini[-1],
                            data_ini=tempo_ini.strftime('%d/%m/%Y').replace(' ', '\\ '),
                            data_fim=tempo_fim.strftime('%d/%m/%Y').replace(' ', '\\ '),
                            sem_intervalo_semana=True, condicao_inicial='Data arquivo'
                    )

                    plot_campos(
                        ds=ds_temp[data_var],
                        variavel_plotagem='temp850' if 'anomalia' not in data_var else 'temp_anomalia',
                        title=titulo,
                        filename=f'{tempo_fim.strftime("%Y%m%d")}_bruto{data_var}' if 'anomalia' not in data_var else f'{tempo_fim.strftime("%Y%m%d")}_anomalia{data_var}',
                        shapefiles=self.shapefiles,
                        plot_bacias=False,
                        **kwargs
                    )

            elif modo == 'gerar_txt_cidades':

                self.tmax, self.cond_ini = self._carregar_t_mean(ultimos_n_dias=True, variavel='tmax', ajusta_nome=False)
                self.tmin, self.cond_ini = self._carregar_t_mean(ultimos_n_dias=True, variavel='tmin', ajusta_nome=False)
                self.tmed, self.cond_ini = self._carregar_t_mean(ultimos_n_dias=True, variavel='tmed', ajusta_nome=False)
                ds_temp = xr.merge([self.tmax.drop_vars('nobs'), self.tmin.drop_vars('nobs'), self.tmed.drop_vars('nobs')])

                # Coordenadas que vamos extrair os pontos
                target_lon, target_lat, pontos = get_pontos_localidades()

                # Criando o diretorio que vou salvar
                os.makedirs(f'{Constants().PATH_TO_SAVE_TXT_SAMET}', exist_ok=True)

                for varname in ds_temp.data_vars:

                    for id in pontos['id']:

                        ds_no_ponto = ds_temp[varname].sel(lat=target_lat, lon=target_lon, method='nearest').to_dataframe().reset_index().round(2)
                        ds_no_ponto = ds_no_ponto[ds_no_ponto['id'] == id]
                        temp_type = ds_no_ponto.columns[-1] # pega o nome da coluna de temperatura
                        ds_no_ponto = ds_no_ponto[['time','lon', 'lat', temp_type]]
                        ds_no_ponto['type'] = temp_type
                        ds_no_ponto.to_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/{id}_{temp_type}.txt', header=False, sep=' ', index=False)

        except Exception as e:
            print(f"Erro ao gerar modo: {e}")  

    ###################################################################################################################

    def gerar_prec24h(self, **kwargs):
        self._processar_precipitacao('24h', **kwargs)

    def gerar_acumulado_mensal(self, **kwargs):
        self._processar_precipitacao('acumulado_mensal', **kwargs)

    def gerar_dif_prev(self, **kwargs):
        self._processar_precipitacao('dif_prev', **kwargs)

    def gerar_bacias_smap(self, **kwargs):
        self._processar_precipitacao('bacias_smap', **kwargs)

    def gerar_temp_diario(self, **kwargs):
        self._processar_temperatura('temp_diario', **kwargs)

    def gerar_temp_mensal(self, **kwargs):
        self._processar_temperatura('temp_mensal', **kwargs)

    def gerar_txt_cidades(self, **kwargs):
        self._processar_temperatura('gerar_txt_cidades', **kwargs)

###################################################################################################################
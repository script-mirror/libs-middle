from datetime import datetime
import requests
import os
import time
import pdb
import pandas as pd
import numpy as np
from functools import lru_cache
import matplotlib
matplotlib.use('Agg')  # Backend para geração de imagens, sem interface gráfica
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
# import scipy.ndimage as nd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap
from .utils import abrir_modelo_sem_vazios
from .plots import gerar_prec24h, gerar_acumulado_total, gerar_semanas_operativas, gerar_prec24hr_pnmm, gerar_jato_div200, gerar_geop_500, gerar_geop_vorticidade_500, gerar_vento_temp850, gerar_vento850, gerar_chuva_geop500_vento850, gerar_ivt

###################################################################################################################

# Tipos de variaveis
surface = ['tp', 'u10', 'v10', 'prec']  # Variáveis em superfície
height_above_ground = ['t2m', '2t']  # Variáveis a 2 metros
isobaric_inhPa = ['u', 'v', 'z', 'gh', 't', 'q']  # Variáveis isobáricas
mean_sea = ['pnmm', 'msl', 'prmsl']  # mean sea level pressure
nominalTop = ['ttr', 'sulwrf']  # Variáveis no topo nominal

###################################################################################################################

shapefiles = ['C:/Temp/shapefiles/Bacias_Hidrograficas_SIN.shp', 'C:/Temp/shapefiles/estados_2010.shp']

###################################################################################################################

# Dicionario de labels e variaveis
labels_variaveis = {
    '[mm]': ['tp', 'chuva_ons', 'prec', 'acumulado_total', 'wind_prec_geop'],
    '[m/s]': ['wind200'],
    '[dam]': ['geop_500'],
    '[1/s]': ['vorticidade', 'divergencia', 'divergencia850'],
    '[°C]': ['temp850', 't2m', '2t'],
    '[kg*m-1*s-1]': ['ivt']
}

###################################################################################################################

class Produtos:

    def __init__(self, modelo, inicializacao=0, resolucao='0p25', data=datetime.now(), output_path='./tmp/downloads', days_time_delta=None, shapefiles=None, name_prefix=None):

        import geopandas as gpd

        self.modelo = modelo
        self.inicializacao = inicializacao
        self.resolucao = resolucao
        self.output_path = output_path
        self.shapefiles = {fp: gpd.read_file(fp) for fp in shapefiles} if shapefiles else {}
        self.name_prefix = name_prefix

        if days_time_delta:
            self.data = data - pd.Timedelta(days=days_time_delta)
        else:
            self.data = data

    # --- DOWNLOAD ---
    def download_files_models(self, variables: str | list, levels=None, steps=[i for i in range(0, 390, 6)], provedor_ecmwf_opendata='ecmwf',
                               model_ecmwf_opendata='ifs', file_size=1000, stream_ecmwf_opendata='oper', wait_members=False, last_member_file=None,
                               type_ecmwf_opendata='fc', levtype_ecmwf_opendata='sfc', levlist_ecmwf_opendata=None, sub_region_as_gribfilter=False) -> None:

        # Formatação da data e inicialização
        data_fmt = self.data.strftime('%Y%m%d')
        inicializacao_fmt = str(self.inicializacao).zfill(2)
        resolucao = self.resolucao
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

        print(f'************* INICIANDO DONWLOAD {data_fmt}{inicializacao_fmt} para o modelo {modelo_fmt.upper()} *************\n')

        # Diretório para salvar os arquivos
        caminho_para_salvar = f'{output_path}/{modelo_fmt}{resolucao}/{data_fmt}{inicializacao_fmt}'

        if wait_members:
            tamanho_min_bytes = 45 * 1024 * 1024  # 45 MB

            while True:
                caminho_arquivo = f'{caminho_para_salvar}/{last_member_file}'
                if os.path.exists(caminho_arquivo):
                    tamanho = os.path.getsize(caminho_arquivo)
                    if tamanho >= tamanho_min_bytes:
                        break  # Arquivo existe e tem tamanho adequado
                    else:
                        print(f'O arquivo {last_member_file} existe, mas ainda está com {tamanho} bytes (aguardando {tamanho_min_bytes} bytes)...')
                else:
                    print(f'Aguardando arquivo {last_member_file} de membros do modelo {modelo_fmt} serem baixados...')

                time.sleep(10)

        os.makedirs(caminho_para_salvar, exist_ok=True)
        print(f'Salvando no diretório: {caminho_para_salvar}')

        if modelo_fmt == 'gfs':
            prefix_url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{resolucao}.pl?dir=%2F'
            prefixo_pgrb2 = 'pgrb2' if resolucao == '0p25' or resolucao == '1p00' else 'pgrb2full'
            prefix_modelo = f'gfs.{data_fmt}%2F{inicializacao_fmt}%2Fatmos&file=gfs.t{inicializacao_fmt}z.{prefixo_pgrb2}.{resolucao}.f'

        elif modelo_fmt == 'gefs':
            prefix_url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_{resolucao}a.pl?dir=%2F'
            prefix_modelo = f'gefs.{data_fmt}%2F{inicializacao_fmt}%2Fatmos%2Fpgrb2ap5&file=geavg.t{inicializacao_fmt}z.pgrb2a.{resolucao}.f'

        # Baixando os arquivos
        if modelo_fmt in ['gfs', 'gefs']:

            while True:
                todos_sucesso = True  # Flag para sair do while quando todos forem baixados corretamente

                for i in steps:
                    filename = f'{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2' if self.name_prefix else f'{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                    caminho_arquivo = f'{caminho_para_salvar}/{filename}'

                    # Se o arquivo já existe e está com tamanho esperado, pula
                    if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) >= file_size:
                        print(f'Arquivo {filename} já existe e está OK, pulando download...')
                        continue

                    url = f'{prefix_url}{prefix_modelo}{i:03d}{variables}{levels}'

                    if sub_region_as_gribfilter:
                        url += sub_region_as_gribfilter

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

        elif 'ecmwf' in modelo_fmt:

            from ecmwf.opendata import Client
            client = Client(provedor_ecmwf_opendata, model=model_ecmwf_opendata, resol=resolucao) 

            while True:
                todos_sucesso = True  # Flag para checar se todos os steps deram certo

                for step in steps:

                    caminho_arquivo = f'{caminho_para_salvar}/{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{str(step).zfill(3)}.grib2'

                    if self.name_prefix:
                        caminho_arquivo = f'{caminho_para_salvar}/{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{str(step).zfill(3)}.grib2'

                    print(f'Baixando... {caminho_arquivo}')

                    if os.path.exists(caminho_arquivo):
                        print(f'Arquivo {caminho_arquivo} já existe, pulando download...')
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
                        print(f'Erro ao baixar ECMWF: {e}, tentando novamente...')
                        todos_sucesso = False
                        time.sleep(5)
                        break  # Sai do for e tenta novamente o while

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
    def open_model_file(self, variavel: str, sel_area=False, ensemble_mean=False, cf_pf_members=False, arquivos_membros_diferentes=False, ajusta_acumulado=False, m_to_mm=False, ajusta_longitude=True):

        print(f'************* ABRINDO DADOS {variavel} DO MODELO {self.modelo.upper()} *************\n')
        
        import xarray as xr

        # Formatação da data e inicialização
        data_fmt = self.data.strftime('%Y%m%d')
        inicializacao_fmt = str(self.inicializacao).zfill(2)
        resolucao = self.resolucao
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

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
                files = files[1:] # Remove o primeiro arquivo
                
            else:
                raise ValueError(f'Variável {variavel} não reconhecida ou não implementada para ensemble model.')

            # Abrindo o arquivo com xarray
            pf = abrir_modelo_sem_vazios(files, backend_kwargs=backend_kwargs_pf)
            cf = abrir_modelo_sem_vazios(files, backend_kwargs=backend_kwargs_cf)

            # pf = xr.open_mfdataset(files, engine='cfgrib', 
            #                     backend_kwargs=backend_kwargs_pf,
            #                     combine='nested', concat_dim='step', decode_timedelta=True)

            # cf = xr.open_mfdataset(files, engine='cfgrib', 
            #                     backend_kwargs=backend_kwargs_cf,
            #                     combine='nested', concat_dim='step', decode_timedelta=True)

            ds = xr.concat([cf, pf], dim='number')            

        else:

            if variavel in surface:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'surface'}, "indexpath": ""}
            
            elif variavel in height_above_ground:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'heightAboveGround'}, "indexpath": ""}

            elif variavel in isobaric_inhPa:  # variaveis isobaricas
                backend_kwargs = {"filter_by_keys": {'cfVarName': variavel, 'typeOfLevel': 'isobaricInhPa'}, "indexpath": ""}

            elif variavel in mean_sea:  # pressao ao nivel do mar
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'meanSea'}, "indexpath": ""}

            elif variavel in nominalTop:
                backend_kwargs = {"filter_by_keys": {'shortName': variavel, 'typeOfLevel': 'nominalTop'}, "indexpath": ""}
                # files = files[1:] # Remove o primeiro arquivo

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

                # datasets = []
                # for f in files:
                #     try:
                #         ds = xr.open_dataset(f, engine='cfgrib', backend_kwargs=backend_kwargs, decode_timedelta=True)
                #         if ds.variables:  # verifica se tem variáveis (não está vazio)
                #             datasets.append(ds)
                #     except Exception as e:
                #         print(f'Ignorando {f}: {e}')

                # ds = xr.concat(datasets, dim='valid_time')
                
                # Abrindo o arquivo com xarray
                # ds = xr.open_mfdataset(files, engine='cfgrib', backend_kwargs=backend_kwargs, combine='nested', concat_dim='valid_time', decode_timedelta=True)
        
        # Renomeando lat para latitude e lon para longitude
        if 'lat' in ds.dims:
            ds = ds.rename({'lat': 'latitude'})

        if 'lon' in ds.dims:
            ds = ds.rename({'lon': 'longitude'})

        # Se step estiver nas dimensions, renomeia para valid_time
        if 'step' in ds.dims:
            ds = ds.swap_dims({'step': 'valid_time'})

        # Ajustando a longitude para 0 a 360
        if 'longitude' in ds.dims and ajusta_longitude:
            ds['longitude'] = (ds['longitude'] + 360) % 360

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

            variaveis_com_valid_time = [v for v in ds.data_vars if 'valid_time' in ds[v].dims]

            ds_diff = xr.Dataset()

            for var in variaveis_com_valid_time:
                primeiro = ds[var].isel(valid_time=0)
                dif = ds[var].diff(dim='valid_time')
                dif_completo = xr.concat([primeiro, dif], dim='valid_time')
                ds_diff[var] = dif_completo

            ds_diff['valid_time'] = ds['valid_time']
            ds = ds_diff

        # Ajusta a unidade de medida
        if m_to_mm and variavel == 'tp':
            # Converte de metros para milímetros
            ds['tp'] = ds['tp'] * 1000

        return ds

    # --- BASE DO MAPA ---
    # @lru_cache(maxsize=8)
    def get_base_ax(self, extent, figsize, central_longitude=0):

        import cartopy.feature as cfeature

        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=central_longitude))
        ax.set_extent(list(extent), crs=ccrs.PlateCarree())

        ax.coastlines(resolution='110m', color='black')
        ax.add_feature(cfeature.BORDERS, edgecolor='black')

        # Labels dos ticks de lat e lon
        gl = ax.gridlines(draw_labels=True, alpha=0.2, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False

        return fig, ax

    # --- COLOR BARS ---
    def custom_colorbar(self, variavel_plotagem):

        if variavel_plotagem in ['chuva_ons', 'tp', 'chuva_pnmm']:
            levels = [0, 1 ,5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
            colors = ['#ffffff', '#e1ffff', '#b3f0fb','#95d2f9','#2585f0','#0c68ce','#73fd8b','#39d52b','#3ba933','#ffe67b','#ffbd4a','#fd5c22','#b91d22','#f7596f','#a9a9a9']
            cmap = None

        elif variavel_plotagem == 'acumulado_total':
            levels = range(0, 420, 20)
            colors = [
                '#FFFFFF',
                '#B1EDCF',
                '#97D8B7',
                '#7DC19E',
                '#62AA85',
                '#48936D',
                '#2E7E54',
                '#14673C',
                '#14678C',
                '#337E9F',
                '#5094B5',
                '#6DACC8',
                '#8BC4DE',
                '#A9DBF2',
                '#EBD5EB',
                '#D9BED8',
                '#C5A7C5',
                '#B38FB2',
                '#A0779F',
                '#8E5F8D',
                '#682F67',
                '#6C0033',
                '#631C2A',
                '#A54945',
                '#C16E4E',
                '#DE9357',
                '#FAC66C',
                '#FBD479',
                '#FDE385',
                '#FEF192',
                '#FFFF9F',
            ]
            cmap = None

        elif variavel_plotagem == 'wind200':
            colors = ['#FFFFFF','#FFFFC1','#EBFF51','#ACFE53','#5AFD5B','#54FCD2','#54DBF5','#54ACFC', '#4364FC','#2F29ED','#3304BC','#440499']
            levels = np.arange(40, 85, 2)
            custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
            cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)

        elif variavel_plotagem == 'geop_500':
            levels = range(450, 605, 5)
            colors = ['#303030', '#585858', '#7A7A7A', '#C9E2F6', '#C6DAF3', '#A0B4CC', '#6A7384', '#E0DCFF',
                    '#C6BBFF', '#836FEC', '#7467D1', '#4230C0', '#3020A5', '#2877ED', '#2D88F1', '#3897F3',
                    '#6CA0D0', '#5EA4EC', '#A1DFDE', '#C1EDBC', '#9EFA95', '#7DE17F', '#24A727', '#069F09',
                    '#FAF6AF', '#F5DD6F', '#E8C96E', '#FBA103', '#E9610D', '#EB3D18', '#DF1507', '#BC0005',
                    '#A50102', '#614338', '#75524C', '#806762', '#886760', '#917571', '#AE867E', '#C3A09A',
                    '#E0C5BE', '#DFABAD', '#E26863', '#C83A36', '#8F1E1A', '#6A0606']
            custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
            cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 

        elif variavel_plotagem == 'vorticidade':
            levels = range(-100, 110, 10)
            colors = None
            cmap = plt.get_cmap('RdBu_r', len(levels)  + 1)

        elif variavel_plotagem == 'temp850':
            levels = np.arange(-14, 34, 1)
            colors = ['#8E27BA','#432A98','#1953A8','#148BC1','#15B3A4', '#16C597','#77DE75','#C5DD47','#F5BB1A','#F0933A','#EF753D',
            '#F23B39', '#C41111', '#8D0A0A']
            custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
            cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)

        elif variavel_plotagem == 'divergencia850':
            levels = np.arange(-5, 6, 1)
            colors = None
            cmap = plt.get_cmap('RdBu_r', len(levels)  + 1)

        elif variavel_plotagem == 'ivt':
            colors = ['white', 'yellow', 'orange', 'red', 'gray']
            levels = np.arange(250, 1650, 50)
            custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
            cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 

        elif variavel_plotagem == 'wind_prec_geop':
            levels = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 35]
            colors = ["#ffffff", '#00004C', '#003862',
                    '#001D7E', '#004C98', '#0066AD', 
                    '#009BDB', '#77BAE8', '#9ED7FF',
                    '#F6E5BD', '#F1E3A0', '#F3D98B',
                    '#F5C96C', '#EFB73F', '#EA7B32',
                    '#D75C12', '#BF0411']
            cmap = None

        return levels, colors, cmap

    # --- PLOT DE VARIÁVEIS ---
    def plot_campos(self, 
                    ds, 
                    # variavel, 
                    variavel_plotagem, 
                    filename, 
                    title, 
                    extent=[240, 360, -60, 20], 
                    figsize=(12, 12), 
                    central_longitude=0, 
                    loc_title='left', 
                    title_fontsize=16, 
                    posicao_colorbar='horizontal',
                    path_to_save='./tmp/plots',
                    ds_contour=None,
                    variavel_contour=None,
                    ds_streamplot=None,
                    variavel_streamplot=None,
                    ds_quiver=None,
                    variavel_quiver=None,
                    plot_bacias=True,
                    color_contour='white'
    ):

        os.makedirs(path_to_save, exist_ok=True)

        extent = tuple(extent)
        figsize = tuple(figsize)
        fig, ax = self.get_base_ax(extent=extent, figsize=figsize, central_longitude=central_longitude)
        levels, colors, cmap = self.custom_colorbar(variavel_plotagem)

        # Se colors e cmap nao forem None, seta levels para None
        if colors is not None and cmap is not None:
            colors = None
        
        lon, lat = np.meshgrid(ds['longitude'], ds['latitude'])
        cf = ax.contourf(lon, lat, ds, transform=ccrs.PlateCarree(), transform_first=True, origin='upper', levels=levels, colors=colors, extend='both', cmap=cmap)

        if ds_contour is not None:

            if variavel_contour == 'pnmm':
                red_levels = np.arange(970, 1020, 5)
                cf2 = ax.contour(lon, lat, ds_contour, levels=red_levels, colors='red', linestyles='solid', linewidths=1.5, transform=ccrs.PlateCarree(), transform_first=True)
                plt.clabel(cf2, inline=True, fmt='%.0f', fontsize=15, colors='red')

                blue_levels = np.arange(1020, 1035, 5)
                cf2 = ax.contour(lon, lat, ds_contour, levels=blue_levels, colors='blue', linestyles='solid', linewidths=1.5, transform=ccrs.PlateCarree(), transform_first=True)
                plt.clabel(cf2, inline=True, fmt='%.0f', fontsize=15, colors='blue')

            elif variavel_contour == 'gh_500':
                cf2 = ax.contour(lon, lat, ds_contour, transform=ccrs.PlateCarree(), colors='black', linestyles='solid', levels=np.arange(500, 605, 5))
                plt.clabel(cf2, inline=True, fmt='%.0f', fontsize=10, colors=color_contour)

            elif variavel_contour == 'gh_700':
                cf2 = ax.contour(lon, lat, ds_contour, transform=ccrs.PlateCarree(), colors='black', linestyles='solid', levels=np.arange(286, 324, 4))
                plt.clabel(cf2, inline=True, fmt='%.0f', fontsize=10, colors=color_contour)

        if ds_streamplot is not None:

            if variavel_streamplot == 'wind200':
                u = ds_streamplot['u']
                v = ds_streamplot['v']
                div = ds_streamplot['divergencia']
                ax.streamplot(lon, lat, u.data, v.data, linewidth=1.5, arrowsize=1, density=2.5, color='black')
                ax.contourf(lon, lat, div, np.arange(2, 15.5, 0.5), colors='#F00082', alpha=0.5)

            elif variavel_streamplot == 'wind850':
                u = ds_streamplot['u']
                v = ds_streamplot['v']
                # div = ds_streamplot['divergencia']
                ax.streamplot(lon, lat, u.data, v.data, linewidth=1.5, arrowsize=1, density=2.5, color='black')
                #ax.contourf(lon, lat, div, np.arange(-15.5, -2, 0.5), colors='#F00082', alpha=0.5)

        if ds_quiver is not None:

            if variavel_quiver == 'wind850':

                u = ds_quiver['u']
                v = ds_quiver['v']
                N_interp = 2.5

                u_interp=u.interp(
                    longitude=np.arange(u.longitude.min().values,u.longitude.max().values, N_interp),
                    latitude=np.arange(u.latitude.min().values,u.latitude.max().values, N_interp))

                v_interp=v.interp(
                    longitude=np.arange(v.longitude.min().values,v.longitude.max().values, N_interp),
                    latitude=np.arange(v.latitude.min().values,v.latitude.max().values, N_interp))


                quiver_kwargs= {'headlength': 4, 'headwidth': 3,'angles': 'uv', 'scale':400}
                qp = ax.quiver(u_interp.longitude, u_interp.latitude, u_interp, v_interp, pivot='mid', transform=ccrs.PlateCarree(), zorder=5, **quiver_kwargs)

            elif variavel_quiver == 'ivt':

                u = ds_quiver['qu']
                v = ds_quiver['qv']

                quiver_kwargs= {'headlength': 4, 'headwidth': 3,'angles': 'uv', 'scale':300}
                qp = ax.quiver(u.longitude, u.latitude, u, v, pivot='mid', transform=ccrs.PlateCarree(), zorder=5, **quiver_kwargs)

        ax.set_title(title, loc=loc_title, fontsize=title_fontsize)

        # Barra de cor
        label = [k for k, v in labels_variaveis.items() if variavel_plotagem in v]
        if label:
            label = label[0]

        if posicao_colorbar == 'vertical':
            axins = inset_axes(ax, width="3%", height="100%", loc='right', borderpad=-2.7)
            fig.colorbar(cf, cax=axins, orientation='vertical', label=label, ticks=levels, extendrect=True)

        elif posicao_colorbar == 'horizontal':
            axins = inset_axes(ax, width="95%", height="2%", loc='lower center', borderpad=-3.6)
            fig.colorbar(cf, cax=axins, orientation='horizontal', ticks=levels if len(levels)<=26 else levels[::2], extendrect=True, label=label)

        if self.shapefiles is not None:
            for gdf in self.shapefiles.values():
                if 'Nome_Bacia' in gdf.columns:
                    if plot_bacias:
                        gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)
                else:
                    gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)

        plt.savefig(f'{path_to_save}/{filename}.png', bbox_inches='tight')
        plt.close(fig)

###################################################################################################################

# Contando o tempo de execução
start_time = time.time()

###################################################################################################################

# Datas e parâmetros
modelo = 'ecmwf-ens'
membros = True
inicializacao = 0
data = datetime.now() - pd.Timedelta(days=2)  # Data de ontem
modelo_fmt = modelo.lower()

###################################################################################################################

# Baixando e abrindo os dados
if modelo == 'ecmwf':

    download_params_sfc = {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp', 'msl', '2t', 'ttr'],
    }

    download_params_pl = {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh', 'u', 'v', 't', 'q'],
        'levlist_ecmwf_opendata': [1000, 925, 850, 700, 600, 500, 400, 300, 200]
    }

    tp_params = {
        'ajusta_acumulado': True,
        'm_to_mm': True,
    }

    produto_config = Produtos(modelo, resolucao='0p25', name_prefix='sfc', data=data, inicializacao=inicializacao, shapefiles=shapefiles)
    produto_config.download_files_models(**download_params_sfc)

    produto_config_pl = Produtos(modelo, resolucao='0p25', name_prefix='pl', data=data, inicializacao=inicializacao, shapefiles=shapefiles)
    produto_config_pl.download_files_models(**download_params_pl)

elif modelo == 'ecmwf-ens':

    download_params_sfc = {
        'type_ecmwf_opendata': ['cf', 'pf'],
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp'],
    }

    if membros == True: # Nao baixa pq vou triggar em paralelo para baixar
        download_params_sfc['wait_members'] = True  # Espera os membros serem baixados
        download_params_sfc['last_member_file'] = f'sfc_ecmwf-ens_{data.strftime("%Y%m%d")}{str(inicializacao).zfill(2)}_360.grib2'  # Nome do último arquivo de membro para verificar se todos foram baixados

    download_params_enfo = {
        'type_ecmwf_opendata': 'em',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh'],
    }  

    tp_params = {
        'ajusta_acumulado': True,
        'm_to_mm': True,
        'cf_pf_members': True,
    }

    produto_config = Produtos(modelo, resolucao='0p25', name_prefix='sfc', data=data, inicializacao=inicializacao)
    produto_config.download_files_models(**download_params_sfc)

    if membros == False:
        produto_config_enfo = Produtos(modelo, resolucao='0p25', name_prefix='enfo', data=data, inicializacao=inicializacao)
        produto_config_enfo.download_files_models(**download_params_enfo)

elif modelo == 'gfs':

    download_params = {
        'variables': '&var_ULWRF=on&var_APCP=on&var_HGT=on&var_PRMSL=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_SPFH=on',
        'levels': '&lev_top_of_atmosphere=on&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on&lev_900_mb=on&lev_875_mb=on&lev_850_mb=on&lev_825_mb=on&lev_800_mb=on&lev_775_mb=on&lev_750_mb=on&lev_725_mb=on&lev_700_mb=on&lev_675_mb=on&lev_650_mb=on&lev_625_mb=on&lev_600_mb=on&lev_575_mb=on&lev_550_mb=on&lev_525_mb=on&lev_500_mb=on&lev_475_mb=on&lev_450_mb=on&lev_425_mb=on&lev_400_mb=on&lev_375_mb=on&lev_350_mb=on&lev_325_mb=on&lev_300_mb=on&lev_200_mb=on&lev_surface=on&lev_mean_sea_level=on&lev_2_m_above_ground=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',
    }

    tp_params = {}

    produto_config = Produtos(modelo, resolucao='0p50', data=data, inicializacao=inicializacao, shapefiles=shapefiles)
    produto_config.download_files_models(**download_params)

elif modelo == 'gefs':

    download_params = {
        'variables': '&var_ULWRF=on&var_APCP=on&var_HGT=on&var_PRMSL=on&var_TMP=on&var_UGRD=on&var_VGRD=on',
        'levels': '&lev_top_of_atmosphere=on&lev_200_mb=on&lev_925_mb=on&lev_500_mb=on&lev_850_mb=on&lev_surface=on&lev_mean_sea_level=on&lev_2_m_above_ground=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',
    }

    tp_params = {}

    produto_config = Produtos(modelo, resolucao='0p50', data=data, inicializacao=inicializacao)
    produto_config.download_files_models(**download_params)

elif modelo == 'gefs-membros':

    download_params = {
        'variables': '&var_APCP=on',
        'levels': '&lev_surface=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',
        'file_size': 0,  # Tamanho mínimo do arquivo para considerar que o download foi bem-sucedido
    }

    tp_params = {
        'arquivos_membros_diferentes': True,
    }

    produto_config = Produtos(modelo, resolucao='0p50', data=data, inicializacao=inicializacao)
    produto_config.download_files_models(**download_params)

elif modelo == 'ecmwf-aifs':

    model_name = 'aifs-single'

    download_params_sfc = {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp'],
        'model_ecmwf_opendata': model_name,
    }

    tp_params = {
        'ajusta_acumulado': True,
    }

    produto_config = Produtos(modelo, resolucao='0p25', name_prefix='sfc', data=data, inicializacao=inicializacao)
    produto_config.download_files_models(**download_params_sfc)

elif modelo == 'ecmwf-aifs-ens':

    model_name = 'aifs-ens'

    download_params_sfc = {
        'type_ecmwf_opendata': ['cf', 'pf'],
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp'],
        'model_ecmwf_opendata': model_name,
    }

    tp_params = {
        'ajusta_acumulado': True,
        'cf_pf_members': True,
    }

    produto_config = Produtos(modelo, resolucao='0p25', name_prefix='sfc', data=data, inicializacao=inicializacao)
    produto_config.download_files_models(**download_params_sfc)

###################################################################################################################

# Inicializando as variaveis para verificar e nao precisar abrir toda hora
tp = None
tp_24h = None
vs = None
us = None
gh = None
gh_24h_500 = None
pnmm = None
t = None
t2m = None
q = None
membros_gefs = None
olr = None
u100 = None

###################################################################################################################

semanas_operativas = ['gfs', 'ecmwf-ens'] #  'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens'
prec_24hr = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens'
acumulado_total = ['gfs']
prec24hr_pnmm = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens']
vento_jato_div200 = ['gfs', 'ecmwf']
geop_500 = ['gfs', 'ecmwf']
geop_vort_500 = ['gfs', 'ecmwf']
vento_temp850 = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens']
vento_850 = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens']
chuva_geop500_vento850 = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens']
ivt = ['gfs', 'ecmwf'] # , 'gefs', 'ecmwf-aifs', 'ecmwf-aifs-ens', 'ecmwf-ens']

modelos_um_config = ['gfs']
modelos_mult_config = ['ecmwf']

###################################################################################################################

if modelo_fmt in semanas_operativas:
    gerar_semanas_operativas(modelo_fmt, produto_config, tp_params, membros=membros)

# if modelo_fmt in prec_24hr:
#     gerar_prec24h(modelo_fmt, produto_config, tp_params)

# if modelo_fmt in acumulado_total:
#     gerar_acumulado_total(modelo_fmt, produto_config, tp_params)

# if modelo_fmt in prec24hr_pnmm:
#     gerar_prec24hr_pnmm(modelo_fmt, produto_config, tp_params)

# if modelo_fmt in vento_jato_div200:

#     if modelo_fmt in modelos_um_config:
#         gerar_jato_div200(modelo_fmt, produto_config)
    
#     elif modelo_fmt in modelos_mult_config:
#         gerar_jato_div200(modelo_fmt, produto_config_pl)

# if modelo_fmt in geop_500:

#     if modelo_fmt in modelos_um_config:
#         gerar_geop_500(modelo_fmt, produto_config)
    
#     elif modelo_fmt in modelos_mult_config:
#         gerar_geop_500(modelo_fmt, produto_config_pl)

# if modelo_fmt in geop_vort_500:

#     if modelo_fmt in modelos_um_config:
#         gerar_geop_vorticidade_500(modelo_fmt, produto_config)
    
#     elif modelo_fmt in modelos_mult_config:
#         gerar_geop_vorticidade_500(modelo_fmt, produto_config_pl)

# if modelo_fmt in vento_temp850:

#     if modelo_fmt in modelos_um_config:
#         gerar_vento_temp850(modelo_fmt, produto_config)
    
#     elif modelo_fmt in modelos_mult_config:
#         gerar_vento_temp850(modelo_fmt, produto_config_pl)    

# if modelo_fmt in vento_850:

#     if modelo_fmt in modelos_um_config:
#         gerar_vento850(modelo_fmt, produto_config)

#     elif modelo_fmt in modelos_mult_config:
#         gerar_vento850(modelo_fmt, produto_config_pl)

# if modelo_fmt in chuva_geop500_vento850:

    # if modelo_fmt in modelos_um_config:
    #     gerar_chuva_geop500_vento850(modelo_fmt, produto_config, tp_params)
    
    # elif modelo_fmt in modelos_mult_config:
    #     gerar_chuva_geop500_vento850(modelo_fmt, produto_config_pl, tp_params, produto_config_sf=produto_config)

# if modelo in ivt:

#     if modelo_fmt in modelos_um_config:
#         gerar_ivt(modelo_fmt, produto_config)
    
#     elif modelo_fmt in modelos_mult_config:
#         gerar_ivt(modelo_fmt, produto_config_pl)

###################################################################################################################

end_time = time.time()
execution_time = end_time - start_time

# Colocando em minutos
execution_time = execution_time / 60  # Convertendo para minutos
print(f'Tempo de execução: {execution_time:.2f} minutos')


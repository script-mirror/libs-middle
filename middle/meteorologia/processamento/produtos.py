from datetime import datetime
import requests
import os
import time
import pandas as pd
from ..utils.utils import abrir_modelo_sem_vazios, ajusta_lon_0_360, ajusta_acumulado_ds
from ..consts.constants import CONSTANTES
from middle.utils import Constants
import shutil

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
                               type_ecmwf_opendata='fc', levtype_ecmwf_opendata='sfc', levlist_ecmwf_opendata=None, sub_region_as_gribfilter=False, baixa_arquivos=True) -> None:

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
            tamanho_min_bytes = 45 * 1024 * 1024  # 45 MB

            while True:
                caminho_arquivo = f'{caminho_para_salvar}/{last_member_file}'
                if os.path.exists(caminho_arquivo):
                    tamanho = os.path.getsize(caminho_arquivo)
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

                while True:
                    todos_sucesso = True  # Flag para sair do while quando todos forem baixados corretamente

                    for i in steps:
                        filename = f'{self.name_prefix}_{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2' if self.name_prefix else f'{modelo_fmt}_{data_fmt}{inicializacao_fmt}_{i:03d}.grib2'
                        caminho_arquivo = f'{caminho_para_salvar}/{filename}'

                        # Se o arquivo já existe e está com tamanho esperado, pula
                        if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) >= file_size:
                            print(f'✅ Arquivo {filename} já existe e está OK, pulando download...')
                            continue

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
                                print(f'Arquivo {filename} está vazio/corrompido, removendo...')
                                os.remove(caminho_arquivo)
                                todos_sucesso = False
                                time.sleep(5)
                                break  # Sai do for e tenta de novo no while
                            else:
                                print(f'✅ Arquivo {filename} baixado com sucesso!')
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

                        fcst_fmt = str(fcst_fmt + 1).zfill(2)

                        while os.path.isfile(f'{caminho_para_salvar}/ecmwf-est_{fcst_fmt}.grib2') == False:

                            dia_mes_prev = dates.strftime('%m%d')

                            try:
                                shutil.copyfile(f'{ftp_dir}/A1F{dia_mes_ini}0000{dia_mes_prev}____1', f'{caminho_para_salvar}/ecmwf-est_{fcst_fmt}.grib2')
    
                            except:
                                print('tentando')
                                time.sleep(10)

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
    def open_model_file(self, variavel: str, sel_area=False, ensemble_mean=False, cf_pf_members=False, arquivos_membros_diferentes=False, ajusta_acumulado=False, m_to_mm=False, ajusta_longitude=True, sel_12z=False, expand_isobaric_dims=False):

        print(f'\n************* ABRINDO DADOS {variavel} DO MODELO {self.modelo.upper()} *************\n')
        import xarray as xr
        import pdb

        # Importando os tipos de variáveis do arquivo de constantes
        surface = CONSTANTES['tipos_variaveis']['surface']
        height_above_ground = CONSTANTES['tipos_variaveis']['height_above_ground']
        isobaric_inhPa = CONSTANTES['tipos_variaveis']['isobaric_inhPa']
        mean_sea = CONSTANTES['tipos_variaveis']['mean_sea']
        nominalTop = CONSTANTES['tipos_variaveis']['nominalTop']

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

###################################################################################################################

class ConfigProdutosObservado:

    def __init__(self, modelo: str, data: datetime, output_path='./tmp/downloads'):
        
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
        caminho_para_salvar = f'{output_path}/{modelo_fmt}/'
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

    # --- ABERTURA DOS DADOS ---
    def open_model_file(self, todo_dir=False, unico=False, ajusta_nome=True, ajusta_longitude=True, apenas_mes_atual=False, variavel=None, ultimos_n_dias=False, n_dias=15):

        import xarray as xr
        import pdb

        print(f'\n************* ABRINDO DADOS {variavel} DO MODELO {self.modelo.upper()} *************\n')
        output_path = self.output_path

        # Formatando modelo
        modelo_fmt = self.modelo.lower()

        # Caminho para salvar os arquivos
        caminho_para_salvar = f'{output_path}/{modelo_fmt}'
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


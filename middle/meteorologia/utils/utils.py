import pandas as pd
import xarray as xr
import numpy as np
import pendulum
import locale
import os
from middle.utils import Constants

###################################################################################################################

def encontra_semanas_operativas(inicializacao, data, qtdade_max_semanas=6, date_format='%d/%m/%Y\ %H\ UTC', ds_tempo_final=None, modelo=None):

    tempos_iniciais = []
    tempos_finais = []
    num_semana = []
    dates_range = []
    intervalos_fmt = []
    days_of_weeks = []

    if inicializacao.hour == 18:
        tempo_ds_inicial = pd.to_datetime(inicializacao, format='%Y%m%d%H') + pd.Timedelta(days=1)

    else:
        tempo_ds_inicial = pd.to_datetime(inicializacao, format='%Y%m%d%H')

    for semanas in range(qtdade_max_semanas):

        if semanas == 0:

            tempoinicial = pd.to_datetime(pd.to_datetime(tempo_ds_inicial, format='%Y%m%d%H').strftime('%Y-%m-%d'))
            tempofinal = pd.to_datetime(pendulum.datetime(int(str(tempoinicial).split('-')[0]), 
                int(str(tempoinicial).split('-')[1]), 
                int(str(tempoinicial).split('-')[2].split(' ')[0])
                ).next(pendulum.SATURDAY).strftime('%Y-%m-%d'))          

        else:

            tempoinicial = pd.to_datetime(tempofinal)
            tempofinal = pd.to_datetime(pendulum.datetime(int(str(tempofinal).split('-')[0]), 
                    int(str(tempofinal).split('-')[1]), 
                    int(str(tempofinal).split('-')[2].split(' ')[0])
                    ).next(pendulum.SATURDAY).strftime('%Y-%m-%d'))
            
        if ds_tempo_final:

            ds_tempo_final = pd.to_datetime(ds_tempo_final)

            if tempofinal + np.timedelta64(6, 'h') >= ds_tempo_final:

                if modelo.lower() != 'ecmwf-ens-estendido':

                    if modelo.lower() == 'eta':
                        tempofinal = pd.to_datetime(ds_tempo_final)

                    else:

                        if inicializacao.hour == 0:
                            tempofinal = ds_tempo_final - pd.Timedelta(hours=12)
                        elif inicializacao.hour == 6:
                            tempofinal = ds_tempo_final - pd.Timedelta(hours=18)
                        elif inicializacao.hour == 12:
                            tempofinal = pd.to_datetime(ds_tempo_final)
                        elif inicializacao.hour == 18:
                            tempofinal = ds_tempo_final - pd.Timedelta(hours=6)
                        else:
                            tempofinal = ds_tempo_final
                
                else:

                    tempofinal = pd.to_datetime(ds_tempo_final)

                intervalo = pd.date_range(tempoinicial.strftime('%Y-%m-%d'), tempofinal.strftime('%Y-%m-%d'), freq='D')
                intervalo_fmt = [str(intervalo[0]).split(' ')[0]+'T18', tempofinal.strftime('%Y-%m-%dT%H')]

            else:

                intervalo = pd.date_range(tempoinicial.strftime('%Y-%m-%d'), tempofinal.strftime('%Y-%m-%d'), freq='D')
                intervalo_fmt = [str(intervalo[0]).split(' ')[0]+'T18', str(intervalo[-1]).split(' ')[0]+'T12']

        date_range = pd.date_range(tempoinicial, tempofinal)
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
        days_of_week = [x.strftime('%a')[0].upper() for x in intervalo]
        days_of_week = ''.join(days_of_week[1:])
        tempos_iniciais.append(tempoinicial) 
        tempos_finais.append(tempofinal) 
        num_semana.append(semanas+1)
        dates_range.append(date_range)
        intervalos_fmt.append(intervalo_fmt)
        days_of_weeks.append(days_of_week)

    for index, date_range in enumerate(dates_range):

        data_nova = pd.to_datetime(data, format=date_format).strftime('%Y-%m-%d')
        data_nova = pd.to_datetime(data_nova)

        if data_nova in date_range:
            semana_encontrada = index+1

    return semana_encontrada, tempos_iniciais, tempos_finais, num_semana, dates_range, intervalos_fmt, days_of_weeks

###################################################################################################################

def extrair_data_hindcast(nome_arquivo):

    data = nome_arquivo.split('_')[-1].split('pmais1')[-1].split('.nc')[0].split('A1H')[-1][0:4]
    data = pd.to_datetime(data, format='%m%d').strftime('%m%d')

    return int(data) # Retornar a data como xum número inteiro no formato MMDD

###################################################################################################################

def ajusta_lon_0_360(ds, var='longitude'):

    if var in ds.dims:
        ds[var] = (ds[var] + 360) % 360

    return ds.sortby('longitude')

###################################################################################################################

def ajusta_lon_180_180(ds, var='longitude'):

    if var in ds.dims:
        ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

    return ds

###################################################################################################################

def open_hindcast_file(var_anomalia, level_anomalia=None, path_clim=Constants().PATH_HINDCAST_ECMWF_EST, inicio_mes=False, modelo='ecmwf-ens-estendido', mesdia=None):

    from datetime import datetime

    if 'ecmwf' in modelo.lower():

        # Pegando a última climatologia
        files_clim = os.listdir(path_clim)
        files_clim = sorted([x for x in files_clim if var_anomalia in x if 'pmenos2' in x], key=extrair_data_hindcast)

        if inicio_mes:
            files_clim_mes1 = None
            tempoinicial_mes1 = pd.to_datetime(datetime(datetime.now().year, datetime.now().month, 1))
            tempoinicial_mes1_comparar = pd.to_datetime(pd.to_datetime(tempoinicial_mes1).strftime('%Y-%m-%d')).strftime('%m-%d')
            # Se o tempo inicial for menor que tempo inicial (começo do mes1), pega o hindcast com o mes completo
            for file_clim in files_clim[-30:]:

                ds_temp = xr.open_dataset(f'{path_clim}/{file_clim}')
                tempo_temp = pd.to_datetime(pd.to_datetime(ds_temp['alvo_previsao'][0].values).strftime('%Y-%m-%d')).strftime('%m-%d')

                if pd.to_datetime(tempo_temp, format='%m-%d') <= pd.to_datetime(tempoinicial_mes1_comparar, format='%m-%d'):
                    files_clim_mes1 = file_clim

        else:
            files_clim_mes1 = files_clim[-1]

        # Abre o arquivo de climatologia
        ds_clim = xr.open_dataset(f'{path_clim}/{files_clim_mes1}')

        # Ajustando longitude
        if var_anomalia in ['tp', 'gh']:
            ds_clim = ajusta_lon_0_360(ds_clim)

        # Selando o level, se existir
        if 'isobaricInhPa' in ds_clim.dims and level_anomalia is not None:
            ds_clim = ds_clim.sel(isobaricInhPa=level_anomalia)

    elif 'gefs' in modelo.lower():

        files_clim = f'{mesdia}_GEFS_REFORECAST.nc'
        # Abre o arquivo de climatologia
        ds_clim = xr.open_dataset(f'{path_clim}/{files_clim}')
        ds_clim = ds_clim.rename({'valid_time': 'alvo_previsao'})

    return ds_clim

###################################################################################################################

def resample_variavel(ds, modelo='ecmwf', coluna_prev='tp', freq='24h', qtdade_max_semanas=3, modo_agrupador='sum', anomalia_sop=False, var_anomalia='tp', level_anomalia=200, prob_semana=False):

    # Condição inicial do dataset
    inicializacao = pd.to_datetime(ds.time.data)

    '''
    Acumula precipitação do xarray que está de 6 em 6 horas para outro período
    considerando o período de 12 UTC do dia anterior até 12 UTC do dia atual
    '''

    if freq == '24h':

        dataini = ds[coluna_prev].valid_time[0].values
        times = ds.valid_time 
        times_12h = times.sel(valid_time=times.dt.hour == 12) 
        datafim = pd.to_datetime(times_12h.valid_time[-2].values)
        intervals = []

        for day in pd.date_range(start=dataini, end=datafim, freq='D'):

            if modelo.lower() == 'eta':
                if pd.to_datetime(dataini).hour == 0:  # rodada das 0
                    interval_start = day + pd.Timedelta(hours=13)
                    interval_end = day + pd.Timedelta(hours=36)
                    intervals.append((interval_start, interval_end))

            elif any(m in modelo.lower() for m in ['gefs', 'gfs', 'ecmwf']):
                hour_ini = pd.to_datetime(dataini).hour
                if hour_ini == 0:
                    interval_start = day + pd.Timedelta(hours=18)
                    interval_end = day + pd.Timedelta(hours=36)
                elif hour_ini == 6:
                    interval_start = day + pd.Timedelta(hours=12)
                    interval_end = day + pd.Timedelta(hours=30)
                elif hour_ini == 12:
                    interval_start = day + pd.Timedelta(hours=6)
                    interval_end = day + pd.Timedelta(hours=24)
                elif hour_ini == 18:
                    interval_start = day + pd.Timedelta(hours=24)
                    interval_end = day + pd.Timedelta(hours=42)
                else:
                    continue
                intervals.append((interval_start, interval_end))

        # Lista para armazenar dados
        data_inicial = []
        data_final = []
        chuva = []

        for interval_start, interval_end in intervals:
            filtered_ds = ds.sel(valid_time=slice(interval_start, interval_end))

            if modo_agrupador == 'sum':
                daily_sum = filtered_ds[coluna_prev].sum(dim='valid_time')
            elif modo_agrupador == 'mean':
                daily_sum = filtered_ds[coluna_prev].mean(dim='valid_time')
            elif modo_agrupador == 'min':
                daily_sum = filtered_ds[coluna_prev].min(dim='valid_time')
            elif modo_agrupador == 'max':
                daily_sum = filtered_ds[coluna_prev].max(dim='valid_time')

            data_inicial.append(interval_start - pd.Timedelta(hours=1) if modelo.lower() == 'eta' else interval_start)
            data_final.append(interval_end)
            chuva.append(daily_sum)

        # Convertendo listas em um Dataset final
        final_ds = xr.Dataset({
            coluna_prev: xr.concat(chuva, dim='tempo')
        }, coords={
            'data_inicial': ('tempo', data_inicial),
            'data_final': ('tempo', data_final)
        })

    elif freq == 'sop': # Semana operativa

        # Data ficticia de início
        data = pd.to_datetime(ds[coluna_prev].valid_time[1].values, format='%d/%m/%Y\ %H\ UTC')
        ds_tempo_final = ds.valid_time[-1].values
        
        semana_encontrada, tempos_iniciais, tempos_finais, num_semana, dates_range, intervalos_fmt, days_of_weeks = encontra_semanas_operativas(
            inicializacao, data, qtdade_max_semanas=qtdade_max_semanas, modelo=modelo, ds_tempo_final=ds_tempo_final
        )
        
        # Lista para armazenar os acumulados
        lista_acumulados = []
        intervalo_labels = []

        # Abrindo arquivo de climatologia
        if anomalia_sop:

            if 'ecmwf' in modelo.lower():
                ds_clim = open_hindcast_file(var_anomalia, level_anomalia, modelo=modelo)

            elif 'gefs' in modelo.lower():
                ds_clim = open_hindcast_file(var_anomalia, path_clim=Constants().PATH_HINDCAST_GEFS_EST, mesdia=pd.to_datetime(ds.time.data).strftime('%m%d'), modelo=modelo)
    
        # Itera sobre os intervalos e semanas
        for (inicio, fim), semana, day_of_weeks in zip(intervalos_fmt, num_semana, days_of_weeks):

            # Ajustando o texto do título
            if modelo not in ['ecmwf-ens-estendido']:
                hours_timedelta = 6

            else:
                if semana == 1:
                    hours_timedelta = 6

                else:
                    hours_timedelta = 6

            # Selecionando os tempos das SOP
            ds_sel = ds.sel(valid_time=slice(inicio, fim))

            if anomalia_sop:
                # Interpola
                ds_clim = interpola_ds(ds_clim, ds_sel)    

                # Anos iniciais e finais da climatologia
                ano_ini = pd.to_datetime(ds_clim.alvo_previsao[0].values).strftime('%Y')
                ano_fim = pd.to_datetime(ds_clim.alvo_previsao[-1].values).strftime('%Y')

                # Pegando o ano inicial da previsao (ds_sel)
                ano_prev_1 = inicio.split('-')[0]
                ano_prev_2 = fim.split('-')[0]

                if int(ano_prev_1) == int(ano_prev_2):
                    intervalo1 = inicio.replace(inicio[:4], ano_ini)
                    intervalo2 = fim.replace(inicio[:4], ano_ini)

                else:
                    intervalo1 = inicio.replace(inicio[:4], ano_ini)
                    intervalo2 = fim.replace(inicio[:4], ano_fim)          

                # Sel nos tempos encontrados
                ds_clim_sel = ds_clim.sel(alvo_previsao=slice(intervalo1, intervalo2))

                # Calcula a anomalia
                if modo_agrupador == 'sum':
                    ds_sel = ds_sel[coluna_prev].sum(dim='valid_time') - ds_clim_sel[coluna_prev].sum(dim='alvo_previsao')

                else:
                    ds_sel = ds_sel[coluna_prev].mean(dim='valid_time') - ds_clim_sel[coluna_prev].mean(dim='alvo_previsao')
                
                # Calcula a anomalia
                # if modo_agrupador == 'sum':
                #     if prob_semana:
                #         ds_sel = ds_sel[coluna_prev] - ds_clim_sel[coluna_prev]
                        
                #     else:
                #         ds_sel = ds_sel[coluna_prev].sum(dim='valid_time') - ds_clim_sel[coluna_prev].sum(dim='alvo_previsao')

                # else:
                #     if prob_semana:
                #         ds_sel = ds_sel[coluna_prev] - ds_clim_sel[coluna_prev]
                        
                #     else:
                #         ds_sel = ds_sel[coluna_prev].mean(dim='valid_time') - ds_clim_sel[coluna_prev].mean(dim='alvo_previsao')

            else:
                ds_sel = ds_sel.sum(dim='valid_time') if modo_agrupador == 'sum' else ds_sel.mean(dim='valid_time')

            # Cria o rótulo do intervalo
            inicio = pd.to_datetime(inicio) - pd.Timedelta(hours=hours_timedelta)  # Ajusta para o início do dia
            fim = pd.to_datetime(fim)
            intervalo_str = f"{inicio.strftime('%d/%m/%Y %H UTC')} até {fim.strftime('%d/%m/%Y %H UTC')}"
            
            # Adiciona nova coordenada para a semana e o intervalo
            ds_sel = ds_sel.expand_dims({'tempo': [semana]})
            ds_sel = ds_sel.assign_coords(intervalo=intervalo_str)
            ds_sel = ds_sel.assign_coords(days_of_weeks=day_of_weeks)

            if isinstance(ds_sel, xr.DataArray):
                ds_sel = ds_sel.to_dataset()
            
            lista_acumulados.append(ds_sel)

        # Concatena ao longo da nova dimensão
        final_ds = xr.concat(lista_acumulados, dim='tempo')

        # A coordenada 'intervalo' está repetida para cada semana, mas pode ser alinhada
        final_ds = final_ds.assign_coords(intervalo=("tempo", intervalo_labels or final_ds['intervalo'].values))

    elif freq == 'pentada':

        # Data ficticia de início
        data = pd.to_datetime(ds[coluna_prev].valid_time[1].values, format='%d/%m/%Y\ %H\ UTC')
        ds_tempo_final = ds.valid_time[-1].values

        # Encontrando os intervalos de pentadas
        intervalos_pentada = []
        for i in range(5):
            inicio = data + pd.Timedelta(days=i*7)
            fim = inicio + pd.Timedelta(days=6)
            intervalos_pentada.append((inicio, fim))

        # Lista para armazenar dados
        data_inicial = []
        data_final = []
        chuva = []

        for interval_start, interval_end in intervalos_pentada:
            filtered_ds = ds.sel(valid_time=slice(interval_start, interval_end))
            daily_sum = filtered_ds[coluna_prev].sum(dim='valid_time')

            data_inicial.append(interval_start)
            data_final.append(interval_end)
            chuva.append(daily_sum)

        # Convertendo listas em um Dataset final
        final_ds = xr.Dataset({
            'chuva': xr.concat(chuva, dim='tempo')
        }, coords={
            'data_inicial': ('tempo', data_inicial),
            'data_final': ('tempo', data_final)
        })

    elif freq == 'mensal':

        # Abrindo arquivo de climatologia
        if anomalia_sop:

            if 'ecmwf' in modelo.lower():
                ds_clim = open_hindcast_file(var_anomalia, level_anomalia)

            elif 'gefs' in modelo.lower():
                ds_clim = open_hindcast_file(var_anomalia, path_clim=Constants().PATH_HINDCAST_GEFS_EST, mesdia=pd.to_datetime(ds.time.data).strftime('%m%d'))

    return final_ds

###################################################################################################################

def abrir_modelo_sem_vazios(files, backend_kwargs=None, concat_dim='valid_time', sel_area=True):

    backend_kwargs = backend_kwargs or {}
    datasets = []

    for index, f in enumerate(files):

        print(f'Abrindo {f}... ({index+1}/{len(files)})')

        try:
            ds = xr.open_dataset(f, engine='cfgrib', backend_kwargs=backend_kwargs, decode_timedelta=True)

            # Renomeando lat para latitude e lon para longitude
            if 'lat' in ds.dims:
                ds = ds.rename({'lat': 'latitude'})

            if 'lon' in ds.dims:
                ds = ds.rename({'lon': 'longitude'})

            if 'longitude' in ds.dims:
                ds = ajusta_lon_0_360(ds)

            if sel_area:
                if 'longitude' in ds.dims and 'latitude' in ds.dims:
                    ds = ds.sortby(['latitude', 'longitude'])
                    ds = ds.sel(latitude=slice(-60, 20), longitude=slice(240, 360))    

            if 'step' in ds.dims:
                ds = ds.swap_dims({'step': 'valid_time'})
                
            if ds.variables:
                datasets.append(ds)

            else:
                print(f'Arquivo ignorado (sem variáveis): {f}')
        except Exception as e:
            print(f'Erro ao abrir {f}: {e}')

    if not datasets:
        raise ValueError("Nenhum arquivo válido encontrado.")

    return xr.concat(datasets, dim=concat_dim)

###################################################################################################################

def ensemble_mean(data):
    return data.mean(dim='number') if 'number' in data.dims else data.copy()

###################################################################################################################

def get_inicializacao_fmt(data, format='%d/%m/%Y %H UTC'):
    return pd.to_datetime(data.time.values).strftime(format)

###################################################################################################################

def get_dado_cacheado(var, obj, varname=None, usa_variavel=True, verifica_cache=True, **kwargs):
    """
    Carrega e cacheia dados de modelo ou observação.

    Parâmetros
    ----------
    var : str
        Nome da variável (pode ser ignorado se usa_variavel=False).
    obj : objeto
        Objeto com método `open_model_file`.
    varname : str, opcional
        Nome usado no cache (default = var).
    usa_variavel : bool, opcional
        Se True, passa `variavel=varname` para open_model_file (modelo).
        Se False, não passa (observação).
    **kwargs : dict
        Argumentos extras para open_model_file.
    """
    varname = varname or var

    if verifica_cache:

        if varname not in globals():
            if usa_variavel:
                globals()[varname] = obj.open_model_file(variavel=varname, **kwargs).load()
            else:
                globals()[varname] = obj.open_model_file(**kwargs).load()

    else:
        if usa_variavel:
            globals()[varname] = obj.open_model_file(variavel=varname, **kwargs).load()
        else:
            globals()[varname] = obj.open_model_file(**kwargs).load()

    return globals()[varname]

###################################################################################################################

def interpola_ds(ds_alvo, ds_referencia):
    """
    Interpola o dataset ds_alvo para o grid do dataset ds_referencia.

    Parâmetros:
    -----------
    ds_alvo : xarray.Dataset
        Dataset a ser interpolado.
    ds_referencia : xarray.Dataset
        Dataset de referência com o grid desejado.

    Retorna:
    --------
    xarray.Dataset
        Dataset interpolado.
    """
    return ds_alvo.interp(latitude=ds_referencia.latitude.values, longitude=ds_referencia.longitude.values)

###################################################################################################################

def format_intervalo(intervalo_str):
    return intervalo_str.replace(' ', '\\ ')

###################################################################################################################

def ajustar_hora_utc(dt):
    return dt - pd.Timedelta(hours=6) if dt.hour == 18 else dt

###################################################################################################################

def gerar_titulo(modelo, tipo, cond_ini, data_ini=None, data_fim=None, semana=None, semana_operativa=False, intervalo=None, days_of_week=None, sem_intervalo_semana=False, unico_tempo=False, condicao_inicial='Condição Inicial', prefixo_negrito=False, prefixo=None):

    modelo = modelo.replace('ecmwf-ens', 'ec-ens').replace('estendido', 'est').replace('pconjunto', 'pconj')

    if semana_operativa:

        titulo = (f'{modelo.upper()} - {tipo} \u2022 '
                f'{condicao_inicial}: {cond_ini}\n'
                f'$\mathbf{{Válido\ de\ {intervalo}\ \u2022\ {days_of_week}}}$')
        
    elif sem_intervalo_semana:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'{condicao_inicial}: {cond_ini}\n'
            f'$\\mathbf{{Válido\ de\ {data_ini}\ a\ {data_fim}}}$'
        )

    elif prefixo_negrito:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'{condicao_inicial}: {cond_ini}\n'
            f'$\\mathbf{{Válido\\ {prefixo}\\ de\\ {data_ini}\\ a\\ {data_fim}}}$'
        )
     
    elif unico_tempo:

        if semana is not None:

            titulo = (
                f'{modelo.upper()} - {tipo} \u2022 '
                f'{condicao_inicial}: {cond_ini}\n'
                f'$\\mathbf{{Válido\\  para\\ {data_ini}\\ \u2022\\ S{semana}}}$'
            )

        else:

            titulo = (
                f'{modelo.upper()} - {tipo} \u2022 '
                f'{condicao_inicial}: {cond_ini}\n'
                f'$\\mathbf{{Válido\\ para\\ {data_ini}}}$'
            )

    else:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'{condicao_inicial}: {cond_ini}\n'
            f'$\\mathbf{{Válido\\ de\\ {data_ini}\\ a\\ {data_fim}\\ \u2022\\ S{semana}}}$'
        )

    return titulo

###################################################################################################################

def encontra_casos_frentes_xarray(ds_slp, ds_vwnd, ds_air, varname='prmsl'):

    cond1 = ds_slp[varname].diff(dim='valid_time') > 0  # Aumento da pressão
    cond2 = (ds_vwnd["v"].shift(valid_time=1) < 0) & (ds_vwnd["v"] > 0)
    cond3 = ds_air["t"].diff(dim='valid_time') < 0  # Temperatura diminuindo
    cond_total = cond1 & cond2 & cond3

    return cond_total.sum(dim='valid_time')

###################################################################################################################

def skip_zero_formatter(x):
    return '' if x == 0 else f'{x:.0f}'

###################################################################################################################

def get_lat_lon_from_df(row, df):
    latitude = df[df['cod_psat'] == row]['vl_lat'].values[0]
    longitude = df[df['cod_psat'] == row]['vl_lon'].values[0]
    
    return latitude, longitude

###################################################################################################################

def get_df_ons():

    import requests
    from middle.utils import get_auth_header
    API_URL = Constants().API_URL_APIV2

    # Vou usar para pegar as informações das subbacias
    df_ons = requests.get(f"{API_URL}/rodadas/subbacias", verify=False, headers=get_auth_header())
    df_ons = pd.DataFrame(df_ons.json()).rename(columns={"nome":"cod_psat", 'id': 'cd_subbacia'})

    return df_ons

###################################################################################################################

def ajusta_shp_json():

    import geopandas as gpd
    # import requests
    # from middle.utils import get_auth_header
    # API_URL = Constants().API_URL_APIV2

    # Abrindo arquvos das subbacias
    shp_path_bacias = Constants().PATH_SUBBACIAS_JSON
    shp = gpd.read_file(shp_path_bacias)
    
    # Vou usar para pegar as informações das subbacias
    # df_ons = requests.get(f"{API_URL}/rodadas/subbacias", verify=False, headers=get_auth_header())
    # df_ons = pd.DataFrame(df_ons.json()).rename(columns={"nome":"cod_psat", 'id': 'cd_subbacia'})
    df_ons = get_df_ons()

    # Atribuindo os valores de latitude e longitude no arquivo shp
    shp[['lat', 'lon']] = shp['cod'].apply(lambda row: pd.Series(get_lat_lon_from_df(row, df_ons)))

    return shp

###################################################################################################################

def calcula_media_bacia(dataset, lat, lon, bacia, codigo, shp):

    import regionmask

    if shp[shp['nome'] == bacia].geometry.values[0] is None:
        # print(f'Não há pontos na bacia {bacia}. Código {codigo}. Pegando o mais próximo')
        media = dataset.sel(latitude=lat, longitude=lon, method='nearest')
        media = media.drop_vars(['latitude', 'longitude'])
    else:
        bacia_mask = regionmask.Regions(shp[shp['nome'] == bacia].geometry)
        mask = bacia_mask.mask(dataset.longitude, dataset.latitude)
        chuva_mask = dataset.where(mask == 0)
        media = chuva_mask.mean(('latitude', 'longitude'))

        if pd.isna(media['tp'].values.mean()):
            # print(f'Não há pontos na bacia {bacia}. Código {codigo}. Pegando o mais próximo')
            media = dataset.sel(latitude=lat, longitude=lon, method='nearest')
            media = media.drop_vars(['latitude', 'longitude'])

    return media.expand_dims({'id': [codigo]})

###################################################################################################################

def converter_psat_para_cd_subbacia(df:pd.DataFrame):

    import requests
    from middle.utils import get_auth_header
   
    df_subbacias = requests.get("https://tradingenergiarz.com/api/v2/rodadas/subbacias", verify=False, headers=get_auth_header())
    df_subbacias = pd.DataFrame(df_subbacias.json()).rename(columns={"nome":"cod_psat"})[["cod_psat", "id"]]

    if 'cd_psat' in df_subbacias.columns:
        df_subbacias = df_subbacias.rename(columns={"cd_psat":"cod_psat"})

    if 'cd_psat' in df.columns:
        df = df.rename(columns={"cd_psat":"cod_psat"})

    merge = df.merge(df_subbacias, on='cod_psat')
    merge = merge.rename(columns={"id":"cd_subbacia"})

    return merge

###################################################################################################################

def ajusta_acumulado_ds(ds: xr.Dataset, m_to_mm=True):

    variaveis_com_valid_time = [v for v in ds.data_vars if 'valid_time' in ds[v].dims]

    ds_diff = xr.Dataset()

    for var in variaveis_com_valid_time:
        primeiro = ds[var].isel(valid_time=0)
        dif = ds[var].diff(dim='valid_time')
        dif_completo = xr.concat([primeiro, dif], dim='valid_time')
        ds_diff[var] = dif_completo

    ds_diff['valid_time'] = ds['valid_time']
    ds = ds_diff

    if m_to_mm:
        ds = ds * 1000  # Convertendo de metros para milímetros

    return ds

###################################################################################################################

def get_prec_db(modelo: str, dt_modelo: str, hr_rodada=None):

    def to_geopandas(df, lon, lat):

        from shapely.geometry import Point
        import geopandas as gpd
        
        geometry = [Point(xy) for xy in zip(df[lon], df[lat])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry)
        gdf = gdf.set_crs("EPSG:4326")

        shp_file = gpd.read_file(Constants().PATH_SUBBACIAS_JSON)
        gdf_basins = shp_file.to_crs(gdf.crs)    

        def geometry_basin(codigo, gdf_basins):

            try:
                geometry = gdf_basins[gdf_basins['cod'] == codigo]['geometry'].values[0]
            except:
                geometry = np.nan
            return geometry

        gdf['geometry'] = gdf['cod_psat'].apply(lambda x: geometry_basin(x, gdf_basins))

        return gdf

    import requests
    from middle.utils import get_auth_header

    if modelo in ['merge', 'mergegpm']:
        response = requests.get(f'https://tradingenergiarz.com/api/v2/rodadas/chuva/observada?dt_observada={dt_modelo}', verify=False, headers=get_auth_header())

    else:
        dt_hr_rodada = f'{dt_modelo}%20{hr_rodada}'
        response = requests.get(f'https://tradingenergiarz.com/api/v2/rodadas/chuva/previsao?nome_modelo={modelo}&dt_hr_rodada={dt_hr_rodada}%3A00%3A00&granularidade=subbacia&no_cache=true&atualizar=false', verify=False, headers=get_auth_header())
        
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        df_ons = get_df_ons()
        df = pd.merge(df, df_ons, on='cd_subbacia', how='left')
        df = to_geopandas(df, 'vl_lon', 'vl_lat')

    return df

###################################################################################################################

def get_pontos_localidades():

    # Coordenadas que vamos extrair os pontos
    pontos = pd.read_csv(f'{Constants().PATH_COORDENADAS_CIDADES}/coord_cidades.dat', names=['lat','lon','id'])
    target_lon = xr.DataArray(pontos.lon, dims='id',coords={"id": pontos.id})
    target_lat = xr.DataArray(pontos.lat, dims='id',coords={"id": pontos.id})

    return target_lon, target_lat, pontos

###################################################################################################################

def formato_filename(modelo, variavel, index=None):

    return f'{index}_{variavel}_{modelo}' if index is not None else f'{variavel}_{modelo}'

###################################################################################################################

def painel_png(path_figs, output_file=None, path_figs2=None, str_contain='semana', str_contain2=None, img_size=(6,6)):
    import matplotlib.pyplot as plt 
    from PIL import Image
    import os, math

    if isinstance(path_figs, list):
        lista_png = path_figs
        lista_png = [x for x in lista_png if f'{str_contain}' in x and '.png' in x]
    
    elif isinstance(path_figs, str):
        lista_png = os.listdir(path_figs)
        lista_png = [f'{path_figs}/{x}' for x in lista_png if f'{str_contain}' in x and '.png' in x]

    if path_figs2 is not None:
        lista_png2 = os.listdir(path_figs2)
        if str_contain2 is not None:
            lista_png2 = [f'{path_figs2}/{x}' for x in lista_png2 if f'{str_contain2}' in x and '.png' in x]
        else:
            lista_png2 = [f'{path_figs2}/{x}' for x in lista_png2 if '.png' in x]
        lista_png.extend(lista_png2)

    n_imgs = len(lista_png)
    ncols = 2 if n_imgs > 3 else n_imgs
    nrows = math.ceil(n_imgs / ncols)

    # ajusta dinamicamente o tamanho da figura
    figsize = (img_size[0]*ncols, img_size[1]*nrows)

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, constrained_layout=True)

    if isinstance(axs, plt.Axes):
        axs = [axs]
    else:
        axs = axs.flatten()

    for i, img_path in enumerate(lista_png):
        img = Image.open(img_path)
        axs[i].imshow(img)
        axs[i].axis("off")

    for j in range(n_imgs, len(axs)):
        axs[j].axis("off")

    if output_file:
        path_to_save = f'{Constants().PATH_ARQUIVOS_TEMP}/paineis'
        os.makedirs(path_to_save, exist_ok=True)
        fig.savefig(f'{path_to_save}/{output_file}', dpi=300, bbox_inches="tight", pad_inches=0)
        print(f"✅ Painel salvo em: {output_file}")
        return f'{path_to_save}/{output_file}'

    return fig

###################################################################################################################


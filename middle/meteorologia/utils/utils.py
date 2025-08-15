
import pandas as pd
import xarray as xr
import numpy as np
import pendulum
from scipy.fft import fft2, ifft2, fftfreq
import locale
import os
import pdb
from middle.utils.constants import Constants

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

            tempoinicial = pd.to_datetime(tempofinal) + pd.Timedelta(days=1)
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
            
        date_range = pd.date_range(tempoinicial, tempofinal)
        intervalo_fmt = [str(tempoinicial).split(' ')[0]+'T18', str(tempofinal).split(' ')[0]+'T12']
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
        days_of_week = [x.strftime('%a')[0].upper() for x in date_range]
        days_of_week = ''.join(days_of_week[1:]) if semanas == 0 else ''.join(days_of_week)

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

    return ds

###################################################################################################################

def resample_variavel(ds, modelo='ecmwf', coluna_prev='tp', freq='24h', qtdade_max_semanas=3, modo_agrupador='sum', anomalia_sop=False, var_anomalia='tp', level_anomalia=200):

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
                if pd.to_datetime(dataini).hour == 1:  # rodada das 0
                    interval_start = day + pd.Timedelta(hours=12)
                    interval_end = day + pd.Timedelta(hours=35)
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
            daily_sum = filtered_ds[coluna_prev].sum(dim='valid_time') if modo_agrupador == 'sum' else filtered_ds[coluna_prev].mean(dim='valid_time')

            data_inicial.append(interval_start)
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
        
        _, _, _, num_semana, _, intervalos_fmt, days_of_weeks = encontra_semanas_operativas(
            inicializacao, data, qtdade_max_semanas=qtdade_max_semanas, modelo=modelo, ds_tempo_final=ds_tempo_final
        )

        # Lista para armazenar os acumulados
        lista_acumulados = []
        intervalo_labels = []

        # Itera sobre os intervalos e semanas
        for (inicio, fim), semana, day_of_weeks in zip(intervalos_fmt, num_semana, days_of_weeks):

            # Ajustando o texto do título
            if modelo not in ['ecmwf-ens-estendido']:
                hours_timedelta = 6

            else:
                if semana == 1:
                    hours_timedelta = 6

                else:
                    hours_timedelta = 30

            # Selecionando os tempos das SOP
            ds_sel = ds.sel(valid_time=slice(inicio, fim))

            if anomalia_sop:

                if modelo.lower() == 'ecmwf-ens-estendido':

                    # Definindo qual arquivo de climatologia vou usar
                    path_clim = Constants().PATH_HINDCAST_ECMWF_EST #'/WX4TB/Documentos/saidas-modelos/ecmwf-estendido/data-netcdf'
                    files_clim = os.listdir(path_clim)

                    if var_anomalia not in ['psi', 'chi']:
                        # Pegando a última climatologia
                        files_clim = sorted([x for x in files_clim if var_anomalia in x if 'pmenos2' in x], key=extrair_data_hindcast)[-1]

                        # Abre o arquivo de climatologia
                        ds_clim = xr.open_dataset(f'{path_clim}/{files_clim}')

                        # Ajustando longitude
                        ds_clim = ajusta_lon_0_360(ds_clim) if var_anomalia == 'tp' else ds_clim

                        # Selando o level, se existir
                        if 'isobaricInhPa' in ds_clim.dims:
                            ds_clim = ds_clim.sel(isobaricInhPa=level_anomalia)

                    else:
                        # Pegando a última climatologia
                        files_clim_u = sorted([x for x in files_clim if 'u' in x if 'pmenos2' in x], key=extrair_data_hindcast)[-1]
                        files_clim_v = sorted([x for x in files_clim if 'v' in x if 'pmenos2' in x], key=extrair_data_hindcast)[-1]
                        
                        # Arquivos climatologia
                        ds_clim_u = xr.open_dataset(f'{path_clim}/{files_clim_u}')
                        ds_clim_v = xr.open_dataset(f'{path_clim}/{files_clim_v}')

                        ds_clim = calcula_psi_chi(ds_clim_u, ds_clim_v, dim_laco='alvo_previsao', level=level_anomalia)[0] if var_anomalia == 'psi' else calcula_psi_chi(ds_clim_u, ds_clim_v, dim_laco='valid_time', level=level_anomalia)[1]      
                
                elif modelo.lower() == 'gefs-estendido':

                    # Definindo qual arquivo de climatologia vou usar
                    path_clim = Constants().PATH_HINDCAST_GEFS_EST  #'/WX4TB/Documentos/reforecast_gefs/dados'
                    mesdia = pd.to_datetime(ds.time.data).strftime('%m%d')
                    
                    # Pegando a última climatologia
                    files_clim = f'{mesdia}_GEFS_REFORECAST.nc'

                    # Abre o arquivo de climatologia
                    ds_clim = xr.open_dataset(f'{path_clim}/{files_clim}')

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

    return final_ds

###################################################################################################################

def abrir_modelo_sem_vazios(files, backend_kwargs=None, concat_dim='valid_time'):

    backend_kwargs = backend_kwargs or {}
    datasets = []

    for f in files:
        try:
            ds = xr.open_dataset(f, engine='cfgrib', backend_kwargs=backend_kwargs, decode_timedelta=True)
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

    # """
    # Abre múltiplos arquivos GRIB ignorando os que estão vazios ou corrompidos.

    # Parâmetros:
    # -----------
    # files : list
    #     Lista de caminhos para arquivos GRIB.
    # backend_kwargs : dict, opcional
    #     Argumentos adicionais para o backend 'cfgrib'.
    # concat_dim : str, opcional
    #     Nome da dimensão de concatenação (padrão: 'valid_time').

    # Retorna:
    # --------
    # xarray.Dataset
    #     Dataset combinado com arquivos válidos.
    # """
    # backend_kwargs = backend_kwargs or {}
    # arquivos_validos = []

    # for f in files:
    #     try:

    #         ds = xr.open_dataset(f, engine='cfgrib', backend_kwargs=backend_kwargs, decode_timedelta=True,)
    #         if ds.variables:
    #             arquivos_validos.append(f)
    #         else:
    #             print(f'Arquivo ignorado (sem variáveis): {f}')

    #     except Exception as e:
    #         print(f'Erro ao abrir {f}: {e}')

    # if not arquivos_validos:
    #     raise ValueError("Nenhum arquivo válido encontrado.")

    # pdb.set_trace()

    # ds_final = xr.open_mfdataset(
    #     arquivos_validos,
    #     engine='cfgrib',
    #     backend_kwargs=backend_kwargs,
    #     combine='nested',
    #     concat_dim=concat_dim,
    #     decode_timedelta=True,
    #     drop_variables=['valid_time'],
    # )

    # return ds_final

###################################################################################################################

def ensemble_mean(data):
    return data.mean(dim='number') if 'number' in data.dims else data.copy()

###################################################################################################################

def get_inicializacao_fmt(data, format='%d/%m/%Y %H UTC'):
    return pd.to_datetime(data.time.values).strftime(format)

###################################################################################################################

def get_dado_cacheado(var, obj, varname=None, **kwargs):
    varname = varname or var
    if varname not in globals():
        globals()[varname] = obj.open_model_file(variavel=varname, **kwargs).load()
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
    return ds_alvo.interp(latitude=ds_referencia.latitude, longitude=ds_referencia.longitude)

###################################################################################################################

def format_intervalo(intervalo_str):
    return intervalo_str.replace(' ', '\\ ')

###################################################################################################################

def ajustar_hora_utc(dt):
    return dt - pd.Timedelta(hours=6) if dt.hour == 18 else dt

###################################################################################################################

def gerar_titulo(modelo, tipo, cond_ini, data_ini=None, data_fim=None, semana=None, semana_operativa=False, intervalo=None, days_of_week=None, sem_intervalo_semana=False, unico_tempo=False):

    if semana_operativa:

        titulo = (f'{modelo.upper()} - {tipo} \u2022 '
                f'Condição Inicial: {cond_ini}\n'
                f'$\mathbf{{Válido\ de\ {intervalo}\ \u2022\ {days_of_week}}}$')
        
    elif sem_intervalo_semana:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'Condição Inicial: {cond_ini}\n'
            f'$\\mathbf{{Válido\ de\ {data_ini}\ a\ {data_fim}}}$'
        )

    elif unico_tempo:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'Condição Inicial: {cond_ini}\n'
            f'$\\mathbf{{Válido\\ para\\ {data_ini}\\ \u2022\\ S{semana}}}$'
        )

    else:

        titulo = (
            f'{modelo.upper()} - {tipo} \u2022 '
            f'Condição Inicial: {cond_ini}\n'
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

def calcula_media_bacia(dataset, lat, lon, bacia, codigo, shp):

    import regionmask

    if shp[shp['nome'] == bacia].geometry.values[0] is None:
        print(f'Não há pontos na bacia {bacia}. Código {codigo}. Pegando o mais próximo')
        media = dataset.sel(latitude=lat, longitude=lon, method='nearest')
        media = media.drop_vars(['latitude', 'longitude'])
    else:
        bacia_mask = regionmask.Regions(shp[shp['nome'] == bacia].geometry)
        mask = bacia_mask.mask(dataset.longitude, dataset.latitude)
        chuva_mask = dataset.where(mask == 0)
        media = chuva_mask.mean(('latitude', 'longitude'))

        if pd.isna(media['tp'].values.mean()):
            print(f'Não há pontos na bacia {bacia}. Código {codigo}. Pegando o mais próximo')
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

def calcula_psi_chi(u: xr.DataArray, v: xr.DataArray, dim_laco='valid_time', level=200):

    def ddx(f, dx):
        """Derivada em x"""
        return np.gradient(f, dx, axis=-1)

    def ddy(f, dy):
        """Derivada em y"""
        return np.gradient(f, dy, axis=-2)

    def poisson_solve(rhs, dx, dy):
        """Resolve a equação de Poisson ∇²φ = rhs usando FFT (condições periódicas)"""
        ny, nx = rhs.shape
        kx = 2 * np.pi * fftfreq(nx, dx)
        ky = 2 * np.pi * fftfreq(ny, dy)
        kx2, ky2 = np.meshgrid(kx**2, ky**2)
        denom = kx2 + ky2
        denom[0, 0] = 1  # evitar divisão por zero

        rhs_hat = fft2(rhs)
        sol_hat = -rhs_hat / denom
        sol_hat[0, 0] = 0  # constante arbitrária
        return np.real(ifft2(sol_hat))

    Re = 6.371e6  # raio da Terra (m)
    lat_rad = np.deg2rad(u.latitude)
    dx = (2 * np.pi * Re * np.cos(lat_rad.mean()) / u.sizes['longitude'])
    dy = (2 * np.pi * Re / 360) * (u.latitude[1] - u.latitude[0])
    coords = u.sel(isobaricInhPa=level).isel({dim_laco: 0}).coords

    chis = []
    psis = []

    for tempo in u[dim_laco]:
        du_dx = ddx(u.sel(isobaricInhPa=level)['u'].sel({dim_laco: tempo}).values, dx.values)
        dv_dy = ddy(v.sel(isobaricInhPa=level)['v'].sel({dim_laco: tempo}).values, dy.values)
        du_dy = ddy(u.sel(isobaricInhPa=level)['u'].sel({dim_laco: tempo}).values, dy.values)
        dv_dx = ddx(v.sel(isobaricInhPa=level)['v'].sel({dim_laco: tempo}).values, dx.values)

        # Divergência e vorticidade
        div = du_dx + dv_dy
        vor = dv_dx - du_dy

        # Resolver para chi e psi
        chi = poisson_solve(div, dx.values, dy.values)
        psi = poisson_solve(-vor, dx.values, dy.values)

        # Transformando em um xarray
        chi = xr.DataArray(chi, coords=coords, name="chi")
        psi = xr.DataArray(psi, coords=coords, name="psi")

        # Atribuindo a variavel tempo ao novo DataArray
        chi[dim_laco] = tempo
        psi[dim_laco] = tempo

        chis.append(chi)
        psis.append(psi)

    # Junto tudo 
    chi_total = xr.concat(chis, dim=dim_laco)
    psi_total = xr.concat(psis, dim=dim_laco)

    # Removendo a media zonal
    chi_total = chi_total - chi_total.mean(dim='latitude').mean(dim='longitude')
    chi_total = chi_total - chi_total.mean(dim='longitude')

    psi_total = psi_total - psi_total.mean(dim='latitude').mean(dim='longitude')
    psi_total = psi_total - psi_total.mean(dim='longitude')

    # anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lat').mean(dim='lon')
    # anomalia_psi200 = anomalia_psi200 - anomalia_psi200.mean(dim='lon')

    # anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lat').mean(dim='lon')
    # anomalia_psi850 = anomalia_psi850 - anomalia_psi850.mean(dim='lon')

    # anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lat').mean(dim='lon')
    # anomalia_chi200 = anomalia_chi200 - anomalia_chi200.mean(dim='lon')

    # anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lat').mean(dim='lon')
    # anomalia_chi850 = anomalia_chi850 - anomalia_chi850.mean(dim='lon')

    return psi_total.to_dataset(), chi_total.to_dataset()

###################################################################################################################


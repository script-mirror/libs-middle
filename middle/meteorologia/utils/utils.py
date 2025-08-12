
import pandas as pd
import xarray as xr
import numpy as np
import pendulum
import locale

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

def resample_variavel(ds, modelo='ecmwf', coluna_prev='tp', freq='24h', qtdade_max_semanas=6, modo_agrupador='sum'):

    # Condição inicial do dataset
    inicializacao = pd.to_datetime(ds.time.data)

    '''
    Acumula precipitação do xarray que está de 6 em 6 horas para outro período
    considerando o período de 12 UTC do dia anterior até 12 UTC do dia atual
    '''

    if freq == '24h':

        dataini = ds[coluna_prev].valid_time[0].values
        datafim = ds[coluna_prev].valid_time[-1].values
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

            if modo_agrupador == 'sum':
                # Seleciona e soma o intervalo de tempo
                ds_sel = ds.sel(valid_time=slice(inicio, fim)).sum(dim='valid_time')

            elif modo_agrupador == 'mean':
                # Seleciona e calcula a média do intervalo de tempo
                ds_sel = ds.sel(valid_time=slice(inicio, fim)).mean(dim='valid_time')
            
            # Cria o rótulo do intervalo
            inicio = pd.to_datetime(inicio) - pd.Timedelta(hours=6)  # Ajusta para o início do dia
            fim = pd.to_datetime(fim)
            intervalo_str = f"{inicio.strftime('%d/%m/%Y %H UTC')} até {fim.strftime('%d/%m/%Y %H UTC')}"
            
            # Adiciona nova coordenada para a semana e o intervalo
            ds_sel = ds_sel.expand_dims({'num_semana': [semana]})
            ds_sel = ds_sel.assign_coords(intervalo=intervalo_str)
            ds_sel = ds_sel.assign_coords(days_of_weeks=day_of_weeks)

            lista_acumulados.append(ds_sel)

        # Concatena ao longo da nova dimensão
        final_ds = xr.concat(lista_acumulados, dim='num_semana')

        # A coordenada 'intervalo' está repetida para cada semana, mas pode ser alinhada
        final_ds = final_ds.assign_coords(intervalo=("num_semana", intervalo_labels or final_ds['intervalo'].values))

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
    """
    Abre múltiplos arquivos GRIB ignorando os que estão vazios ou corrompidos.

    Parâmetros:
    -----------
    files : list
        Lista de caminhos para arquivos GRIB.
    backend_kwargs : dict, opcional
        Argumentos adicionais para o backend 'cfgrib'.
    concat_dim : str, opcional
        Nome da dimensão de concatenação (padrão: 'valid_time').

    Retorna:
    --------
    xarray.Dataset
        Dataset combinado com arquivos válidos.
    """
    backend_kwargs = backend_kwargs or {}
    arquivos_validos = []

    for f in files:
        try:
            ds = xr.open_dataset(f, engine='cfgrib', backend_kwargs=backend_kwargs, decode_timedelta=True,)
            if ds.variables:
                arquivos_validos.append(f)
            else:
                print(f'Arquivo ignorado (sem variáveis): {f}')
        except Exception as e:
            print(f'Erro ao abrir {f}: {e}')

    if not arquivos_validos:
        raise ValueError("Nenhum arquivo válido encontrado.")

    ds_final = xr.open_mfdataset(
        arquivos_validos,
        engine='cfgrib',
        backend_kwargs=backend_kwargs,
        combine='nested',
        concat_dim=concat_dim,
        decode_timedelta=True,
    )

    return ds_final

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
        globals()[varname] = obj.open_model_file(variavel=varname, sel_area=True, **kwargs).load()
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
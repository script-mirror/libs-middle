import pandas as pd
import numpy as np
import pdb
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
import scipy.ndimage as nd
from .utils import (
    get_dado_cacheado,
    ensemble_mean,
    resample_variavel,
    get_inicializacao_fmt,
    ajustar_hora_utc,
    encontra_semanas_operativas,
    gerar_titulo
)

###################################################################################################################

def gerar_prec24h(modelo_fmt, produto_config, tp_params):
    
    try:

        tp = get_dado_cacheado('tp', produto_config, **tp_params)
        tp_mean = ensemble_mean(tp)
        tp_24h = resample_variavel(tp_mean, modelo_fmt, 'tp', '24h')
        cond_ini = get_inicializacao_fmt(tp_mean)

        for n_24h in tp_24h.tempo:
            tp_plot = tp_24h.sel(tempo=n_24h)
            tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(tp_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(tp.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='PREC24HRS', cond_ini=cond_ini,
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=tp_plot['tp'],
                # variavel='tp',
                variavel_plotagem='chuva_ons',
                title=titulo,
                filename=f'tp_24h_{modelo_fmt}_{n_24h.item()}',
            )

    except Exception as e:
        print(f'Erro ao gerar prec24h: {e}')

###################################################################################################################

def gerar_acumulado_total(modelo_fmt, produto_config, tp_params):

    try:

        tp = get_dado_cacheado('tp', produto_config, **tp_params)
        tp_mean = ensemble_mean(tp)

        cond_ini = get_inicializacao_fmt(tp_mean)
        tempo_ini = pd.to_datetime(tp_mean.valid_time.values[0])
        tempo_fim = pd.to_datetime(tp_mean.valid_time.values[-1])

        tp_plot = tp_mean.sum(dim='valid_time')
        titulo = gerar_titulo(
            modelo=modelo_fmt, tipo='Acumulado total', cond_ini=cond_ini,
            data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
            data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
            sem_intervalo_semana=True
        )

        produto_config.plot_campos(
            ds=tp_plot['tp'],
            # variavel='tp',
            variavel_plotagem='acumulado_total',
            title=titulo,
            filename=f'tp_acumulado_total_{modelo_fmt}',
        )

    except Exception as e:
        print(f'Erro ao gerar acumulado total: {e}')

###################################################################################################################

def gerar_semanas_operativas(modelo_fmt, produto_config, tp_params, membros=False):

    try:

        tp = get_dado_cacheado('tp', produto_config, **tp_params)
        
        if membros == False:
            tp_mean = ensemble_mean(tp)
        else:
            tp_mean = tp.copy()

        tp_sop = resample_variavel(tp_mean, modelo_fmt, 'tp', 'sop', qtdade_max_semanas=3)
        cond_ini = get_inicializacao_fmt(tp_mean)

        if membros:
            
            for membro in tp['number']:
                for n_semana in tp_sop.num_semana:
                    tp_plot = tp_sop.sel(num_semana=n_semana).sel(number=membro)
                    intervalo = tp_plot.intervalo.item()
                    intervalo = intervalo.replace(' ', '\ ')
                    days_of_week = tp_plot.days_of_weeks.item()

                    titulo = gerar_titulo(modelo=modelo_fmt, tipo=f'Semana{n_semana.item()}', cond_ini=cond_ini, intervalo=intervalo, days_of_week=days_of_week, semana_operativa=True)

                    produto_config.plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='chuva_ons',
                        title=titulo,
                        filename=f'tp_sop_{modelo_fmt}_semana{n_semana.item()}_{modelo_fmt}_{membro.item()}',
                    )

        else:

            for n_semana in tp_sop.num_semana:
                tp_plot = tp_sop.sel(num_semana=n_semana)
                intervalo = tp_plot.intervalo.item()
                intervalo = intervalo.replace(' ', '\ ')
                days_of_week = tp_plot.days_of_weeks.item()

                titulo = gerar_titulo(modelo=modelo_fmt, tipo=f'Semana{n_semana.item()}', cond_ini=cond_ini, intervalo=intervalo, days_of_week=days_of_week, semana_operativa=True)

                produto_config.plot_campos(
                    ds=tp_plot['tp'],
                    variavel_plotagem='chuva_ons',
                    title=titulo,
                    filename=f'tp_sop_{modelo_fmt}_semana{n_semana.item()}_{modelo_fmt}',
                )

    except Exception as e:
        print(f'Erro ao executar semanas operativas: {e}')

###################################################################################################################

def gerar_prec24hr_pnmm(modelo_fmt, produto_config, tp_params):
    
    try:

        varname = 'msl' if 'ecmwf' in modelo_fmt else 'prmsl'

        # Tp
        tp = get_dado_cacheado('tp', produto_config, **tp_params)
        tp_mean = ensemble_mean(tp)
        tp_24h = resample_variavel(tp_mean, modelo_fmt, 'tp', '24h')
        cond_ini = get_inicializacao_fmt(tp_mean)

        # Pnmm
        pnmm = get_dado_cacheado(varname, produto_config)
        pnmm_mean = ensemble_mean(pnmm)
        pnmm_24h = resample_variavel(pnmm_mean, modelo_fmt, varname, '24h', modo_agrupador='mean')

        for n_24h, p_24h in zip(tp_24h.tempo, pnmm_24h.tempo):

            tp_plot = tp_24h.sel(tempo=n_24h)
            pnmm_plot = pnmm_24h.sel(tempo=p_24h)
            pnmm_plot = nd.gaussian_filter(pnmm_plot[varname]*1e-2, sigma=2)

            tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(tp_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(tp.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='PREC24, PNMM', cond_ini=cond_ini,
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=tp_plot['tp'],
                variavel_plotagem='chuva_ons',
                title=titulo,
                filename=f'tp_24h_pnmm_{modelo_fmt}_{n_24h.item()}',
                ds_contour=pnmm_plot,
                variavel_contour='pnmm'
            )

    except Exception as e:
        print(f'Erro ao gerar prec24hr_pnmm: {e}')

###################################################################################################################

def gerar_jato_div200(modelo_fmt, produto_config, us=None, vs=None):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        # Resample para 24 horas
        us_24h_200 = resample_variavel(us_mean.sel(isobaricInhPa=200), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_200 = resample_variavel(vs_mean.sel(isobaricInhPa=200), modelo_fmt, 'v', '24h', modo_agrupador='mean')

        for n_24h in us_24h_200.tempo:

            us_plot = us_24h_200.sel(tempo=n_24h)
            vs_plot = vs_24h_200.sel(tempo=n_24h)
            vento_jato = (us_plot['u']**2 + vs_plot['v']**2)**0.5
            divergencia = mpcalc.divergence(us_plot['u'], vs_plot['v'])* 1e5  # Convertendo para 1/s
            ds_streamplot = xr.Dataset({'u': us_plot['u'], 'v': vs_plot['v'], 'divergencia': divergencia, 'jato': vento_jato})

            tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(us_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(us.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Vento Jato 200hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=ds_streamplot['jato'],
                variavel_plotagem='wind200',
                title=titulo,
                filename=f'vento_jato_div200_{modelo_fmt}_{n_24h.item()}',
                ds_streamplot=ds_streamplot,
                variavel_streamplot='wind200',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar vento_jato_div200: {e}')

###################################################################################################################

def gerar_geop_500(modelo_fmt, produto_config, geop=None):
    
    try:

        geop = get_dado_cacheado('gh', produto_config)
        geop_mean = ensemble_mean(geop)
        geop_500 = resample_variavel(geop_mean.sel(isobaricInhPa=500), modelo_fmt, 'gh', '24h', modo_agrupador='mean')

        for n_24h in geop_500.tempo:

            geop_plot = geop_500.sel(tempo=n_24h)
            tempo_ini = ajustar_hora_utc(pd.to_datetime(geop_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(geop_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(geop.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Geopotencial 500hPa', cond_ini=get_inicializacao_fmt(geop_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=geop_plot['gh']/10,
                variavel_plotagem='geop_500',
                title=titulo,
                filename=f'geopotencial_500_{modelo_fmt}_{n_24h.item()}',
                ds_contour=geop_plot['gh']/10,
                variavel_contour='gh_500',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar geopotencial 500: {e}')

###################################################################################################################

def gerar_geop_vorticidade_500(modelo_fmt, produto_config, geop=None):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        geop = get_dado_cacheado('gh', produto_config)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        geop_mean = ensemble_mean(geop)
        
        # Resample para 24 horas
        us_24h_500 = resample_variavel(us_mean.sel(isobaricInhPa=500), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_500 = resample_variavel(vs_mean.sel(isobaricInhPa=500), modelo_fmt, 'v', '24h', modo_agrupador='mean')
        geop_500 = resample_variavel(geop_mean.sel(isobaricInhPa=500), modelo_fmt, 'gh', '24h', modo_agrupador='mean')

        for n_24h in geop_500.tempo:

            geop_plot = geop_500.sel(tempo=n_24h)
            tempo_ini = ajustar_hora_utc(pd.to_datetime(geop_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(geop_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(geop.time.values), tempo_ini)[0]

            geop_plot = nd.gaussian_filter(geop_plot['gh'], sigma=3)
            u_plot = us_24h_500.sel(tempo=n_24h)*units.meter_per_second
            v_plot = vs_24h_500.sel(tempo=n_24h)*units.meter_per_second
            vorticidade = mpcalc.vorticity(u_plot['u'], v_plot['v']) * 1e6  # Convertendo para 1/s
            vorticidade = nd.gaussian_filter(vorticidade, sigma=3)
            ds_plot = xr.Dataset({'gh': (('latitude', 'longitude'), geop_plot), 'vorticidade': (('latitude', 'longitude'), vorticidade), 'u': u_plot['u'], 'v': v_plot['v']})

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Vort. e Geop. em 500hPa', cond_ini=get_inicializacao_fmt(geop_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=ds_plot['vorticidade'],
                variavel_plotagem='vorticidade',
                title=titulo,
                filename=f'geop_vorticidade_500_{modelo_fmt}_{n_24h.item()}',
                ds_contour=ds_plot['gh']/10,
                variavel_contour='gh_500',
                plot_bacias=False,
                color_contour='black'
            )

    except Exception as e:
        print(f'Erro ao gerar geopotencial 500: {e}')

###################################################################################################################

def gerar_vento_temp850(modelo_fmt, produto_config):
    
    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        t = get_dado_cacheado('t', produto_config)

        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        t_mean = ensemble_mean(t)

        # Resample para 24 horas
        us_24h_850 = resample_variavel(us_mean.sel(isobaricInhPa=850), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_850 = resample_variavel(vs_mean.sel(isobaricInhPa=850), modelo_fmt, 'v', '24h', modo_agrupador='mean')
        t850_24h = resample_variavel(t_mean.sel(isobaricInhPa=850), modelo_fmt, 't', '24h', modo_agrupador='mean')

        for n_24h in us_24h_850.tempo:

            pdb.set_trace()

            us_plot = us_24h_850.sel(tempo=n_24h)
            vs_plot = vs_24h_850.sel(tempo=n_24h)
            t850_plot = t850_24h.sel(tempo=n_24h)
            ds_quiver = xr.Dataset({
                'u': us_plot['u'],
                'v': vs_plot['v'],
                't850': t850_plot['t']
            })

            tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(us_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(us.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Vento e Temp. em 850hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(
                ds=ds_quiver['t850']-273.15,  # Convertendo de Kelvin para Celsius
                variavel_plotagem='temp850',
                title=titulo,
                filename=f'vento_temp850_{modelo_fmt}_{n_24h.item()}',
                ds_quiver=ds_quiver,
                variavel_quiver='wind850',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar vento e temperatura a 850hPa: {e}')
        return

###################################################################################################################

def gerar_vento850(modelo_fmt, produto_config):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)

        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        # Resample para 24 horas
        us_24h_850 = resample_variavel(us_mean.sel(isobaricInhPa=850), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_850 = resample_variavel(vs_mean.sel(isobaricInhPa=850), modelo_fmt, 'v', '24h', modo_agrupador='mean')

        for n_24h in us_24h_850.tempo:

            pdb.set_trace()

            us_plot = us_24h_850.sel(tempo=n_24h)
            vs_plot = vs_24h_850.sel(tempo=n_24h)
            divergencia = mpcalc.divergence(us_plot['u'], vs_plot['v'])* 1e5  # Convertendo para 1/s
            ds_streamplot = xr.Dataset({
                'u': us_plot['u'],
                'v': vs_plot['v'],
                'divergencia': divergencia
            })

            tempo_ini = ajustar_hora_utc(pd.to_datetime(us_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(us_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(us.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Vento e divergência em 850hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            produto_config.plot_campos(ds=xr.where((divergencia.values >= -1) & (divergencia.values <= 1),divergencia,np.nan),variavel_plotagem='divergencia850',title=titulo,filename=f'vento850_{modelo_fmt}_{n_24h.item()}',ds_streamplot=ds_streamplot,variavel_streamplot='wind850',plot_bacias=False)

    except Exception as e:
        print(f'Erro ao gerar vento e temperatura a 850hPa: {e}')
        return

###################################################################################################################

def gerar_chuva_geop500_vento850(modelo_fmt, produto_config, tp_params, produto_config_sf=None):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        gh = get_dado_cacheado('gh', produto_config)
        tp = get_dado_cacheado('tp', produto_config, **tp_params) if produto_config_sf is None else get_dado_cacheado('tp', produto_config_sf, **tp_params)

        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        gh_mean = ensemble_mean(gh)
        tp_mean = ensemble_mean(tp)

        for index, n_24h in enumerate(tp_mean.valid_time):

            pdb.set_trace()

            us_plot = us_mean.sel(valid_time=n_24h)
            vs_plot = vs_mean.sel(valid_time=n_24h)
            gh_plot = gh_mean.sel(valid_time=n_24h)
            tp_plot = tp_mean.sel(valid_time=n_24h)

            ds_quiver = xr.Dataset({
                'u': us_plot['u'].sel(isobaricInhPa=850).drop_vars('isobaricInhPa'), 
                'v': vs_plot['v'].sel(isobaricInhPa=850).drop_vars('isobaricInhPa'), 
                'geop_500': gh_plot['gh'].sel(isobaricInhPa=500).drop_vars('isobaricInhPa') / 10,
                'tp': tp_plot['tp']
            })

            tempo_ini = ajustar_hora_utc(pd.to_datetime(n_24h.item()))
            semana = encontra_semanas_operativas(pd.to_datetime(us.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Prec6h, Geo500hPa, Vento850hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana, unico_tempo=True
            )

            produto_config.plot_campos(ds=ds_quiver['tp'], variavel_plotagem='wind_prec_geop', title=titulo, filename=f'vento850_prec_geop500_{modelo_fmt}_{index}', 
                                       plot_bacias=False, ds_quiver=ds_quiver, variavel_quiver='wind850', ds_contour=ds_quiver['geop_500'], variavel_contour='gh_500', color_contour='black')

    except Exception as e:
        print(f'Erro ao gerar chuva, geopotencial e vento a 850hPa: {e}')
        return
    
###################################################################################################################

def gerar_ivt(modelo_fmt, produto_config):

    try:

        gh = get_dado_cacheado('gh', produto_config)
        qs = get_dado_cacheado('q', produto_config)
        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)

        gh_mean = ensemble_mean(gh).sel(isobaricInhPa=700)
        qs_mean = ensemble_mean(qs).sel(isobaricInhPa=slice(1000, 300))
        us_mean = ensemble_mean(us).sel(isobaricInhPa=slice(1000, 300))
        vs_mean = ensemble_mean(vs).sel(isobaricInhPa=slice(1000, 300))

        # Resample para 24 horas
        gh_24h = resample_variavel(gh_mean, modelo_fmt, 'gh', '24h', modo_agrupador='mean')
        qs_24h = resample_variavel(qs_mean, modelo_fmt, 'q', '24h', modo_agrupador='mean')
        us_24h = resample_variavel(us_mean, modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h = resample_variavel(vs_mean, modelo_fmt, 'v', '24h', modo_agrupador='mean')

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

            tempo_ini = ajustar_hora_utc(pd.to_datetime(gh_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(gh_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(gh.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo='Geop 700hPa e TIWV (1000-300)', cond_ini=get_inicializacao_fmt(gh_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            pdb.set_trace()

            produto_config.plot_campos(
                ds=ds_quiver['ivt']*100,
                variavel_plotagem='ivt',
                title=titulo,
                filename=f'ivt_geop700_{modelo_fmt}_{n_24h.item()}',
                ds_quiver=ds_quiver,
                variavel_quiver='ivt',
                ds_contour=ds_quiver['gh_700'],
                variavel_contour='gh_700',
                plot_bacias=False,
                color_contour='black'
            )

    except Exception as e:
        print(f'Erro ao gerar Geop 700hPa e TIWV (1000-300): {e}')
        return
    
###################################################################################################################
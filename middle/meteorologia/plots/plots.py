import pandas as pd
import numpy as np
import pdb
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
import scipy.ndimage as nd
from ..utils.utils import (
    get_dado_cacheado,
    ensemble_mean,
    resample_variavel,
    get_inicializacao_fmt,
    ajustar_hora_utc,
    encontra_semanas_operativas,
    gerar_titulo
)
import matplotlib
matplotlib.use('Agg')  # Backend para geração de imagens, sem interface gráfica
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap
import os

###################################################################################################################

# --- BASE DO MAPA ---
def get_base_ax(extent, figsize, central_longitude=0):

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

###################################################################################################################

# --- COLOR BARS ---
def custom_colorbar(variavel_plotagem):

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

###################################################################################################################

# --- PLOT DE VARIÁVEIS ---
def plot_campos(
                ds, 
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
                color_contour='white',
                shapefiles=None
):

    os.makedirs(path_to_save, exist_ok=True)

    # Importando constantes e funções auxiliares
    from ..consts.namelist import CONSTANTES

    extent = tuple(extent)
    figsize = tuple(figsize)
    fig, ax = get_base_ax(extent=extent, figsize=figsize, central_longitude=central_longitude)
    levels, colors, cmap = custom_colorbar(variavel_plotagem)

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
    label = [k for k, v in CONSTANTES['labels_variaveis'].items() if variavel_plotagem in v]
    if label:
        label = label[0]

    if posicao_colorbar == 'vertical':
        axins = inset_axes(ax, width="3%", height="100%", loc='right', borderpad=-2.7)
        fig.colorbar(cf, cax=axins, orientation='vertical', label=label, ticks=levels, extendrect=True)

    elif posicao_colorbar == 'horizontal':
        axins = inset_axes(ax, width="95%", height="2%", loc='lower center', borderpad=-3.6)
        fig.colorbar(cf, cax=axins, orientation='horizontal', ticks=levels if len(levels)<=26 else levels[::2], extendrect=True, label=label)

    if shapefiles is not None:
        for gdf in shapefiles.values():
            if 'Nome_Bacia' in gdf.columns:
                if plot_bacias:
                    gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)
            else:
                gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)

    plt.savefig(f'{path_to_save}/{filename}.png', bbox_inches='tight')
    plt.close(fig)

###################################################################################################################

# --- Geração de precipitação acumulada em 24 horas ---
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

            plot_campos(
                ds=tp_plot['tp'],
                # variavel='tp',
                variavel_plotagem='chuva_ons',
                title=titulo,
                filename=f'tp_24h_{modelo_fmt}_{n_24h.item()}',
            )

    except Exception as e:
        print(f'Erro ao gerar prec24h: {e}')

###################################################################################################################

# --- Geração de precipitação acumulada total ---
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

        plot_campos(
            ds=tp_plot['tp'],
            # variavel='tp',
            variavel_plotagem='acumulado_total',
            title=titulo,
            filename=f'tp_acumulado_total_{modelo_fmt}',
        )

    except Exception as e:
        print(f'Erro ao gerar acumulado total: {e}')

###################################################################################################################

# --- Geração de semanas operativas ---
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

                    plot_campos(
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

                plot_campos(
                    ds=tp_plot['tp'],
                    variavel_plotagem='chuva_ons',
                    title=titulo,
                    filename=f'tp_sop_{modelo_fmt}_semana{n_semana.item()}_{modelo_fmt}',
                )

    except Exception as e:
        print(f'Erro ao executar semanas operativas: {e}')

###################################################################################################################

# --- Geração de precipitação acumulada em 24 horas com PNMM ---
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

            plot_campos(
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

# --- Geração de vento jato e divergência a 200hPa ---
def gerar_jato_div200(modelo_fmt, produto_config, us=None, vs=None, level_divergencia=200):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        # Resample para 24 horas
        us_24h_200 = resample_variavel(us_mean.sel(isobaricInhPa=level_divergencia), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_200 = resample_variavel(vs_mean.sel(isobaricInhPa=level_divergencia), modelo_fmt, 'v', '24h', modo_agrupador='mean')

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
                modelo=modelo_fmt, tipo=f'Vento Jato {level_divergencia}hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            plot_campos(
                ds=ds_streamplot['jato'],
                variavel_plotagem='wind200',
                title=titulo,
                filename=f'vento_jato_div{level_divergencia}_{modelo_fmt}_{n_24h.item()}',
                ds_streamplot=ds_streamplot,
                variavel_streamplot='wind200',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar vento_jato_div200: {e}')

###################################################################################################################

# --- Geração de geopotencial a 500hPa ---
def gerar_geop_500(modelo_fmt, produto_config, geop=None, level_geop=500):
    
    try:

        geop = get_dado_cacheado('gh', produto_config)
        geop_mean = ensemble_mean(geop)
        geop_500 = resample_variavel(geop_mean.sel(isobaricInhPa=level_geop), modelo_fmt, 'gh', '24h', modo_agrupador='mean')

        for n_24h in geop_500.tempo:

            geop_plot = geop_500.sel(tempo=n_24h)
            tempo_ini = ajustar_hora_utc(pd.to_datetime(geop_plot.data_inicial.item()))
            tempo_fim = pd.to_datetime(geop_plot.data_final.item())
            semana = encontra_semanas_operativas(pd.to_datetime(geop.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo=f'Geopotencial {level_geop}hPa', cond_ini=get_inicializacao_fmt(geop_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            plot_campos(
                ds=geop_plot['gh']/10,
                variavel_plotagem='geop_500',
                title=titulo,
                filename=f'geopotencial_{level_geop}_{modelo_fmt}_{n_24h.item()}',
                ds_contour=geop_plot['gh']/10,
                variavel_contour='gh_500',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar geopotencial 500: {e}')

###################################################################################################################

# --- Geração de vorticidade e geopotencial a 500hPa ---
def gerar_geop_vorticidade_500(modelo_fmt, produto_config, geop=None, level_geop=500):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        geop = get_dado_cacheado('gh', produto_config)
        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        geop_mean = ensemble_mean(geop)
        
        # Resample para 24 horas
        us_24h_500 = resample_variavel(us_mean.sel(isobaricInhPa=level_geop), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_500 = resample_variavel(vs_mean.sel(isobaricInhPa=level_geop), modelo_fmt, 'v', '24h', modo_agrupador='mean')
        geop_500 = resample_variavel(geop_mean.sel(isobaricInhPa=level_geop), modelo_fmt, 'gh', '24h', modo_agrupador='mean')

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
                modelo=modelo_fmt, tipo=f'Vort. e Geop. em {level_geop}hPa', cond_ini=get_inicializacao_fmt(geop_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            plot_campos(
                ds=ds_plot['vorticidade'],
                variavel_plotagem='vorticidade',
                title=titulo,
                filename=f'geop_vorticidade_{level_geop}_{modelo_fmt}_{n_24h.item()}',
                ds_contour=ds_plot['gh']/10,
                variavel_contour='gh_500',
                plot_bacias=False,
                color_contour='black'
            )

    except Exception as e:
        print(f'Erro ao gerar geopotencial 500: {e}')

###################################################################################################################

# --- Geração de vento e temperatura a 850hPa ---
def gerar_vento_temp850(modelo_fmt, produto_config, level_temp=850):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)
        t = get_dado_cacheado('t', produto_config)

        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)
        t_mean = ensemble_mean(t)

        # Resample para 24 horas
        us_24h_850 = resample_variavel(us_mean.sel(isobaricInhPa=level_temp), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_850 = resample_variavel(vs_mean.sel(isobaricInhPa=level_temp), modelo_fmt, 'v', '24h', modo_agrupador='mean')
        t850_24h = resample_variavel(t_mean.sel(isobaricInhPa=level_temp), modelo_fmt, 't', '24h', modo_agrupador='mean')

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
                modelo=modelo_fmt, tipo=f'Vento e Temp. em {level_temp}hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            plot_campos(
                ds=ds_quiver['t850']-273.15,  # Convertendo de Kelvin para Celsius
                variavel_plotagem='temp850',
                title=titulo,
                filename=f'vento_temp{level_temp}_{modelo_fmt}_{n_24h.item()}',
                ds_quiver=ds_quiver,
                variavel_quiver='wind850',
                plot_bacias=False
            )

    except Exception as e:
        print(f'Erro ao gerar vento e temperatura a 850hPa: {e}')
        return

###################################################################################################################

# --- Geração de vento e divergência a 850hPa ---
def gerar_vento850(modelo_fmt, produto_config, level_vento=850):

    try:

        us = get_dado_cacheado('u', produto_config)
        vs = get_dado_cacheado('v', produto_config)

        us_mean = ensemble_mean(us)
        vs_mean = ensemble_mean(vs)

        if us_mean.longitude.min() >= 0:
            us_mean = us_mean.assign_coords(longitude=(((us_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')
            vs_mean = vs_mean.assign_coords(longitude=(((vs_mean.longitude + 180) % 360) - 180)).sortby('longitude').sortby('latitude')

        # Resample para 24 horas
        us_24h_850 = resample_variavel(us_mean.sel(isobaricInhPa=level_vento), modelo_fmt, 'u', '24h', modo_agrupador='mean')
        vs_24h_850 = resample_variavel(vs_mean.sel(isobaricInhPa=level_vento), modelo_fmt, 'v', '24h', modo_agrupador='mean')

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
                modelo=modelo_fmt, tipo=f'Vento e divergência em {level_vento}hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana
            )

            plot_campos(ds=xr.where((divergencia.values >= -1) & (divergencia.values <= 1),divergencia,np.nan),variavel_plotagem='divergencia850',title=titulo,filename=f'vento{level_vento}_{modelo_fmt}_{n_24h.item()}',ds_streamplot=ds_streamplot,variavel_streamplot='wind850',plot_bacias=False)

    except Exception as e:
        print(f'Erro ao gerar vento e temperatura a 850hPa: {e}')
        return

###################################################################################################################

# --- Geração de precipitação, geopotencial e vento a 850hPa ---
def gerar_chuva_geop500_vento850(modelo_fmt, produto_config, tp_params, produto_config_sf=None, level_vento=850, level_geop=500):

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
                'u': us_plot['u'].sel(isobaricInhPa=level_vento).drop_vars('isobaricInhPa'), 
                'v': vs_plot['v'].sel(isobaricInhPa=level_vento).drop_vars('isobaricInhPa'), 
                'geop_500': gh_plot['gh'].sel(isobaricInhPa=level_geop).drop_vars('isobaricInhPa') / 10,
                'tp': tp_plot['tp']
            })

            tempo_ini = ajustar_hora_utc(pd.to_datetime(n_24h.item()))
            semana = encontra_semanas_operativas(pd.to_datetime(us.time.values), tempo_ini)[0]

            titulo = gerar_titulo(
                modelo=modelo_fmt, tipo=f'Prec6h, Geo{level_geop}hPa, Vento{level_vento}hPa', cond_ini=get_inicializacao_fmt(us_mean),
                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                semana=semana, unico_tempo=True
            )

            plot_campos(ds=ds_quiver['tp'], variavel_plotagem='wind_prec_geop', title=titulo, filename=f'vento{level_vento}_prec_geop{level_geop}_{modelo_fmt}_{index}', 
                                       plot_bacias=False, ds_quiver=ds_quiver, variavel_quiver='wind850', ds_contour=ds_quiver['geop_500'], variavel_contour='gh_500', color_contour='black')

    except Exception as e:
        print(f'Erro ao gerar chuva, geopotencial e vento a 850hPa: {e}')
        return
    
###################################################################################################################

# --- Geração de IVT (Integrated Vapor Transport) ---
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

            plot_campos(
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

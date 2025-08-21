import pandas as pd
import numpy as np
import xarray as xr
import requests
import metpy.calc as mpcalc
from middle.utils import Constants
from metpy.units import units
import pdb
import scipy.ndimage as nd
from ..utils.utils import (
    get_dado_cacheado,
    ensemble_mean,
    resample_variavel,
    get_inicializacao_fmt,
    ajustar_hora_utc,
    encontra_semanas_operativas,
    gerar_titulo,
    encontra_casos_frentes_xarray,
    skip_zero_formatter,
    interpola_ds,
    get_df_ons,
    calcula_media_bacia,
    converter_psat_para_cd_subbacia,
    calcula_psi_chi,
    open_hindcast_file,
    ajusta_lon_0_360,
    ajusta_acumulado_ds,
    ajusta_shp_json,
    get_prec_db,
    get_pontos_localidades
)
from ..consts.constants import CONSTANTES
from middle.utils import get_auth_header
import matplotlib

matplotlib.use('Agg')  # Backend para geração de imagens, sem interface gráfica
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as mticker
import os
import warnings
warnings.filterwarnings("ignore")

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
        cbar_ticks = None

    elif variavel_plotagem in ['tp_anomalia']:
        colors = ['mediumvioletred', 'maroon', 'firebrick', 'red', 'chocolate', 'orange', 'gold', 'yellow', 'white', 'aquamarine', 'mediumturquoise', 'cyan', 'lightblue', 'blue', 'purple', 'mediumpurple', 'blueviolet']
        levels = range(-150, 155, 5)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = [-150, -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125, 150]

    elif variavel_plotagem in ['dif_prev']:
        colors = ['#FF0000', '#Ffa500', '#FFFFFF', '#FFFFFF', '#0000ff', '#800080']
        levels = np.arange(-50, 55, 5)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem in ['pct_climatologia']:
        colors = ['firebrick', 'red', 'orange', 'yellow', 'white', 'aquamarine', 'mediumturquoise', 'cyan', 'lightblue', 'blue', 'purple', 'mediumpurple', 'blueviolet']
        levels = range(0, 305, 5)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = levels[::4]   

    elif variavel_plotagem in ['psi']:
        levels = np.arange(-30, 30.2, 0.2)
        colors = ['maroon', 'darkred', 'red', 'orange', 'yellow', 'white', 'cyan', 'dodgerblue', 'blue', 'darkblue', 'indigo']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem in ['geop_500_anomalia']:
        levels = range(-40, 42, 2)
        colors = ['darkblue', 'blue', 'white', 'red', 'darkred']
        cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(cmap, len(levels))    
        cbar_ticks = None     

    elif variavel_plotagem == 'frentes':
        levels = list(range(0, 6))
        colors = [
            "#ffffff",  # 0 - branco
            "#fee391",  # 1 - amarelo claro
            "#fec44f",  # 2 - laranja claro
            "#fe9929",  # 3 - laranja médio
            "#ec7014",  # 4 - laranja escuro
            "#cc4c02",  # 5 - vermelho-laranja
        ]
        cmap = None       
        cbar_ticks = None 

    elif variavel_plotagem == 'frentes_anomalia':
        levels = [-3, -2, -1, 0, 1, 2, 3]
        colors = [
            "#b2182b",  # -3 - vermelho escuro
            "#ef8a62",  # -2 - vermelho claro
            "#ffffff",  # -1 - bege rosado
            "#ffffff",  #  0 - branco
            "#d1e5f0",  # +1 - azul claro
            "#67a9cf",  # +2 - azul médio
            "#2166ac",  # +3 - azul escuro
        ]
        cmap = None   
        cbar_ticks = None

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
        cbar_ticks = None

    elif variavel_plotagem == 'wind200':
        colors = ['#FFFFFF','#FFFFC1','#EBFF51','#ACFE53','#5AFD5B','#54FCD2','#54DBF5','#54ACFC', '#4364FC','#2F29ED','#3304BC','#440499']
        levels = np.arange(40, 85, 2)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)
        cbar_ticks = None

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
        cbar_ticks = None

    elif variavel_plotagem == 'vorticidade':
        levels = range(-100, 110, 10)
        colors = None
        cmap = plt.get_cmap('RdBu_r', len(levels)  + 1)
        cbar_ticks = None

    elif variavel_plotagem == 'temp850':
        levels = np.arange(-14, 34, 1)
        colors = ['#8E27BA','#432A98','#1953A8','#148BC1','#15B3A4', '#16C597','#77DE75','#C5DD47','#F5BB1A','#F0933A','#EF753D',
        '#F23B39', '#C41111', '#8D0A0A']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)
        cbar_ticks = None

    elif variavel_plotagem == 'temp_anomalia':
        levels = np.arange(-5, 5.1, 0.1)
        colors = None
        cmap = 'RdBu_r'
        cbar_ticks = np.arange(-5, 5.5, 0.5)

    elif variavel_plotagem == 'divergencia850':
        levels = np.arange(-5, 6, 1)
        colors = None
        cmap = plt.get_cmap('RdBu_r', len(levels)  + 1)
        cbar_ticks = None

    elif variavel_plotagem == 'ivt':
        colors = ['white', 'yellow', 'orange', 'red', 'gray']
        levels = np.arange(250, 1650, 50)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem == 'wind_prec_geop':
        levels = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 35]
        colors = ["#ffffff", '#00004C', '#003862',
                '#001D7E', '#004C98', '#0066AD', 
                '#009BDB', '#77BAE8', '#9ED7FF',
                '#F6E5BD', '#F1E3A0', '#F3D98B',
                '#F5C96C', '#EFB73F', '#EA7B32',
                '#D75C12', '#BF0411']
        cmap = None
        cbar_ticks = None

    elif variavel_plotagem == 'diferenca':
        levels = range(-100, 110, 10)
        colors = ['mediumvioletred', 'maroon', 'firebrick', 
                  'red', 'chocolate', 'orange', 'gold', 
                  'yellow', 'white', 'white', 'aquamarine', 
                  'mediumturquoise', 'cyan', 'lightblue', 'blue', 
                  'purple', 'mediumpurple', 'blueviolet']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem in ['probabilidade', 'desvpad']:
        levels = range(0, 110, 10)
        colors = ['white', 'yellow', 'lightgreen', 'green', 'blue', 'purple']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem == 'geada-inmet':
        levels = [-100, -8, -3, -1, 100]
        colors = ['#FFFFFF','#D2CBEB','#6D55BF','#343396']
        cmap = None
        cbar_ticks = None

    elif variavel_plotagem == 'geada-cana':
        levels = [-100, -5, -3.5, -2, 100]
        colors = ['#FFFFFF','#D2CBEB','#6D55BF','#343396']
        cmap = None
        cbar_ticks = None

    elif variavel_plotagem == 'olr':
        levels = range(200, 410, 10)
        colors = None
        cmap = 'plasma' 
        cbar_ticks = None       

    elif variavel_plotagem == 'mag_vento100':
        levels = np.arange(1, 20, 1)
        colors = ['#FFFFFF','#FFFFC1','#EBFF51','#ACFE53','#5AFD5B','#54FCD2','#54DBF5','#54ACFC', '#4364FC','#2F29ED','#3304BC','#440499']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)
        cbar_ticks = None

    return levels, colors, cmap, cbar_ticks

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
                shapefiles=None,
                margin_x = -50,
                margin_y = -10,
                add_valor_bacias=False,
    ):

    os.makedirs(path_to_save, exist_ok=True)

    # Importando constantes e funções auxiliares
    from ..consts.constants import CONSTANTES
    from PIL import Image

    extent = tuple(extent)
    figsize = tuple(figsize)
    fig, ax = get_base_ax(extent=extent, figsize=figsize, central_longitude=central_longitude)
    levels, colors, cmap, cbar_ticks = custom_colorbar(variavel_plotagem)

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

        elif variavel_contour == 'frentes':
            contour_levels = [lvl for lvl in levels if lvl != 0]
            cf2 = ax.contour(lon, lat, ds_contour, transform=ccrs.PlateCarree(), colors='black', linestyles='solid', levels=contour_levels, linewidths=0.5)
            plt.clabel(cf2, inline=True, fmt=mticker.FuncFormatter(lambda x, _: skip_zero_formatter(x)), fontsize=10)

        elif variavel_contour == 'psi':
            cf2 = ax.contour(lon, lat, ds_contour, transform=ccrs.PlateCarree(), colors='black', linestyles='solid', levels=np.arange(-4, 14, 2))
            plt.clabel(cf2, inline=True, fmt='%.0f', fontsize=10, colors=color_contour)            

        elif variavel_contour == 'olr':
            cf2 = ax.contour(lon, lat, ds_contour, transform=ccrs.PlateCarree(), colors='black', linestyles='solid', levels=np.arange(220, 250, 10))
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
            ax.streamplot(lon, lat, u.data, v.data, linewidth=1.5, arrowsize=1, density=2.5, color='black')

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
        cb = fig.colorbar(cf, cax=axins, orientation='vertical', label=label, ticks=levels, extendrect=True)

    elif posicao_colorbar == 'horizontal':
        axins = inset_axes(ax, width="95%", height="2%", loc='lower center', borderpad=-3.6)
        cb = fig.colorbar(cf, cax=axins, orientation='horizontal', ticks=levels if len(levels)<=26 else levels[::2], extendrect=True, label=label)

    if cbar_ticks is not None:
        cb.set_ticks(cbar_ticks)

    # Apenas para geada
    if variavel_plotagem == 'geada':
        midpoints = [(levels[j] + levels[j + 1]) / 2 for j in range(len(levels) - 1)]
        cb.set_ticks(midpoints)
        cb.set_ticklabels(['Sem risco', 'Fraca', 'Moderada', 'Forte'])

        # Polos de Biomassa        
        la = [-21.21,-21.77,-22.66,-22.35,-17.84,-22.36,-22.63,-22.73,-21.18]
        lo = [-50.43, -48.18,-50.4, -48.1, -51.73,-48.69,-54.82,-47.65,-47.82]
        lo = [x+360 for x in lo]
        cores = ['#70279C', '#AE9AD4', '#757575', '#CF2664', '#0BAAF2', '#80CFF3', '#FF8F00', '#FDD835', '#E78CAB']
        marcador = 'o'
        ax.scatter(lo, la, marker=marcador, edgecolor=cores, facecolors=cores,s=50)

    if shapefiles is not None:
        for shapefile in shapefiles:
            gdf = gpd.read_file(shapefile)
            if 'Nome_Bacia' in gdf.columns:
                if plot_bacias:
                    gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)
            else:
                gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5)

    if add_valor_bacias:

        # criando a var para tp no dataset se nao existir, o valor será o mesmo
        ds = ds.to_dataset()
        if 'tp' not in ds.data_vars:
            varname = list(ds.data_vars.keys())[0]  # pega o primeiro nome de variável
            ds = ds.rename({varname: "tp"})

        # Abrindo o json arrumado
        shp = ajusta_shp_json()

        chuva_media = []
        for lat, lon, bacia, codigo in zip(shp['lat'], shp['lon'], shp['nome'], shp['cod']):
            chuva_media.append(calcula_media_bacia(ds, lat, lon, bacia, codigo, shp))

        df = xr.concat(chuva_media, dim='id').to_dataframe().reset_index()
        df = df.rename(columns={'id': 'cod_psat'})
        df_ons = get_df_ons()
        df = pd.merge(df, df_ons, on='cod_psat', how='left')
        media_bacia = df.groupby(['nome_bacia'])[['tp', 'vl_lat', 'vl_lon']].mean().reset_index()
        bacias_para_plotar = [
            'grande',
            'iguaçu',
            'itaipu',
            'jacuí',
            'madeira',
            'paranapane',
            'paranaíba',
            'tietê',
            'uruguai',
            'paraná',
            'xingu',
            'tocantins',
            'são franci',
        ]

        # Itera sobre as bacias e adiciona as anotações no mapa
        for idx, row in media_bacia.iterrows():

            if row['nome_bacia'].lower() in bacias_para_plotar:

                # if media_bacia['tp'].min() > 0:
                #     color='black'
                # else:
                #     if row['tp'] > 0:
                #         color='green'
                #     else:
                #         color='purple'

                if not np.isnan(row['tp']):  # Garante que há valor para exibir
                    lon, lat = row["vl_lon"], row["vl_lat"]  # Extrai coordenadas do centroide
                    lon = lon+360
                    ax.text(lon, lat, f"{row['tp']:.0f}", fontsize=11, color='black', fontweight='bold', ha='center', va='center', transform=ccrs.PlateCarree())
                            # bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')c
                            # )

    # Logo
    img = Image.open(Constants().LOGO_RAIZEN)
    im_width, _ = img.size
    bbox = plt.gca().get_window_extent()
    xo = bbox.x1 - im_width + margin_x
    yo = bbox.y0 + margin_y
    plt.figimage(img, xo=xo, yo=yo, alpha=0.3)

    plt.savefig(f'{path_to_save}/{filename}.png', bbox_inches='tight')
    plt.close(fig)

    return

###################################################################################################################

# --- PLOT GRÁFICOS PREVISAO BACIAS SMAP ---
def plot_chuva_acumulada(
    df_merged,
    mes,
    dt_inicial,
    dt_final,
    dt_inicial_prev,
    df_final_prev,
    modelo_obs,
    modelo_prev,
    dt_rodada,
    path_to_save,
    index,
    mes_fmt_svg,
    com_climatologia=True,
    logo_path=Constants().LOGO_RAIZEN,
    margin_x=110,
    margin_y=100
):
    
    from PIL import Image

    """
    Plota gráfico de precipitação acumulada (observado + previsão) e salva como PNG.

    Parâmetros
    ----------
    df_merged : DataFrame
        Deve conter colunas 'str_bacia', 'chuva_acumulada', 'vl_chuva' e opcionalmente 'climatologia'.
    mes : int
        Mês de referência para verificar se inclui observações.
    dt_inicial, dt_final : datetime
        Período observado.
    dt_inicial_prev, df_final_prev : str
        Período de previsão (formatado como string para exibir no título).
    modelo_obs, modelo_prev : str
        Nomes dos modelos.
    dt_rodada : str
        Data da rodada do modelo.
    hr_rodada : str
        Hora da rodada do modelo.
    path_to_save : str
        Caminho para salvar o arquivo PNG.
    index : str
        Nome identificador do gráfico.
    mes_fmt_svg : str
        Formato de mês para o nome do arquivo.
    com_climatologia : bool
        Se True, plota linha de climatologia.
    logo_path : str
        Caminho para o logo a ser sobreposto.
    margin_x, margin_y : int
        Margens para posicionamento do logo.
    """

    fig, ax = plt.subplots(figsize=(12, 6))
    width = 0.6
    indices = [x.title() for x in df_merged['str_bacia']]

    if mes == pd.to_datetime(dt_final).month:
        ax.bar(indices, df_merged["chuva_acumulada"], width=width, color="gray", alpha=0.8,
               label=f"Observado {dt_inicial.strftime('%d/%m')} a {dt_final.strftime('%d/%m')}")
        ax.bar(indices, df_merged["vl_chuva"], width=width, bottom=df_merged["chuva_acumulada"], color="blue", alpha=0.7,
               label=f'{modelo_prev.upper()} {dt_inicial_prev} a {df_final_prev}')
    else:
        ax.bar(indices, df_merged["vl_chuva"], width=width, color="blue", alpha=0.7,
               label=f'{modelo_prev.upper()} {dt_inicial_prev} a {df_final_prev}')

    # Texto nas barras
    for i in range(len(df_merged)):
        obs = df_merged.loc[i, "chuva_acumulada"] if mes == pd.to_datetime(dt_final).month else 0
        prev = df_merged.loc[i, "vl_chuva"]
        total = obs + prev
        ax.text(i, total + 1, f"{total:.0f}", ha="center", va="bottom", fontsize=9)
        ax.text(i, 2, f"{obs:.0f}", ha="center", va="bottom", fontsize=9)

    # Climatologia
    if com_climatologia and "climatologia" in df_merged.columns:
        ax.plot(indices, df_merged["climatologia"], color="orange", marker="o", linestyle="-", linewidth=2,
                label="Climatologia total MERGE")
        for i, val in enumerate(df_merged["climatologia"]):
            ax.text(i, val + 2, f"{val:.0f}", ha="center", va="bottom", fontsize=8, color="orange")

    ax.set_ylabel("Precipitação (mm)")

    if mes == pd.to_datetime(dt_final).month:
        ax.set_title(f'Precipitação Acumulada: {modelo_obs.upper()} + {modelo_prev.upper()} {dt_rodada}',
                     fontsize=14, fontweight='bold', loc='left')
        ax.set_title(f"De {dt_inicial.strftime('%d/%m')} até {df_final_prev}", fontsize=12, loc='right', fontweight='bold')
    else:
        ax.set_title(f'Precipitação Acumulada: {modelo_prev.upper()} {dt_rodada}',
                     fontsize=14, fontweight='bold', loc='left')
        ax.set_title(f'De {dt_inicial_prev} até {df_final_prev}', fontsize=12, loc='right', fontweight='bold')

    ax.set_xticks(range(len(indices)))
    ax.set_xticklabels(indices, rotation=90)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Logo
    img = Image.open(logo_path)
    im_width, _ = img.size
    bbox = plt.gca().get_window_extent()
    xo = bbox.x1 - im_width + margin_x
    yo = bbox.y0 + margin_y
    plt.figimage(img, xo=xo, yo=yo, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{path_to_save}/{index}_chuva_acumulada_{modelo_prev.upper()}_{dt_rodada}_{mes_fmt_svg}.png", bbox_inches="tight")
    plt.close(fig)

###################################################################################################################

# --- PLOT CHUVA A PARTIR DE UM GEODATAFRAME ---
def plot_df_to_mapa(df, path_to_save='./tmp/plots', filename='filename', column_plot='dif', type='dif', titulo=None, shapefiles=None):

    from PIL import Image

    # Agrupando por bacia
    media_bacia = df.groupby('nome_bacia')[column_plot].mean()
    media_bacia = media_bacia.rename({'Paranapane':'Paranapanema', 'São Franci':'São Francisco', 'Jequitinho':'Jequitinhonha'})

    fig, ax = get_base_ax(extent=[280, 330, -35, 10], figsize=(12, 12), central_longitude=0)

    # Titulo
    ax.set_title(titulo, loc='left', fontsize=16)

    # Barra de cor
    levels, colors, cmap, cbar_ticks = custom_colorbar('dif_prev')
    norm = matplotlib.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

    if shapefiles is not None:
        for shapefile in shapefiles:
            gdf = gpd.read_file(shapefile)
            if 'Nome_Bacia' in gdf.columns:
                shp = gdf.copy()

    shp = shp.rename(columns={'Nome_Bacia': 'nome_bacia'})
    shp = shp.merge(media_bacia, on="nome_bacia", how="left")
    shp["centroid"] = shp.geometry.centroid
    shp.plot(ax=ax, transform=ccrs.PlateCarree(), edgecolor='black', alpha=0.8, linewidths=1.2, facecolor = 'none', zorder=10)

    # Plota o GeoDataFrame no eixo do Cartopy
    df.plot(column=column_plot, legend=False, lw=0, legend_kwds={'extend':'both'}, ax=ax, cmap=cmap, norm=norm, ec='black')

    # Itera sobre as bacias e adiciona as anotações no mapa
    for idx, row in shp.iterrows():
        if not np.isnan(row[column_plot]):  # Garante que há valor para exibir
            lon, lat = row["centroid"].x, row["centroid"].y  # Extrai coordenadas do centroide

            if row['nome_bacia'] == 'Uruguai': # Caso especial para o uruguai
                lat = lat + 1
                lon = lon + 2
            
            ax.text(lon, lat, f"{row[column_plot]:.0f}", 
                    fontsize=15, color='black', fontweight='bold',
                    ha='center', va='center', transform=ccrs.PlateCarree(),
                    # bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
                    )

    # Escala de cores
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []  # necessário para ScalarMappable
    axins = inset_axes(ax, width="95%", height="2.5%", loc='lower center', borderpad=-3.6)
    fig.colorbar(sm, cax=axins, orientation='horizontal', ticks=levels, extendrect=True)

    # Labels dos ticks de lat e lon
    gl = ax.gridlines(xlocs=np.arange(-120, 0, 10), ylocs=np.arange(-55, 25, 10), draw_labels=True, alpha=0, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    # Adicionando o logo
    margin_x = -100
    margin_y = -60
    img = Image.open(Constants().LOGO_RAIZEN)
    im_width, im_height = img.size

    # Obtém o retângulo da figura atual
    bbox = plt.gca().get_window_extent()
    xo = bbox.x1 - im_width + margin_x
    yo = bbox.y0 + margin_y
    plt.figimage(img, xo=xo, yo=yo)

    if type == 'dif':
        # Adiciona "Vermelho: Subestimativa da previsão" no topo em vermelho
        ax.annotate("Vermelho:", xy=(0.58, 0.92), xycoords='axes fraction', fontsize=12, fontweight='bold', color='red')

        ax.annotate(" Subestimativa da previsão", xy=(0.68, 0.92), xycoords='axes fraction', fontsize=12, fontweight='bold', color='black')

        # Adiciona "Azul: Superestimativa da previsão" no topo em azul
        ax.annotate("Azul:", xy=(0.58, 0.89), xycoords='axes fraction', fontsize=12, fontweight='bold', color='blue')

        ax.annotate("  Superestimativa da previsão", xy=(0.62, 0.89), xycoords='axes fraction', fontsize=12, fontweight='bold', color='black')

    # filename = filename + '_' + dt_observada_fmt.replace('/', '')
    plt.savefig(f'{path_to_save}/{filename}.png', bbox_inches='tight')
    plt.close()

###################################################################################################################

# --- PLOT GRÁFICOS PREVISAO 2D ---
def plot_graficos_2d(df: pd.DataFrame, tipo: str, df_tmin=None, titulo=None, filename='grafico'):

    plt.figure(figsize=(12, 6))
    
    if tipo == 'tmax_tmin':

        df_tmin_obs = df_tmin[df_tmin['type'] == 'observado']
        df_tmin_prev = df_tmin[df_tmin['type'] == 'previsão']
        df_tmax_obs = df[df['type'] == 'observado']
        df_tmax_prev = df[df['type'] == 'previsão'] 

        # tmin obs
        plt.plot(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m'], color='blue', lw=1.5, marker='o', markerfacecolor="None")
        plt.plot(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m_clim'], color='blue', lw=1, ls='--')

        for x, y in zip(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", color='blue', ha='right', va='bottom', fontsize=16)

        # tmax obs
        plt.plot(df_tmax_obs['valid_time_fmt'], df_tmax_obs['t2m'], color='red', lw=1.5, marker='o', markerfacecolor="None")
        plt.plot(df_tmax_obs['valid_time_fmt'], df_tmax_obs['t2m_clim'], color='red', lw=1, ls='--')

        for x, y in zip(df_tmax_obs['valid_time_fmt'], df_tmax_obs['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='red')

        # tmin prev
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m'], color='blue', lw=1.5, marker='o')
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m_clim'], color='blue', lw=1, ls='--')

        for x, y in zip(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='blue')

        # tmax prev
        plt.plot(df_tmax_prev['valid_time_fmt'], df_tmax_prev['t2m'], color='red', lw=1.5, marker='o')
        plt.plot(df_tmax_prev['valid_time_fmt'], df_tmax_prev['t2m_clim'], color='red', lw=1, ls='--')

        for x, y in zip(df_tmax_prev['valid_time_fmt'], df_tmax_prev['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='red')

        # Ajustes de layout
        plt.ylabel('Temperatura do Ar (°C)\n', fontsize=20)
        plt.ylim(5, 45)  
        plt.xlabel('Data', fontsize=18)
        plt.xticks(rotation=45, fontsize=16)
        plt.yticks(fontsize=16)
        plt.grid(axis='both', ls='--', alpha=0.4)

    elif tipo == 'geada':

        df_tmin_obs = df[df['type'] == 'observado']
        df_tmin_prev = df[df['type'] == 'previsão']
        xaxix_l1 = df['valid_time_fmt'].values.tolist()

        # tmin obs
        plt.plot(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m'], color='blue', lw=1.5, marker='o', markerfacecolor="None")
        plt.plot(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m_clim'], color='blue', lw=1, ls='--')

        for x, y in zip(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", color='blue', ha='right', va='bottom', fontsize=16)

        # tmin prev
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m'], color='blue', lw=1.5, marker='o')
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m_clim'], color='blue', lw=1, ls='--')

        for x, y in zip(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='blue')

        limites_geada = [5.5, 1.8, -0.5, -4]
        fraca = [limites_geada[0]] * len(xaxix_l1)
        moderada = [limites_geada[1]] * len(xaxix_l1)
        forte = [limites_geada[2]] * len(xaxix_l1)
        base = [limites_geada[3]]  * len(xaxix_l1)

        plt.fill_between(xaxix_l1, base, forte, color='#5759A8', label='forte')
        plt.fill_between(xaxix_l1, forte, moderada, color='#917BCE', label='moderada')
        plt.fill_between(xaxix_l1, moderada, fraca, color='#C4BDE6', label='fraca')
        
        plt.axhline(y=-0.5, color='black', linestyle='--', label='-0.5')
        plt.axhline(y=1.8,  color='black', linestyle='--', label='1.8')
        plt.axhline(y=5.5,  color='black', linestyle='--', label='5.5')

        plt.text(0.2, 0.16, 'Forte', fontsize=16, color='black', ha='center', va='bottom', transform=plt.gcf().transFigure)
        plt.text(0.217, 0.25, 'Moderada', fontsize=16, color='black', ha='center', va='bottom', transform=plt.gcf().transFigure)
        plt.text(0.2, 0.34, 'Fraca', fontsize=16, color='black', ha='center', va='bottom', transform=plt.gcf().transFigure)
        plt.text(0.217, 0.45, 'Sem Risco', fontsize=16, color='black', ha='center', va='bottom', transform=plt.gcf().transFigure)

        plt.ylim(-4, 20)
        plt.yticks(fontsize=16)
        plt.ylabel('Temp. minima do Ar (°C)\n', fontsize=20)
        plt.xlabel('Data', fontsize=18)
        plt.xticks(rotation=45, fontsize=16)
        plt.grid(axis='both', ls='--', alpha=0.4)

    elif tipo == 'submercado':

        df_obs = df[df['type'] == 'observado']
        df_prev = df[df['type'] == 'previsão']

        # obs
        plt.plot(df_obs['valid_time_fmt'], df_obs['t2m'], color='purple', lw=1.5, marker='o', markerfacecolor="None")
        plt.plot(df_obs['valid_time_fmt'], df_obs['t2m_clim'], color='purple', lw=1, ls='--')

        for x, y in zip(df_obs['valid_time_fmt'], df_obs['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", color='purple', ha='right', va='bottom', fontsize=16)

        # prev
        plt.plot(df_prev['valid_time_fmt'], df_prev['t2m'], color='purple', lw=1.5, marker='o')
        plt.plot(df_prev['valid_time_fmt'], df_prev['t2m_clim'], color='purple', lw=1, ls='--')

        for x, y in zip(df_prev['valid_time_fmt'], df_prev['t2m']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='purple')

       # Ajustes de layout
        plt.ylabel('Temp. média do ar (°C)\n', fontsize=20)
        plt.xlabel('Data', fontsize=18)
        plt.xticks(rotation=45, fontsize=16)
        
        if df['regiao'].unique() == 'Sudeste':
            plt.yticks(np.arange(15, 35, 5),fontsize=16)

        elif df['regiao'].unique() == 'Sul':
            plt.yticks(np.arange(10, 35, 5),fontsize=16)

        elif df['regiao'].unique() == 'Nordeste' or df['regiao'].unique() ==    'Norte':
            plt.yticks(np.arange(20, 36, 5),fontsize=16)

        plt.grid(axis='both', ls='--', alpha=0.4)

    elif tipo == 'prec24h':

        plt.bar(df['data_fmt'], df['tp'], color='#810090', edgecolor='black')
        plt.ylim(0, 100)  
        plt.ylabel('Precipitação (mm)', fontsize=20)
        plt.yticks(range(0, 101, 10))
        plt.xticks(rotation=45, fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='both', ls='--', alpha=0.4)

    elif tipo == 'vento':

        plt.plot(df['data'], df['magnitude'], marker='o', color='purple')
        plt.plot(df['data'], df['magnitude_clim'], linestyle='--', color='black')
        plt.ylabel('Magnitude do vento (m/s)', size=15)
        plt.grid(axis='both', ls='--', alpha=0.4)
        plt.yticks(size=13)
        plt.ylim(0, 12)
        plt.xticks(rotation=75, size=13)        

        for x, y in zip(df['data'], df['magnitude']):
            plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='purple')

    plt.title(titulo, fontsize=16, fontweight='bold')
    plt.savefig(f'{filename}.png', bbox_inches='tight')

    return

###################################################################################################################

class GeraProdutosPrevisao:

    def __init__(self, produto_config_sf, tp_params=None, pl_params=None, shapefiles=None, produto_config_pl=None):

        self.produto_config_sf = produto_config_sf
        self.modelo_fmt = self.produto_config_sf.modelo
        self.data_fmt = f'{pd.to_datetime(self.produto_config_sf.data).strftime("%Y%m%d")}{str(self.produto_config_sf.inicializacao).zfill(2)}'
        self.tp_params = tp_params or {}
        self.pl_params = pl_params or {}
        self.shapefiles = shapefiles
        self.produto_config_pl = produto_config_pl
        self.qtdade_max_semanas = CONSTANTES['semanas_operativas'].get(self.modelo_fmt, 3)
        self.path_savefiguras = f'{Constants().PATH_SAVE_FIGS_METEOROLOGIA}/{self.modelo_fmt}/{self.data_fmt}'

        os.makedirs(self.path_savefiguras, exist_ok=True)

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
                'prefix_filename': 'tempo',
                'prefix_title': ''
            }
        }

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
                                var_anomalia='tp', level_anomalia=200, anomalia_mensal=False, regiao_estacao_chuvosa='seb',
                                **kwargs):
        
        """
        modo: 24h, total, semanas_operativas, bacias_smap, probabilidade_limiar, diferenca, prec_pnmm'
        """


        qtdade_max_semanas = self.qtdade_max_semanas
        path_to_save = f'{self.path_savefiguras}/{modo}'
        os.makedirs(path_to_save, exist_ok=True)

        # try:

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
                    filename=f'tp_24h_{self.modelo_fmt}_{n_24h.item()}',
                    shapefiles=self.shapefiles,
                    path_to_save=path_to_save,
                    **kwargs
                )

        elif modo == 'prec_pnmm':

            varname = 'msl' if 'ecmwf' in self.modelo_fmt else 'prmsl'

            # Tp
            tp_24h = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')

            # Pnmm
            if self.pnmm_mean is None:
                _, self.pnmm_mean, _ = self._carregar_pnmm_mean()

            pnmm_24h = resample_variavel(self.pnmm_mean, self.modelo_fmt, varname, '24h', modo_agrupador='mean')

            for n_24h, p_24h in zip(tp_24h.tempo, pnmm_24h.tempo):

                print(f'Processando {n_24h.item()}...')
                tp_plot = tp_24h.sel(tempo=n_24h)
                pnmm_plot = pnmm_24h.sel(tempo=p_24h)
                pnmm_plot = nd.gaussian_filter(pnmm_plot[varname]*1e-2, sigma=2)

                tempo_ini = ajustar_hora_utc(pd.to_datetime(tp_plot.data_inicial.item()))
                semana = encontra_semanas_operativas(pd.to_datetime(self.tp.time.values), tempo_ini, ds_tempo_final=self.tp.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                titulo = gerar_titulo(
                    modelo=self.modelo_fmt, tipo='PREC24, PNMM', cond_ini=self.cond_ini,
                    data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    data_fim=pd.to_datetime(tp_plot.data_final.item()).strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                    semana=semana
                )

                plot_campos(
                    ds=tp_plot['tp'],
                    variavel_plotagem='chuva_ons',
                    title=titulo,
                    filename=f'tp_24h_pnmm_{self.modelo_fmt}_{n_24h.item()}',
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
                filename=f'tp_acumulado_total_{self.modelo_fmt}',
                shapefiles=self.shapefiles,
                path_to_save=path_to_save,
                **kwargs
            )

            # Acumulado com MERGE
            path_merge = './tmp/downloads/merge'
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
                        tipo=f'MERGE + Prev. {mes}'
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
                        tipo=f'Acumulado total. {mes}'
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
                            sem_intervalo_semana=True
                        )

                        plot_campos(
                            ds=ds_anomalia['tp'],
                            variavel_plotagem='tp_anomalia',
                            title=titulo,
                            filename=f'{index}_tp_anomalia_merge_{self.modelo_fmt}',
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
                        sem_intervalo_semana=True
                    )

                    plot_campos(
                        ds=ds_acumulado['tp'],
                        variavel_plotagem='acumulado_total',
                        title=titulo,
                        filename=f'{index}_tp_acumulado_total_merge_{self.modelo_fmt}',
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
                        variavel_plotagem='chuva_ons' if not anomalia_sop else 'tp_anomalia',
                        title=titulo,
                        filename=f'tp_sop_{self.modelo_fmt}_semana{n_semana.item()}' if not anomalia_sop else f'tp_sop_{self.modelo_fmt}_anomalia_semana{n_semana.item()}',
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
                        filename=f'tp_sop_{tipo}_{self.modelo_fmt}_semana{n_semana.item()}',
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
                        filename=f'tp_{freq_prob}_{self.modelo_fmt}_{self.freqs_map[freq_prob]["prefix_filename"]}{n.item()}_probabilidade_{limiar}',
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

            ds_anterior = ajusta_acumulado_ds(ds_anterior, m_to_mm=True)

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
                    modelo=self.modelo_fmt, sem_intervalo_semana=True, tipo=f'Diferença {tipo_dif}', cond_ini=self.cond_ini,
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
                    filename=f'tp_{freq_prob}_{self.modelo_fmt}_{self.freqs_map[freq_prob]["prefix_filename"]}{n.item()}_desvpad',
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
            ds_mask = xr.open_dataset('./tmp/data/land.nc').isel(time=0).isel(nbnds=0)
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

        elif modo == 'graficos':

            target_lon, target_lat, _ = get_pontos_localidades()
            tp_proc = resample_variavel(self.tp_mean, self.modelo_fmt, 'tp', '24h')
            tp_no_ponto = tp_proc.sel(latitude=target_lat, longitude=target_lon+360, method='nearest').to_dataframe().reset_index()
            tp_no_ponto['data_fmt'] = tp_no_ponto['data_final'].dt.strftime('%d/%m')

            for id in tp_no_ponto['id'].unique():

                tp_plot = tp_no_ponto[tp_no_ponto['id'] == id]
                titulo = f"{CONSTANTES['city_dict'][id]}\n{self.modelo_fmt.upper()} - PRECH24HRS - Condição Inicial: {self.cond_ini}"
                filename = f'{path_to_save}/{id}_prec24h'
                plot_graficos_2d(df=tp_plot, tipo='prec24h', titulo=titulo, filename=filename)

        # except Exception as e:
        #     print(f'Erro ao gerar precipitação ({modo}): {e}')

    def _processar_varsdinamicas(self, modo, anomalia_frentes=False, resample_freq='24h', anomalia_sop=False, var_anomalia='gh', level_anomalia=500, **kwargs):

        """
        modo: jato_div200, vento_temp850, geop_vort500, frentes_frias, geop500, ivt, vento_div850,  chuva_geop500_vento850
        """

        qtdade_max_semanas = self.qtdade_max_semanas
        path_to_save = f'{self.path_savefiguras}/{modo}'
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
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Jato {level_divergencia}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_streamplot['jato'],
                        variavel_plotagem='wind200',
                        title=titulo,
                        filename=f'vento_jato_div{level_divergencia}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
                        ds_streamplot=ds_streamplot,
                        variavel_streamplot='wind200',
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
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Temp. em {level_temp}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_quiver['t850'] - 273.15,  # Kelvin para Celsius
                        variavel_plotagem='temp850',
                        title=titulo,
                        filename=f'vento_temp{level_temp}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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
                        semana = encontra_semanas_operativas(pd.to_datetime(geop_.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                        titulo = self._ajustar_tempo_e_titulo(geop_, f'{self.freqs_map[resample_freq]["prefix_title"]}Vort. e Geop. {level_geop}hPa', semana, self.cond_ini )

                    else:
                        intervalo = geop_.intervalo.item().replace(' ', '\ ')
                        days_of_week = geop_.days_of_weeks.item()                        
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_plot['vorticidade'],
                        variavel_plotagem='vorticidade',
                        title=titulo,
                        filename=f'geop_vorticidade_{level_geop}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
                        ds_contour=ds_plot['gh']/10,
                        variavel_contour='gh_500',
                        plot_bacias=False,
                        color_contour='black',
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'frentes_frias':

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

                for mes in list(set(pnmm_sel.valid_time.dt.month.values)):

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
                        filename=f'frentes_{self.modelo_fmt}',
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
                        if (ds_climatologia.longitude < 0).any():
                            ds_climatologia = ds_climatologia.assign_coords(longitude=(ds_climatologia.longitude % 360)).sortby('longitude').sortby('latitude')

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
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=geop_plot['gh']/10,
                        variavel_plotagem='geop_500' if not anomalia_sop else 'geop_500_anomalia',
                        title=titulo,
                        filename=f'geopotencial_{level_geop}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}' if not anomalia_sop else f'geopotencial_{level_geop}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}_anomalia',
                        ds_contour=geop_plot['gh']/10 if not anomalia_sop else geop_plot_contour['gh']/10,
                        variavel_contour='gh_500',
                        color_contour='black' if anomalia_sop else 'white',
                        plot_bacias=False,
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
                        semana = encontra_semanas_operativas(pd.to_datetime(self.geop.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                        titulo = gerar_titulo(
                                modelo=self.modelo_fmt, tipo='Geop 700hPa e TIWV (1000-300)', cond_ini=self.cond_ini,
                                data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                                semana=semana
                            )

                    else:
                        intervalo = gh_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = gh_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_quiver['ivt']*100,
                        variavel_plotagem='ivt',
                        title=titulo,
                        filename=f'ivt_geop700_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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
                        semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]
                        titulo = self._ajustar_tempo_e_titulo(
                            us_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Vento e Divergência {level_divergencia}hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = us_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = us_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=ds_streamplot['divergencia'],
                        variavel_plotagem='divergencia850',
                        title=titulo,
                        filename=f'vento_div{level_divergencia}_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(n_24h.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.us.time.values), tempo_ini, ds_tempo_final=self.us.valid_time[-1].values, modelo=self.modelo_fmt)[0]

                    titulo = gerar_titulo(
                        modelo=self.modelo_fmt, tipo=f'Prec6h, Geo{level_geop}hPa, Vento{level_vento}hPa', cond_ini=self.cond_ini,
                        data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                        semana=semana, unico_tempo=True
                    )

                    plot_campos(ds=ds_quiver['tp'], 
                                variavel_plotagem='wind_prec_geop', 
                                title=titulo, 
                                filename=f'vento{level_vento}_prec_geop{level_geop}_{self.modelo_fmt}_{index}', 
                                plot_bacias=False, ds_quiver=ds_quiver, 
                                variavel_quiver='wind850', 
                                ds_contour=ds_quiver['geop_500'], 
                                variavel_contour='gh_500', 
                                color_contour='black',
                                shapefiles=self.shapefiles,
                                path_to_save=path_to_save,
                                **kwargs
                                )

            elif modo == 'psi':

                if self.us_mean is None or self.vs_mean is None or self.cond_ini is None:
                    self.us, self.vs, self.us_mean, self.vs_mean, self.cond_ini = self._carregar_uv_mean()

                psi200, chi200 = calcula_psi_chi(self.us_mean, self.vs_mean, dim_laco='valid_time', level=200)
                psi850, chi850 = calcula_psi_chi(self.us_mean, self.vs_mean, dim_laco='valid_time', level=850)
                psi200 = resample_variavel(psi200, self.modelo_fmt, 'psi', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, level_anomalia=200, var_anomalia='psi', anomalia_sop=anomalia_sop)
                psi850 = resample_variavel(psi850, self.modelo_fmt, 'psi', resample_freq, modo_agrupador='mean', qtdade_max_semanas=qtdade_max_semanas, level_anomalia=850, var_anomalia='psi', anomalia_sop=anomalia_sop)

                for n_24h in psi200.tempo:

                    print(f'Processando {n_24h.item()}...')
                    psi_plot = psi200.sel(tempo=n_24h)
                    psi_850_plot = psi850.sel(tempo=n_24h)

                    if resample_freq == '24h':
                        tempo_ini = ajustar_hora_utc(pd.to_datetime(psi_plot.data_inicial.item()))
                        semana = encontra_semanas_operativas(pd.to_datetime(psi200.time.values), tempo_ini)[0]
                        titulo = self._ajustar_tempo_e_titulo(
                            psi_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}PSI 200hPa', semana, self.cond_ini,
                    )

                    else:
                        intervalo = psi_plot.intervalo.item().replace(' ', '\ ')
                        days_of_week = psi_plot.days_of_weeks.item()
                        titulo = gerar_titulo(
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    psi_plot = psi_plot*(-1)
                    
                    plot_campos(
                        ds=psi_plot['psi']/1e6 if not anomalia_sop else psi_plot/1e6,
                        variavel_plotagem='psi',
                        title=titulo,
                        filename=f'psi_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}' if not anomalia_sop else f'psi_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}_anomalia',
                        ds_contour=psi_850_plot['psi']/1e6 if not anomalia_sop else psi_850_plot/1e6,
                        variavel_contour='psi',
                        color_contour='black' if anomalia_sop else 'white',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'geada-inmet':

                if self.t2m_mean is None:
                    _, self.t2m_mean, _ = self._carregar_t2m_mean()

                t2m_24h = resample_variavel(self.t2m_mean, self.modelo_fmt, 't2m', resample_freq, modo_agrupador='min', qtdade_max_semanas=qtdade_max_semanas)

                for n_24h in t2m_24h.tempo:
                    print(f'Processando {n_24h.item()}...')
                    t2m_24h_plot = t2m_24h.sel(tempo=n_24h)  
                    t2m_24h_plot = t2m_24h_plot-273.15
                    t2m_24h_plot = -1*t2m_24h_plot

                    tempo_ini = ajustar_hora_utc(pd.to_datetime(t2m_24h_plot.data_inicial.item()))
                    semana = encontra_semanas_operativas(pd.to_datetime(self.t2m_mean.time.values), tempo_ini)[0]
                    titulo = self._ajustar_tempo_e_titulo(t2m_24h_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Geada', semana, self.cond_ini)
                
                    plot_campos(
                        ds=t2m_24h_plot['t2m'],
                        variavel_plotagem='geada-inmet',
                        title=titulo,
                        filename=f'geada_inmet_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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
                    semana = encontra_semanas_operativas(pd.to_datetime(self.t2m_mean.time.values), tempo_ini)[0]
                    titulo = self._ajustar_tempo_e_titulo(t2m_24h_plot, f'{self.freqs_map[resample_freq]["prefix_title"]}Geada', semana, self.cond_ini)
                
                    plot_campos(
                        ds=t2m_24h_plot['t2m'],
                        variavel_plotagem='geada-cana',
                        title=titulo,
                        filename=f'geada_cana_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=var_24h_plot[varname],
                        variavel_plotagem='olr',
                        title=titulo,
                        filename=f'olr_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
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
                            modelo=self.modelo_fmt, tipo=f'Semana{n_24h.item()}',
                            cond_ini=self.cond_ini, intervalo=intervalo, days_of_week=days_of_week,
                            semana_operativa=True
                    )

                    plot_campos(
                        ds=magnitude,
                        variavel_plotagem='mag_vento100',
                        title=titulo,
                        filename=f'mag_vento100_{self.modelo_fmt}_{self.freqs_map[resample_freq]["prefix_filename"]}{n_24h.item()}',
                        ds_quiver=ds_quiver,
                        variavel_quiver='wind850',
                        plot_bacias=False,
                        shapefiles=self.shapefiles,
                        path_to_save=path_to_save,
                        **kwargs
                    )

            elif modo == 'graficos':

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
                obs_tmax_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMAX_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmin_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMIN_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmed_atual = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMED_{ano_atual}{mes_atual}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmax_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMAX_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmin_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMIN_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmed_anterior = pd.read_csv(f'{Constants().PATH_TO_SAVE_TXT_SAMET}/csv_files/SAMeT_CPTEC_TMED_{ano_anterior}{mes_anterior}.csv', parse_dates=['time']).drop(columns=['lon', 'lat']).rename(columns={'time': 'valid_time'})
                obs_tmax = pd.concat([obs_tmax_anterior, obs_tmax_atual], ignore_index=True)
                obs_tmin = pd.concat([obs_tmin_anterior, obs_tmin_atual], ignore_index=True)
                obs_tmed = pd.concat([obs_tmed_anterior, obs_tmed_atual], ignore_index=True)
                obs_tmax['type'] = 'observado'
                obs_tmin['type'] = 'observado'
                obs_tmed['type'] = 'observado'
                ultimos_15_dias = pd.date_range(start=pd.to_datetime(self.t2m_mean.time.item()) - pd.DateOffset(days=15), end=pd.to_datetime(self.t2m_mean.time.item()))
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
                    dados_t2max = t2max_no_ponto[t2max_no_ponto['id'] == id]
                    dados_t2min = t2min_no_ponto[t2min_no_ponto['id'] == id]

                    titulo = f"{CONSTANTES['city_dict'][id]}\n{self.modelo_fmt.upper()} - {self.cond_ini}"
                    filename = f'{path_to_save}/{id}'
                    plot_graficos_2d(df=dados_t2max, tipo='tmax_tmin', df_tmin=dados_t2min, titulo=titulo, filename=filename)
                    
                    filename = f'{path_to_save}/{id}_geada'
                    plot_graficos_2d(df=dados_t2min, tipo='geada', titulo=titulo, filename=filename)

                # Grafico por submercado
                for submercado in t2med_no_ponto_submercado['regiao'].unique():
                    dados_submercado = t2med_no_ponto_submercado[t2med_no_ponto_submercado['regiao'] == submercado].rename(columns={'t2m_peso': 't2m', 't2m_clim_peso': 't2m_clim'})

                    titulo = f"{submercado}\n{self.modelo_fmt.upper()} - {self.cond_ini}"
                    filename = f'{path_to_save}/{submercado}'
                    plot_graficos_2d(df=dados_submercado, tipo='submercado', titulo=titulo, filename=filename)

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

                for area in AREAS:

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
                        'magnitude_clim': magnitude_clim
                    })

                    # Titulo do plot
                    titulo = f'{self.modelo_fmt.upper()} - Magnitude do vento a 100m - {area.replace("_", " ")}\nCondição Inicial: {self.cond_ini} \u2022 Climatologia ERA5 [1991-2020]'
                    path_to_save = path_to_save.replace('_vento', '')
                    os.makedirs(path_to_save, exist_ok=True)
                    filename = f'{path_to_save}/mag_vento100_{area}'
                    plot_graficos_2d(df=df, tipo='vento', titulo=titulo, filename=filename)

        except Exception as e:
            print(f'Erro ao gerar variaveis dinâmicas ({modo}): {e}')

    ###################################################################################################################

    def gerar_prec24h(self, **kwargs):
        self._processar_precipitacao('24h', **kwargs)

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
        self._processar_varsdinamicas('frentes_frias', **kwargs)

    def gerar_geop500(self, **kwargs):
        self._processar_varsdinamicas('geop500', **kwargs)

    def gerar_ivt(self, **kwargs):
        self._processar_varsdinamicas('ivt', **kwargs)

    def gerar_vento_div850(self, **kwargs):
        self._processar_varsdinamicas('vento_div850', **kwargs)

    def gerar_chuva_geop500_vento850(self, **kwargs):
        self._processar_varsdinamicas('chuva_geop500_vento850', **kwargs)

    def gerar_psi(self, **kwargs):
        self._processar_varsdinamicas('psi', **kwargs)

    def gerar_geada_inmet(self, **kwargs):
        self._processar_varsdinamicas('geada-inmet', **kwargs)

    def gerar_geada_cana(self, **kwargs):
        self._processar_varsdinamicas('geada-cana', **kwargs)

    def gerar_olr(self, **kwargs):
        self._processar_varsdinamicas('olr', **kwargs)

    def gerar_mag_vento100(self, **kwargs):
        self._processar_varsdinamicas('mag_vento100', **kwargs)

    def gerar_graficos_temp(self, **kwargs):
        self._processar_varsdinamicas('graficos', **kwargs)

    def gerar_graficos_chuva(self, **kwargs):
        self._processar_precipitacao('graficos', **kwargs)

    def gerar_graficos_v100(self, **kwargs):
        self._processar_varsdinamicas('graficos_vento', **kwargs)

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

        try:

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
                            modelo=self.modelo_fmt, tipo='PREC24', cond_ini=cond_ini,
                            data_ini=tempo_ini.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            data_fim=tempo_fim.strftime('%d/%m/%Y %H UTC').replace(' ', '\\ '),
                            sem_intervalo_semana=True, condicao_inicial='Data arquivo'
                        )

                    plot_campos(
                        ds=tp_plot['tp'],
                        variavel_plotagem='chuva_ons',
                        title=titulo,
                        filename=f'{index}_tp_24h_{self.modelo_fmt}',
                        shapefiles=self.shapefiles,
                        **kwargs
                    )

            elif modo == 'acumulado_mensal':

                from calendar import monthrange

                self.tp, self.cond_ini = self._carregar_tp_mean(apenas_mes_atual=True)

                if len(self.cond_ini) > 0:
                    cond_ini = self.cond_ini[-1]

                else:
                    cond_ini = self.cond_ini

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
                        "acumulado_total": tp_plot_acc["tp"],
                        "anomalia_total": (("latitude", "longitude"), tp_plot_anomalia_total),
                        "anomalia_parcial": (("latitude", "longitude"), tp_plot_anomalia_parcial),
                        "pct_climatologia": (("latitude", "longitude"), tp_plot_anomalia_percentual),
                        "pct_climatologia_parcial": (("latitude", "longitude"), tp_plot_anomalia_percentual_parcial),
                    }
                )
                
                for data_var in ds_total.data_vars:

                    print(f'Processando {data_var}')

                    if data_var == 'acumulado_total':
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
                        filename=f'tp_{data_var}_{self.modelo_fmt}_{tempo_fim.strftime("%Y%m%d")}_{tempo_fim.strftime("%b%Y")}',
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

                                plot_df_to_mapa(dif, titulo=titulo, shapefiles=self.shapefiles, filename=f'dif_{modelo_prev}-{self.modelo_fmt}_{n_dia.strftime("%Y%m%d%H")}_f{cond_ini.strftime("%Y%m%d%H")}')

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
                                    shapefiles=self.shapefiles,
                                    **kwargs
                                )

                        except Exception as e:
                            print(f'Erro ao processar {modelo_prev} - {n_dia}: {e}')

        except Exception as e:
            print(f'Erro ao processar {modo}: {e}')

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
                t2max_no_ponto = t2max_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'}).drop(columns=['valid_time'])
                t2min_no_ponto = t2min_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'}).drop(columns=['valid_time'])
                t2med_no_ponto = t2med_no_ponto.rename(columns={'latitude': 'lat', 'longitude': 'lon'}).drop(columns=['valid_time'])

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

    def gerar_temp_diario(self, **kwargs):
        self._processar_temperatura('temp_diario', **kwargs)

    def gerar_temp_mensal(self, **kwargs):
        self._processar_temperatura('temp_mensal', **kwargs)

    def gerar_txt_cidades(self, **kwargs):
        self._processar_temperatura('gerar_txt_cidades', **kwargs)

###################################################################################################################
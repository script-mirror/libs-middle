import pandas as pd
import numpy as np
import xarray as xr
from middle.utils import Constants
from ..utils.utils import skip_zero_formatter, get_df_ons, calcula_media_bacia, ajusta_shp_json
import matplotlib
matplotlib.use('Agg')  # Backend para geração de imagens, sem interface gráfica
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, ListedColormap
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

    elif variavel_plotagem in ['chuva_ons_geodataframe']:
        levels = [0, 1 ,5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
        colors = ['#ffffff', '#e1ffff', '#b3f0fb','#95d2f9','#2585f0','#0c68ce','#73fd8b','#39d52b','#3ba933','#ffe67b','#ffbd4a','#fd5c22','#b91d22','#f7596f','#a9a9a9']  
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = ListedColormap(colors)
        cbar_ticks = None

    elif variavel_plotagem in ['chuva_boletim_consumidores']:
        levels = range(-300, 305, 5)
        colors = ['purple', 'white', 'green']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = range(-300, 350, 50)

    elif variavel_plotagem == 'acumulado_total_geodataframe':
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
        ]
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = None

    elif variavel_plotagem in ['tp_anomalia']:
        colors = ['mediumvioletred', 'maroon', 'firebrick', 'red', 'chocolate', 'orange', 'gold', 'yellow', 'white', 'aquamarine', 'mediumturquoise', 'cyan', 'lightblue', 'blue', 'purple', 'mediumpurple', 'blueviolet']
        levels = range(-150, 155, 5)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = [-150, -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125, 150]

    elif variavel_plotagem in ['tp_anomalia_mensal']:
        colors = ['mediumvioletred', 'maroon', 'firebrick', 'red', 'chocolate', 'orange', 'gold', 'yellow', 'white', 'aquamarine', 'mediumturquoise', 'cyan', 'lightblue', 'blue', 'purple', 'mediumpurple', 'blueviolet']
        levels = range(-300, 305, 5)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = range(-300, 350, 50)

    elif variavel_plotagem in ['chuva_acumualada_merge']:
        colors = ["#ffffff", "#e6e6e6", "#bebebe", "#969696", 
                  "#6e6e6e", "#c8ffbe", "#96f58c", "#50f050", 
                  "#1eb41e", "#057805", "#0a50aa", "#1464d2", 
                  "#2882f0", "#50a5f5", "#96d2fa", "#e1ffff", 
                  "#fffaaa", "#ffe878", "#ffc03c", "#ffa000", 
                  "#ff6000", "#ff3200", "#e11400", "#a50000",
                  "#c83c3c", "#e67070", "#f8a0a0", "#ffe6e6", 
                  "#cdcdff", "#b4a0ff", "#8c78ff", "#6455dc",
                  "#3c28b4"]
        levels = [0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 50, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300]
        cmap = None 
        cbar_ticks = None

    elif variavel_plotagem in ['chuva_acumualada_merge_anomalia']:
        colors = ['#FF0000', '#Ffa500', '#FFFFFF', '#0000ff', '#800080']
        levels = np.arange(-200, 210, 10)
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = [-200, -175, -150, -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125, 150, 175, 200]

    elif variavel_plotagem in ['dif_prev']:
        colors = ['#FF0000', '#Ffa500', '#FFFFFF', '#0000ff', '#800080']
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
        cbar_ticks = np.arange(-30, 35, 5)

    elif variavel_plotagem in ['chi']:
        levels = np.arange(-10, 10.5, 0.5)
        colors = ['green', 'white', 'brown']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1) 
        cbar_ticks = np.arange(-10, 11, 1)

    elif variavel_plotagem in ['geop_500_anomalia']:
        levels = range(-40, 42, 2)
        colors = ['darkblue', 'blue', 'white', 'red', 'darkred']
        cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(cmap, len(levels))    
        cbar_ticks = None     

    elif variavel_plotagem in ['pnmm_vento']:
        levels = [
        900, 950, 976, 986, 995, 1002, 1007, 1011,
        1013, 1015, 1019, 1024, 1030, 1038, 1046, 1080
        ]
        colors = [
        "#2b2e52", "#2a4d91", "#3e66c5", "#5498c6", "#54b3bc",
        "#56bfb7", "#87c2b6", "#c1ccc6", "#d7c6c8", "#dcc1a5",
        "#dfcd9b", "#dfba7a", "#d68856", "#c0575b", "#8f2c53"
        ]
        cmap = ListedColormap(colors)
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

    elif variavel_plotagem == 'mag_vento100_anomalia':
        levels = np.arange(-3, 3.5, 0.5)
        colors = None
        cmap = 'RdBu'
        cbar_ticks = np.arange(-3, 3.5, 0.5)

    elif variavel_plotagem == 'sst_anomalia':
        levels = np.arange(-3, 3.05, 0.05)
        colors = ['indigo', 'darkblue', 'blue', 'dodgerblue', 'cyan', 'white', 'white', 'yellow', 'orange', 'red', 'darkred', 'maroon']
        custom_cmap = LinearSegmentedColormap.from_list("CustomCmap", colors)
        cmap = plt.get_cmap(custom_cmap, len(levels)  + 1)
        cbar_ticks = np.arange(-3, 3.5, 0.5)

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
                path_to_save=Constants().PATH_SAVE_FIGS_METEOROLOGIA,
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
                with_norm=False,
                footnote_text=False,
                with_logo=True,
    ):

    os.makedirs(path_to_save, exist_ok=True)

    # Importando constantes e funções auxiliares
    from ..consts.constants import CONSTANTES
    from PIL import Image

    extent = tuple(extent)
    figsize = tuple(figsize)
    fig, ax = get_base_ax(extent=extent, figsize=figsize, central_longitude=central_longitude)
    levels, colors, cmap, cbar_ticks = custom_colorbar(variavel_plotagem)

    if with_norm:
        norm = BoundaryNorm(levels, len(colors))
    else:
        norm = None

    # Se colors e cmap nao forem None, seta levels para None
    if colors is not None and cmap is not None:
        colors = None
    
    lon, lat = np.meshgrid(ds['longitude'], ds['latitude'])
    cf = ax.contourf(lon, lat, ds, transform=ccrs.PlateCarree(), transform_first=True, origin='upper', levels=levels, colors=colors, extend='both', cmap=cmap, norm=norm)

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
            levels_clabel = np.arange(-4, 14, 2)
            # contornos negativos (tracejado)
            neg_levels = [lev for lev in levels_clabel if lev < 0]
            cf_neg = ax.contour(
                lon, lat, ds_contour,
                transform=ccrs.PlateCarree(),
                colors='black',
                linestyles='dashed',
                levels=neg_levels,
                linewidths=1.2
            )

            # contornos positivos e zero (sólido)
            pos_levels = [lev for lev in levels_clabel if lev >= 0]
            cf_pos = ax.contour(
                lon, lat, ds_contour,
                transform=ccrs.PlateCarree(),
                colors='black',
                linestyles='solid',
                levels=pos_levels,
                linewidths=1.2
            )

            # rótulos
            plt.clabel(cf_neg, inline=True, fmt='%.0f', fontsize=10, colors='black')
            plt.clabel(cf_pos, inline=True, fmt='%.0f', fontsize=10, colors='black')

        elif variavel_contour == 'chi':
            levels_clabel = np.arange(-4, 5, 1)
            # contornos negativos (tracejado)
            neg_levels = [lev for lev in levels_clabel if lev < 0]
            cf_neg = ax.contour(
                lon, lat, ds_contour,
                transform=ccrs.PlateCarree(),
                colors='black',
                linestyles='dashed',
                levels=neg_levels,
                linewidths=1.2
            )

            # contornos positivos e zero (sólido)
            pos_levels = [lev for lev in levels_clabel if lev >= 0]
            cf_pos = ax.contour(
                lon, lat, ds_contour,
                transform=ccrs.PlateCarree(),
                colors='black',
                linestyles='solid',
                levels=pos_levels,
                linewidths=1.2
            )

            # rótulos
            plt.clabel(cf_neg, inline=True, fmt='%.0f', fontsize=10, colors='black')
            plt.clabel(cf_pos, inline=True, fmt='%.0f', fontsize=10, colors='black')


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
    if variavel_plotagem in ['geada-inmet', 'geada-cana']:
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
                    gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5, transform=ccrs.PlateCarree())
            else:
                gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidths=1, alpha=0.5, transform=ccrs.PlateCarree())

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
                    ax.text(lon, lat, f"{row['tp']:.0f}", fontsize=13, color='black', fontweight='bold', ha='center', va='center', transform=ccrs.PlateCarree())
                            # bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')c
                            # )

    # Logo
    if with_logo:
        img = Image.open(Constants().LOGO_RAIZEN)
        im_width, _ = img.size
        bbox = plt.gca().get_window_extent()
        xo = bbox.x1 - im_width + margin_x
        yo = bbox.y0 + margin_y
        plt.figimage(img, xo=xo, yo=yo, alpha=0.3)

    # Footnote se existir
    if footnote_text:
        ax.text(-79.5, -34, footnote_text, ha='left', va='bottom', fontsize=10, color='#70279C', weight='bold')

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
def plot_df_to_mapa(df, path_to_save=Constants().PATH_DOWNLOAD_ARQUIVOS_DIFGPM, filename='filename', column_plot='dif', _type='dif', titulo=None, shapefiles=None, agrupador='mean', variavel_plotagem='dif_prev'):

    from PIL import Image
    import pdb

    # Agrupando por bacia
    if agrupador == 'mean':
        media_bacia = df.groupby('nome_bacia')[column_plot].mean()

    elif agrupador == 'sum':
        media_bacia = df.groupby('nome_bacia')[column_plot].sum()

    media_bacia = media_bacia.rename({'Paranapane':'Paranapanema', 'São Franci':'São Francisco', 'Jequitinho':'Jequitinhonha'})

    fig, ax = get_base_ax(extent=[280, 330, -35, 10], figsize=(12, 12), central_longitude=0)

    # Titulo
    ax.set_title(titulo, loc='left', fontsize=16)

    # Barra de cor
    levels, colors, cmap, cbar_ticks = custom_colorbar(variavel_plotagem)
    try:
        norm = BoundaryNorm(boundaries=levels, ncolors=len(colors), extend='both')
    except:
        norm = matplotlib.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
    # BoundaryNorm(boundaries=levels, ncolors=len(colors), extend='both')

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
    fig.colorbar(sm, cax=axins, orientation='horizontal', ticks=levels, extendrect=True, label='Precipitação [mm]')

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

    if _type == 'dif':
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

        # for x, y in zip(df_tmin_obs['valid_time_fmt'], df_tmin_obs['t2m']):
        #     plt.text(x, y+0.3, f"{y:.0f}", color='blue', ha='right', va='bottom', fontsize=16)

        # tmin prev
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m'], color='blue', lw=1.5, marker='o')
        plt.plot(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m_clim'], color='blue', lw=1, ls='--')

        # for x, y in zip(df_tmin_prev['valid_time_fmt'], df_tmin_prev['t2m']):
        #     plt.text(x, y+0.3, f"{y:.0f}", ha='right', va='bottom', fontsize=16, color='blue')

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
        plt.plot(df_obs['valid_time_fmt'], df_obs['t2m_w'], color='purple', lw=1.5, marker='o', markerfacecolor="None")
        plt.plot(df_obs['valid_time_fmt'], df_obs['t2m_clim_w'], color='purple', lw=1, ls='--')

        for x, y in zip(df_obs['valid_time_fmt'], df_obs['t2m_w']):
            plt.text(x, y+0.3, f"{y:.0f}", color='purple', ha='right', va='bottom', fontsize=16)

        # prev
        plt.plot(df_prev['valid_time_fmt'], df_prev['t2m_w'], color='purple', lw=1.5, marker='o')
        plt.plot(df_prev['valid_time_fmt'], df_prev['t2m_clim_w'], color='purple', lw=1, ls='--')

        for x, y in zip(df_prev['valid_time_fmt'], df_prev['t2m_w']):
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
    plt.close()

    return

###################################################################################################################


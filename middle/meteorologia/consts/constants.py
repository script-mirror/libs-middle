CONSTANTES = {

    'tipos_variaveis': {
        "surface": ['tp', 'u10', 'v10', 'prec'],                  # Variáveis em superfície
        "height_above_ground": ['t2m', '2t', 'v100', 'u100'],                     # Variáveis a 2 metros
        "isobaric_inhPa": ['u', 'v', 'z', 'gh', 't', 'q'],        # Variáveis isobáricas
        "mean_sea": ['pnmm', 'msl', 'prmsl'],                     # Pressão ao nível médio do mar
        "nominalTop": ['ttr', 'sulwrf']                           # Variáveis no topo nominal
    },

    "shapefiles": ['C:/Temp/shapefiles/Bacias_Hidrograficas_SIN.shp', 
                   'C:/Temp/shapefiles/estados_2010.shp'], # Shapefiles utilizados

    'labels_variaveis': {

        '[mm]': ['tp', 'chuva_ons', 'prec', 'acumulado_total', 'wind_prec_geop', 'diferenca', 'desvpad', 'tp_anomalia'],
        '[m/s]': ['wind200', 'mag_vento100'],
        '[dam]': ['geop_500'],
        '[1/s]': ['vorticidade', 'divergencia', 'divergencia850'],
        '[°C]': ['temp850', 't2m', '2t', 'geada'],
        '[kg*m-1*s-1]': ['ivt'],
        '[Anomalia de frentes frias]': ['frentes_anomalia'],
        '[Número de eventos]': ['frentes'],
        '[%]': ['probabilidade'],
        '[agdp]': ['geop_500_anomalia'],
        '[W/m²]': ['olr']
    },

    'path_save_netcdf': './tmp/data', # '/WX2TB/Documentos/saidas-modelos-novo'

    'path_reanalise_ncepI': './tmp/data', #'/WX2TB/Documentos/dados/reanI-ncep',

    'path_subbacias_shapefile': './tmp',

    'novas_subbacias': [

        {
            'cod': 'PSATMORP',
            'submercado': 'Nordeste',
            'bacia': 'São Francisco',
            'nome': 'Morpara',
            'geometry': None, 
            'lat': -11.57,
            'lon': -43.29
        },
        {
            'cod': 'PSATSBRD',
            'submercado': 'Nordeste',
            'bacia': 'São Francisco',
            'nome': 'Sobradinho',
            'geometry': None, 
            'lat': -9.43,
            'lon': -40.83
        },        
        {
            'cod': 'PSATCARIN',
            'submercado': 'Nordeste',
            'bacia': 'São Francisco',
            'nome': 'Carinhanha',
            'geometry': None, 
            'lat': -14.25,
            'lon': -43.76
        },
        {
            'cod': 'PSATPIMEALT',
            'submercado': 'Norte',
            'bacia': 'Xingu',
            'nome': 'Pimentalalt',
            'geometry': None, 
            'lat': -51.77,
            'lon': -3.13,
        },
    ],

    'semanas_operativas': {

        'gfs': 3,
        'ecmwf': 3,
        'gefs': 3,
        'ecmwf-ens': 3,
        'ecmwf-aifs': 3,
        'ecmwf-aifs-ens': 3,
        'gefs-estendido': 6,
        'gefs-membros': 3,
        'gefs-membros-estendido': 6,
        'ecmwf-ens-membros': 3,
        'ecmwf-ens-estendido': 7,
        'ecmwf-ens-membros-estendido': 7


    }

}


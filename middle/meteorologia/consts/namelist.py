CONSTANTES = {

    'tipos_variaveis': {
        "surface": ['tp', 'u10', 'v10', 'prec'],                  # Variáveis em superfície
        "height_above_ground": ['t2m', '2t'],                     # Variáveis a 2 metros
        "isobaric_inhPa": ['u', 'v', 'z', 'gh', 't', 'q'],        # Variáveis isobáricas
        "mean_sea": ['pnmm', 'msl', 'prmsl'],                     # Pressão ao nível médio do mar
        "nominalTop": ['ttr', 'sulwrf']                           # Variáveis no topo nominal
    },

    "shapefiles": ['C:/Temp/shapefiles/Bacias_Hidrograficas_SIN.shp', 
                   'C:/Temp/shapefiles/estados_2010.shp'], # Shapefiles utilizados

    'labels_variaveis': {

        '[mm]': ['tp', 'chuva_ons', 'prec', 'acumulado_total', 'wind_prec_geop', 'diferenca'],
        '[m/s]': ['wind200'],
        '[dam]': ['geop_500'],
        '[1/s]': ['vorticidade', 'divergencia', 'divergencia850'],
        '[°C]': ['temp850', 't2m', '2t'],
        '[kg*m-1*s-1]': ['ivt']
        
    },

    'path_save_netcdf': './data', # '/WX2TB/Documentos/saidas-modelos-novo'

}


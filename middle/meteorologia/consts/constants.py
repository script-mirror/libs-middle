import pandas as pd

CONSTANTES = {

    'tipos_variaveis': {
        "surface": ['tp', 'u10', 'v10', 'prec', 'prate'],                  # Variáveis em superfície
        "height_above_ground": ['t2m', '2t', 'v100', 'u100', '100u', '100v'],                     # Variáveis a 2 metros
        "isobaric_inhPa": ['u', 'v', 'z', 'gh', 't', 'q', 'strf'],        # Variáveis isobáricas
        "mean_sea": ['pnmm', 'msl', 'prmsl'],                     # Pressão ao nível médio do mar
        "nominalTop": ['ttr', 'sulwrf'],
        "mensal_sazonal": ['tpara'],
        "depthBelowSea": ['pt']                   
    },

    'shapefiles': ['C:/Temp/shapefiles/Bacias_Hidrograficas_SIN.shp', 
                   'C:/Temp/shapefiles/estados_2010.shp'], # Shapefiles utilizados

    'labels_variaveis': {

        '[mm]': ['tp', 'chuva_ons', 'prec', 'acumulado_total', 'wind_prec_geop', 'diferenca', 'desvpad', 'tp_anomalia', 'chuva_acumualada_merge', 'chuva_acumualada_merge_anomalia', 'chuva_boletim_consumidores', 'tp_anomalia_mensal', 'tp_anomalia_discretizado'],
        '[m/s]': ['wind200', 'mag_vento100', 'mag_vento100_anomalia'],
        '[dam]': ['geop_500'],
        '[1/s]': ['vorticidade', 'divergencia', 'divergencia850'],
        '[°C]': ['temp850', 't2m', '2t', 'geada', 'temp_anomalia', 'sst_anomalia'],
        '[kg*m-1*s-1]': ['ivt'],
        '[Anomalia de frentes frias]': ['frentes_anomalia'],
        '[Número de eventos]': ['frentes'],
        '[%]': ['probabilidade', 'pct_climatologia'],
        '[agdp]': ['geop_500_anomalia'],
        '[W/m²]': ['olr'],
        '[hPa]': ['pnmm_vento', 'pos_asas']
    },

    'path_save_netcdf': '/projetos/arquivos/meteorologia/dados_modelos/netcdf_salvos', # '/WX2TB/Documentos/saidas-modelos-novo'

    'path_reanalise_ncepI': '/WX2TB/Documentos/dados/reanI-ncep/diarios/dados_climatologia_frentes',

    # 'path_subbacias_shapefile': './tmp',

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
        'ecmwf-ens-membros-estendido': 7,
        'cfsv2': 7,
        'hgefs': 2,
        'aigefs': 3,
        'aigfs': 3,

    },

    'city_dict': {'sp': 'São Paulo', 'sp_pp': 'Presidente Prudente', 'sp_rp':'Ribeirão Preto',
                'rj':'Rio de Janeiro', 'mg':'Belo Horizonte', 'es':'Vitória', 'rs':'Porto Alegre',
                'sc':'Florianópolis', 'pr':'Curitiba','df':'Brasília', 'go':'Goiânia',
                'ms':'Campo Grande', 'mt':'Cuiabá', 'ba':'Salvador', 'se':'Aracaju',
                'al':'Maceió','pe':'Recife','pb':'João Pessoa','rn':'Natal','ce':'Fortaleza',
                'pi':'Teresina','ma':'São Luis','to':'Palmas','pa':'Belém','am':'Manaus',
                'ap':'Macapá','rr':'Boa Vista','ac':'Rio Branco','ro':'Porto Velho','sp_as':'Assis',
                'sp_ar':'Araçatuba', 'sp_aq':'Araraquara','sp_br':'Brotas','sp_ja':'Jaú',
                'sp_pi':'Piracicaba','ms_ms':'MS','go_ja':'Jataí','sp_ou':'Ourinhos','sp_sa':'Santos',
                'sp_va':'Valinhos','sp_ss':'São Sebastião','mg_ub':'Ubá','mg_de':'Descoberto',
                'sc_ba':'Balneário Camboriú', 'sc_it':'Itajaí', 'be':'Benálcool (Araçatuba - SP)',
                'de':'Destivale (Araçatuba - SP)', 'ga':'Gasa (Araçatuba - SP)',
                'mu':'Mundial (Araçatuba - SP)', 'un' : 'Univalem (Araçatuba - SP)',
                'bo':'Bonfim (Araraquara - SP)','se_':'Serra (Araraquara - SP)',
                'ta':'Tamoio (Araraquara - SP)','za':'Araraquara (Araraquara - SP)',
                'lem':'Leme (Araraquara - SP)', 'ip':'Iparussu (Assis - SP)',
                'ma_':'Maracaí (Assis - SP)', 'pa_':'Paraguaçu (Assis - SP)',
                'tr':'Tarumã (Assis - SP)', 'ps':'Paraiso (Brotas - SP)',
                'sc_':'Santa Cândida (Brotas - SP)','ja':'Jataí (Jataí - GO)','ba_':'Barra (Jaú - SP)',
                'dc':'Dois Córregos (Jaú - SP)','di':'Diamante (Jau - SP)','ca':'Caarapó (MS)',
                'ptp':'Passa Tempo (MS)','rbr':'Rio Brilhante (MS)','br':'Bom Retiro (Piracicaba - SP)',
                'cp':'Costa Pinto (Piracicaba - SP)','ra':'Rafard (Piracicaba - SP)',
                'sf':'São Francisco (Piracicaba - SP)','sh':'Santa Helena (Piracicaba - SP)',
                'ju':'Junqueira (Ribeirão Norte)','lpt':'Lagoa da Prata (Ribeiraão Norte)',
                'cnt':'Continental (Ribeirão Norte)','vro':'Vale do Rosário (Ribeirão Sul)',
                'umb':'Morro Agudo (Ribeirão Sul)','sel':'Santa Elisa (Ribeirão Sul)'
        },

    'city_peso': pd.DataFrame(
        {
            'id': ['sp_pp','sp_rp','rj','mg','es','go','rs','sc','pr','ba','pe',
                'pb','rn','ce','pi','ma','pa','am','ap'],
            'weights': [0.100,0.210,0.231,0.098,0.244,0.118,0.483,0.228,0.289,
                        0.244,0.075,0.170,0.227,0.115,0.170,0.270,0.130,0.310,0.290],
            'region': [
                'Sudeste','Sudeste','Sudeste',
                'Sudeste','Sudeste','Sudeste',
                'Sul','Sul','Sul',
                'Nordeste','Nordeste','Nordeste','Nordeste','Nordeste','Nordeste',
                'Norte','Norte','Norte','Norte'
            ]
        }
    ),

    'extents_mapa': {

        'brasil': [280, 330, -35, 10],
        'biomassa': [303, 317, -26, -17],
        'global': [0, 359, -90, 90],

    },

    'LOGO_RAIZEN': './tmp/raizen-logo.png',

    'PATH_SAVE_FIGS_METEOROLOGIA': './tmp/plots', # '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS'

    'PATH_HINDCAST_GEFS_EST': './tmp/data', # /WX4TB/Documentos/reforecast_gefs/dados

    'PATH_HINDCAST_ECMWF_EST': './tmp/data',

    'PATH_TO_SAVE_TXT_SAMET': './tmp/plots', # '/WX2TB/Documentos/saidas-modelos-novo/samet'

    'PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL': './tmp/data', # '/WX2TB/Documentos/saidas-modelos-novo/samet/WX/WX2TB/Documentos/fontes/tempo/novos_produtos/CLIMATOLOGIA_TEMPERATURAS'

    'PATH_CLIMATOLOGIA_UV100': './tmp/data', # '/WX2TB/Documentos/dados/UVCLIM/'

    'PATH_CLIMATOLOGIA_MERGE': './tmp/data', # '/WX/WX2TB/Documentos/dados/merge-climatologia'
    
    'PATH_CLIMATOLOGIA_SAMET': './tmp/data', # '/WX2TB/Documentos/dados/temp_samet/climatologia/'

    'PATH_TO_SAVE_TXT_SAMET': './tmp/plots', # '/WX2TB/Documentos/saidas-modelos-novo/samet'

    'PATH_FTP_ECMWF': './tmp/data',

    'PATH_SUBBACIAS_JSON': './tmp/subbacias.json',
    
    'PATH_COORDENADAS_CIDADES': './tmp/data', # '/WX2TB/Documentos/fontes/tempo/novos_produtos/COORDENADAS_CIDADES/'

    'PATH_DOWNLOAD_ARQUIVOS_METEOROLOGIA': './tmp/downloads', # '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS'

}


from ..consts.constants import CONSTANTES

###################################################################################################################

def pipelines(modelo, produtos, tipo):

    if modelo == 'gfs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.gerar_graficos_v100(),
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_temp850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop_vort500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_ivt(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_olr(margin_y=-90, resample_freq='sop'),

                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_frentes_frias(margin_y=-90, anomalia_frentes=True),
                lambda: produtos.gerar_jato_div200(margin_y=-90),
                lambda: produtos.gerar_vento_temp850(margin_y=-90),
                lambda: produtos.gerar_geop_vort500(margin_y=-90),
                lambda: produtos.gerar_vento_div850(margin_y=-90),
                lambda: produtos.gerar_ivt(margin_y=-90),
                lambda: produtos.gerar_olr(margin_y=-90),
                lambda: produtos.gerar_chuva_geop500_vento850(extent=CONSTANTES['extents_mapa']['brasil']),
                
                
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),
                lambda: produtos.gerar_graficos_chuva(),
                lambda: produtos.gerar_graficos_temp(),
                lambda: produtos.salva_netcdf(variavel='tp'),

            ]

    elif modelo == 'gefs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_temp850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop_vort500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_olr(margin_y=-90, resample_freq='sop'),

                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_frentes_frias(margin_y=-90, anomalia_frentes=True),
                lambda: produtos.gerar_jato_div200(margin_y=-90),
                lambda: produtos.gerar_vento_temp850(margin_y=-90),
                lambda: produtos.gerar_geop_vort500(margin_y=-90),
                lambda: produtos.gerar_vento_div850(margin_y=-90),
                lambda: produtos.gerar_olr(margin_y=-90),
                lambda: produtos.gerar_chuva_geop500_vento850(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.salva_netcdf(variavel='tp'),
                
                
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                # lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                # lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),

            ]

    elif modelo == 'gefs-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, anomalia_sop=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], anomalia_mensal=True),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]

        elif tipo == 'pl':
            return [

                # # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                # lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                # lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),

            ]

    elif modelo == 'gefs-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False),
                lambda: produtos.gerar_desvpad(ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(ensemble=False),
                lambda: produtos.gerar_probabilidade_climatologia(ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'gefs-membros-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False),
                lambda: produtos.gerar_probabilidade_climatologia(ensemble=False),
                lambda: produtos.gerar_desvpad(ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'ecmwf':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.gerar_graficos_v100(),
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_temp850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop_vort500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_ivt(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_olr(margin_y=-90, resample_freq='sop'),

                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_frentes_frias(margin_y=-90, anomalia_frentes=True),
                lambda: produtos.gerar_jato_div200(margin_y=-90),
                lambda: produtos.gerar_vento_temp850(margin_y=-90),
                lambda: produtos.gerar_geop_vort500(margin_y=-90),
                lambda: produtos.gerar_vento_div850(margin_y=-90),
                lambda: produtos.gerar_ivt(margin_y=-90),
                lambda: produtos.gerar_olr(margin_y=-90),
                lambda: produtos.gerar_chuva_geop500_vento850(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.salva_netcdf(variavel='tp'),
                
                
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),

            ]

    elif modelo == 'ecmwf-ens':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]  
        
        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_olr(margin_y=-90),
                lambda: produtos.gerar_olr(margin_y=-90, resample_freq='sop'),
                lambda: produtos.salva_netcdf(variavel='tp'),
            ]

    elif modelo == 'ecmwf-aifs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]  
        
        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.salva_netcdf(variavel='tp'),
            ]

    elif modelo == 'ecmwf-aifs-ens':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                # lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False, verifica_cache=False),
                # lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False, verifica_cache=False),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]  
        
        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
            ]

    elif modelo == 'ecmwf-ens-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False),
                lambda: produtos.gerar_probabilidade_climatologia(ensemble=False),
                lambda: produtos.gerar_desvpad(ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'ecmwf-ens-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_diferenca_tp(margin_y=-90),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, anomalia_sop=True),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], anomalia_mensal=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
            ]

        elif tipo == 'pl':
            return [

                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop', anomalia_sop=True),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop', anomalia_sop=True),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop', anomalia_sop=True),
            ]

    return 

###################################################################################################################

download_sfc_params = {

    'ecmwf-ens': {
        'type_ecmwf_opendata': ['cf', 'pf'],
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp', 'msl', 'ttr'],
        'provedor_ecmwf_opendata': 'ecmwf'
    },

    'ecmwf': {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp', 'msl', '2t', 'ttr', '100u', '100v'],
        'provedor_ecmwf_opendata': 'ecmwf',
    },

    'ecmwf-aifs': {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp', 'msl'],
        'model_ecmwf_opendata': 'aifs-single',

    },

    'ecmwf-aifs-ens': {
        'type_ecmwf_opendata': ['cf', 'pf'],
        'levtype_ecmwf_opendata': 'sfc',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['tp'],
        'model_ecmwf_opendata': 'aifs-ens',

    },

    'gefs': {
        'variables': '&var_ULWRF=on&var_APCP=on&var_PRMSL=on',
        'levels': '&lev_top_of_atmosphere=on&lev_surface=on&lev_mean_sea_level=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',        
    },

    'gefs-estendido': {
        'variables': '&var_ULWRF=on&var_APCP=on&var_PRMSL=on',
        'levels': '&lev_top_of_atmosphere=on&lev_surface=on&lev_mean_sea_level=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',       
        'steps': [i for i in range(0, 846, 6)]     
    },

    'gfs': {
        'variables': '&var_ULWRF=on&var_APCP=on&var_PRMSL=on&var_TMP=on&var_UGRD=on&var_VGRD=on',
        'levels': '&lev_top_of_atmosphere=on&lev_surface=on&lev_mean_sea_level=on&lev_2_m_above_ground=on&lev_100_m_above_ground=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60', 
    },

    'gefs-membros': {
        'variables': '&var_APCP=on',
        'levels': '&lev_surface=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',
        'file_size': 0,  # Tamanho mínimo do arquivo para considerar que o download foi bem-sucedido        
    },

    'ecmwf-ens-estendido': {

    },

}

download_pl_params = {

    'ecmwf': {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh', 'u', 'v', 't', 'q'],
        'levlist_ecmwf_opendata': [1000, 925, 850, 700, 600, 500, 400, 300, 200]        
    },

    'ecmwf-aifs': {
        'type_ecmwf_opendata': 'fc',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'oper',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh'],
        'levlist_ecmwf_opendata': [500]        
    },

    'ecmwf-ens': {
        'type_ecmwf_opendata': 'em',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh'],
        'levlist_ecmwf_opendata': [500]        
    },

    'ecmwf-aifs-ens': {
        'type_ecmwf_opendata': 'em',
        'levtype_ecmwf_opendata': 'pl',
        'stream_ecmwf_opendata': 'enfo',
        'steps': [i for i in range(0, 366, 6)],
        'variables': ['gh'],
        'levlist_ecmwf_opendata': [500]         
    },

    'gfs': {
        'variables': '&var_HGT=on&var_UGRD=on&var_VGRD=on&var_SPFH=on&var_TMP=on',
        'levels': '&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on&lev_900_mb=on&lev_875_mb=on&lev_850_mb=on&lev_825_mb=on&lev_800_mb=on&lev_775_mb=on&lev_750_mb=on&lev_725_mb=on&lev_700_mb=on&lev_675_mb=on&lev_650_mb=on&lev_625_mb=on&lev_600_mb=on&lev_575_mb=on&lev_550_mb=on&lev_525_mb=on&lev_500_mb=on&lev_475_mb=on&lev_450_mb=on&lev_425_mb=on&lev_400_mb=on&lev_375_mb=on&lev_350_mb=on&lev_325_mb=on&lev_300_mb=on&lev_200_mb=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',
    },

    'gefs': {
        'variables': '&var_HGT=on&var_UGRD=on&var_VGRD=on&var_TMP=on',
        'levels': '&lev_top_of_atmosphere=on&lev_200_mb=on&lev_925_mb=on&lev_500_mb=on&lev_850_mb=on&lev_surface=on&lev_mean_sea_level=on',
        'sub_region_as_gribfilter': '&subregion=&toplat=20&leftlon=240&rightlon=360&bottomlat=-60',        
    },

}

###################################################################################################################

open_model_params = {

    'ecmwf': {

        'tp_params': {
            'ajusta_acumulado': True,
            'm_to_mm': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
        }

    },

    'ecmwf-ens': {

        'tp_params': {
            'ajusta_acumulado': True,
            'm_to_mm': True,
            'cf_pf_members': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'expand_isobaric_dims': True,
        }

    },

    'ecmwf-ens-membros': {

        'tp_params': {
            'ajusta_acumulado': True,
            'm_to_mm': True,
            'cf_pf_members': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
        }

    },

    'ecmwf-aifs': {

        'tp_params': {
            'ajusta_acumulado': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'expand_isobaric_dims': True,
        }

    },

    'ecmwf-aifs-ens': {

        'tp_params': {
            'ajusta_acumulado': True,
            'm_to_mm': False,
            'cf_pf_members': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'expand_isobaric_dims': True,
        }

    },

    'gfs': {

        'tp_params': {
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'ajusta_longitude': True
        }

    },

    'gefs': {

        'tp_params': {
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'ajusta_longitude': True,
        }

    },

    'gefs-estendido': {

        'tp_params': {
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
            'ajusta_longitude': True,
        }

    },

    'gefs-membros': {

        'tp_params': {
            'arquivos_membros_diferentes': True,
            'sel_area': True,
        },

        'pl_params': {
            'sel_area': True,
        }

    },

    'ecmwf-ens-estendido': {

        'tp_params': {
            'ajusta_acumulado': True,
            'm_to_mm': True,
            'cf_pf_members': True,
            'sel_12z': True,
            'sel_area': True,
        },

        'pl_params': {
            'cf_pf_members': True,
            'sel_12z': True,
            'expand_isobaric_dims': True,
            'sel_area': False
        }
    }

}

###################################################################################################################

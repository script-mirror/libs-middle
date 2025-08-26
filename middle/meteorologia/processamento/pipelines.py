from encodings.punycode import T
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
                lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil']),
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
                lambda: produtos.salva_netcdf(variavel='tp'),
                lambda: produtos.gerar_graficos_chuva(),
                lambda: produtos.gerar_graficos_temp(),
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
                # lambda: produtos.gerar_prec_pnmm(margin_y=-90),
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
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                #lambda: produtos.salva_netcdf(variavel='tp'),
            ]  
        
        elif tipo == 'pl':
            return [                
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
            ]

    elif modelo == 'ecmwf-aifs-ens-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False, verifica_cache=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False, verifica_cache=False),
                # lambda: produtos.gerar_probabilidade_climatologia(ensemble=False),
                lambda: produtos.gerar_desvpad(ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return [
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
                lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], dif_01_15d=True, dif_15_final=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, anomalia_sop=True),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], anomalia_mensal=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.salva_netcdf(variavel='tp'),
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop', anomalia_sop=True, anomalia_mensal=True),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop', anomalia_sop=True),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop', anomalia_sop=True),
            ]

    elif modelo == 'ecmwf-ens-estendido-membros':

        if tipo == 'sfc':
            return [
                # lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=False),
                # lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                # lambda: produtos.gerar_desvpad(ensemble=False),
                # lambda: produtos.gerar_probabilidade_limiar(ensemble=False),
                lambda: produtos.gerar_probabilidade_climatologia(ensemble=False),
            ]

        elif tipo == 'pl':
            return [
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
            ]

    return 

###################################################################################################################

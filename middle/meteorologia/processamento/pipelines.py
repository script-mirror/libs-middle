from ..consts.constants import CONSTANTES

###################################################################################################################

def pipelines(modelo, produtos, tipo=None, hora=None):

    if modelo == 'gfs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_prec24h_biomassa(extent=CONSTANTES['extents_mapa']['biomassa']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                # lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.gerar_graficos_v100(),
                lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,
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
                lambda: produtos.gerar_indices_itcz(),
                
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_geada_inmet(),
                lambda: produtos.gerar_geada_cana(),
                lambda: produtos.gerar_graficos_chuva(),
                lambda: produtos.gerar_graficos_temp(),    
                lambda: produtos.gerar_vento_weol() if hora == 0 else None,    
            ]

    elif modelo == 'cmc-ens':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
            ]

        elif tipo == 'pl':
            return [            
            ]

    elif modelo == 'gefs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                # lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,     
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
                lambda: produtos.gerar_indices_itcz(),
                         
            ]

    elif modelo == 'gefs-bc':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, destinatario_wpp='11968606707'),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True, destinatario_wpp='11968606707'),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                # lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,     
            ]

        elif tipo == 'pl':
            return [
                         
            ]

    elif modelo == 'aigfs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                # lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),     
            ]

        elif tipo == 'pl':
            return [
                         
            ]

    elif modelo == 'aigefs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=False),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                # lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),     
            ]

        elif tipo == 'pl':
            return [
                         
            ]

    elif modelo == 'gefs-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, anomalia_sop=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], anomalia_mensal=True, add_valor_bacias=True),
                lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, dif_01_15d=True, dif_15_final=True) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_indices_itcz(),
            ]

    elif modelo == 'gefs-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=True),
                lambda: produtos.gerar_desvpad(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'gefs-membros-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=True),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'],ensemble=False),
                lambda: produtos.gerar_desvpad(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'ecmwf':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                # lambda: produtos.gerar_diferenca_tp(margin_y=-90, add_valor_bacias=True) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.gerar_graficos_v100(),
                lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,
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
                lambda: produtos.gerar_indices_itcz(),
                
                # Não é PL mas vou deixar aqui para gerar as coisas mais importantes antes
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
            ]

    elif modelo == 'ecmwf-ens':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                # lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,
                # lambda: produtos.gerar_indices_itcz(),  
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_olr(margin_y=-90, resample_freq='sop'),   
                lambda: produtos.gerar_olr(margin_y=-90),
            ]

    elif modelo == 'ecmwf-aifs':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_prec_pnmm(margin_y=-90),
                # lambda: produtos.gerar_diferenca_tp(margin_y=-90) if hora == 0 else None,
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                # lambda: produtos.salva_netcdf(variavel='tp') if hora == 0 else None,
            ]

        elif tipo == 'pl':
            return [
                lambda: produtos.gerar_geop500(margin_y=-90),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop'),
            ]

    elif modelo == 'ecmwf-aifs-ens':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
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
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=True),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_desvpad(extent=CONSTANTES['extents_mapa']['brasil'],ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return [
            ]

    elif modelo == 'ecmwf-ens-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=True),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_desvpad(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
            ]  
        
        elif tipo == 'pl':
            return []

    elif modelo == 'ecmwf-ens-estendido':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_diferenca_tp(extent=CONSTANTES['extents_mapa']['brasil'], dif_01_15d=True, dif_15_final=True, add_valor_bacias=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, anomalia_sop=True),
                lambda: produtos.gerar_acumulado_total(extent=CONSTANTES['extents_mapa']['brasil'], anomalia_mensal=True, add_valor_bacias=True),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='sudeste'),
                lambda: produtos.gerar_estacao_chuvosa(regiao_estacao_chuvosa='norte'),
                lambda: produtos.salva_netcdf(variavel='tp'),
                lambda: produtos.gerar_geop500(margin_y=-90, resample_freq='sop', anomalia_sop=True, anomalia_mensal=True),
                lambda: produtos.gerar_jato_div200(margin_y=-90, resample_freq='sop', anomalia_sop=True),
                lambda: produtos.gerar_vento_div850(margin_y=-90, resample_freq='sop', anomalia_sop=True),
                lambda: produtos.gerar_anomalia_vento850(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop', anomalia_mensal=True),
                lambda: produtos.gerar_psi(margin_y=-90, extent=CONSTANTES['extents_mapa']['global'], central_longitude=180, figsize=(17, 17), resample_freq='sop', anomalia_mensal=True),
            ]

        elif tipo == 'pl':
            return [

            ]

    elif modelo == 'ecmwf-ens-estendido-membros':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_media_bacia_smap(plot_graf=False, ensemble=False, salva_db=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=False, ensemble=False),
                lambda: produtos.gerar_desvpad(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_limiar(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], ensemble=False),
            ]

        elif tipo == 'pl':
            return [

            ]

    elif modelo == 'pconjunto-ons':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_prec_db(plot_semana=True, acumulado_total=True, prec_24h=True),
            ]

        elif tipo == 'pl':
            return []

    elif modelo == 'eta':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
                lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_media_bacia_smap(plot_graf=True, ensemble=True, salva_db=True),
            ]

        elif tipo == 'pl':
            return [

            ]

    elif modelo == 'merge':

        return [
            lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
            lambda: produtos.gerar_acumulado_mensal(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
            lambda: produtos.gerar_bacias_smap(salva_db=True),
            lambda: produtos.gerar_dif_prev(),
        ]

    elif modelo == 'cpc':

        return [
            lambda: produtos.gerar_prec24h(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
            lambda: produtos.gerar_acumulado_mensal(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True),
            # lambda: produtos.gerar_bacias_smap(salva_db=True),
            # lambda: produtos.gerar_dif_prev(),
        ]

    elif modelo == 'samet':

        return [
            lambda: produtos.gerar_temp_diario(extent=CONSTANTES['extents_mapa']['brasil']),
            lambda: produtos.gerar_temp_mensal(extent=CONSTANTES['extents_mapa']['brasil']),
        ]

    elif modelo == 'gefs-wind':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_vento_weol() if hora == 0 else None, 
            ]
    
        elif tipo == 'pl':
            return []
        
    elif modelo == 'gefs-estendido-wind':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil'], resample_freq='sop'),
                lambda: produtos.gerar_mag_vento100(extent=CONSTANTES['extents_mapa']['brasil']),
                lambda: produtos.gerar_vento_weol() if hora == 0 else None, 
            ]
    
        elif tipo == 'pl':
            return []

    elif modelo == 'cfsv2':

        if tipo == 'sfc':
            return [
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, periods_cfs=12, anomalia_sop=True),
                lambda: produtos.gerar_semanas_operativas(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, periods_cfs=28, anomalia_sop=True),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, periods_cfs=12, ensemble=False),
                lambda: produtos.gerar_probabilidade_climatologia(extent=CONSTANTES['extents_mapa']['brasil'], add_valor_bacias=True, periods_cfs=28, ensemble=False),
                lambda: produtos.gerar_ocnsst_cfsv2(periods_cfs=12, figsize=(17, 17), resample_freq='sop', anomalia_sop=True, extent=CONSTANTES['extents_mapa']['global']),
                # lambda: produtos.gerar_ocnsst_cfsv2(periods_cfs=28, resample_freq='sop', anomalia_sop=True, extent=CONSTANTES['extents_mapa']['global']),
                lambda: produtos.gerar_psi_cfsv2(periods_cfs=12, resample_freq='sop', anomalia_sop=True, extent=CONSTANTES['extents_mapa']['global'], central_longitude=180, figsize=(17, 17)),
                # lambda: produtos.gerar_psi_cfsv2(periods_cfs=28, resample_freq='sop', anomalia_sop=True, extent=CONSTANTES['extents_mapa']['global']),
            ]
    
        elif tipo == 'pl':
            return []

    elif modelo == 'cfsv2-mensal':

        if tipo == 'sfc':
            return [
            ]
    
        elif tipo == 'pl':
            return []

    return 

###################################################################################################################

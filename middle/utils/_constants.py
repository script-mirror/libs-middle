import os
from dotenv import load_dotenv
from .logger import setup_logger
logger = setup_logger()

env_path = os.path.join(os.path.abspath(os.path.expanduser("~")), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Carregando .env de: {env_path}")
else:
    load_dotenv()
    logger.warning(f".env nao encontrado no path {env_path}, usando load_dotenv() default")

class Constants:
    @property
    def BASE_URL(self):
        return os.getenv("BASE_URL", "https://tradingenergiarz.com")
    
    @property
    def USER_PLUVIA(self):
        return os.getenv('USER_PLUVIA')

    @property
    def PASSWORD_PLUVIA(self):
        return os.getenv('PASSWORD_PLUVIA')

    @property
    def PASSWORD_CARTEIRA_OFICIAL(self):
        return os.getenv('PASSWORD_CARTEIRA_OFICIAL')

    @property
    def USER_SINTEGRE(self):
        return os.getenv('USER_SINTEGRE')

    @property
    def PASSWORD_SINTEGRE(self):
        return os.getenv('PASSWORD_SINTEGRE')

    @property
    def HOST_MYSQL(self):
        return os.getenv('HOST_MYSQL')

    @property
    def PORT_DB_MYSQL(self):
        return os.getenv('PORT_DB_MYSQL')

    @property
    def USER_DB_MYSQL(self):
        return os.getenv('USER_DB_MYSQL')

    @property
    def PASSWORD_DB_MYSQL(self):
        return os.getenv('PASSWORD_DB_MYSQL')

    @property
    def USER_DB_ANEEL(self):
        return os.getenv('USER_DB_ANEEL')

    @property
    def PASSWORD_DB_ANEEL(self):
        return os.getenv('PASSWORD_DB_ANEEL')

    @property
    def HOST_MSSQL(self):
        return os.getenv('HOST_MSSQL')

    @property
    def PORT_DB_MSSQL(self):
        return os.getenv('PORT_DB_MSSQL')

    @property
    def USER_DB_MSSQL(self):
        return os.getenv('USER_DB_MSSQL')

    @property
    def PASSWORD_DB_MSSQL(self):
        return os.getenv('PASSWORD_DB_MSSQL')

    @property
    def IP_SMTP_EMAIL(self):
        return os.getenv('IP_SMTP_EMAIL')

    @property
    def PORT_EMAIL(self):
        return os.getenv('PORT_EMAIL')

    @property
    def PASSWORD_EMAIL_CLIME(self):
        return os.getenv('PASSWORD_EMAIL_CLIME')

    @property
    def PASSWORD_EMAIL_CV(self):
        return os.getenv('PASSWORD_EMAIL_CV')

    @property
    def USER_AIRFLOW(self):
        return os.getenv('USER_AIRFLOW')

    @property
    def PASSWORD_AIRFLOW(self):
        return os.getenv('PASSWORD_AIRFLOW')

    @property
    def API_URL_AIRFLOW(self):
        return os.getenv('API_URL_AIRFLOW')

    @property
    def API_URL_APIV2(self):
        return os.getenv('URL_API_V2')

    @property
    def USER_BBCE(self):
        return os.getenv('USER_BBCE')

    @property
    def PASSWORD_BBCE(self):
        return os.getenv('PASSWORD_BBCE')

    @property
    def API_URL_BBCE(self):
        return os.getenv('API_URL_BBCE')

    @property
    def API_KEY_BBCE(self):
        return os.getenv('API_KEY_BBCE')

    @property
    def CODE_COMPANY_BBCE(self):
        return os.getenv('CODE_COMPANY_BBCE')

    @property
    def USER_HCTI(self):
        return os.getenv('USER_HCTI')

    @property
    def API_KEY_HCTI(self):
        return os.getenv('API_KEY_HCTI')

    @property
    def USER_HCTI2(self):
        return os.getenv('USER_HCTI2')

    @property
    def API_KEY_HCTI2(self):
        return os.getenv('API_KEY_HCTI2')

    @property
    def USER_HCTI3(self):
        return os.getenv('USER_HCTI3')

    @property
    def API_KEY_HCTI3(self):
        return os.getenv('API_KEY_HCTI3')

    @property
    def USER_HCTI4(self):
        return os.getenv('USER_HCTI4')

    @property
    def API_KEY_HCTI4(self):
        return os.getenv('API_KEY_HCTI4')

    @property
    def USER_HCTI5(self):
        return os.getenv('USER_HCTI5')

    @property
    def API_KEY_HCTI5(self):
        return os.getenv('API_KEY_HCTI5')

    @property
    def API_URL_HCTI(self):
        return os.getenv('API_URL_HCTI')

    @property
    def FLASK_SECRET_KEY(self):
        return os.getenv('FLASK_SECRET_KEY')

    @property
    def HOST_SERVIDOR(self):
        return os.getenv('HOST_SERVIDOR')

    @property
    def AWS_ACCESS_KEY_ID(self):
        return os.getenv('AWS_ACCESS_KEY_ID')

    @property
    def AWS_SECRET_ACCESS_KEY(self):
        return os.getenv('AWS_SECRET_ACCESS_KEY')

    @property
    def WHATSAPP_API(self):
        return os.getenv('WHATSAPP_API')

    @property
    def URL_COGNITO(self):
        return os.getenv('URL_COGNITO')

    @property
    def CONFIG_COGNITO(self):
        return os.getenv('CONFIG_COGNITO')

    @property
    def URL_HTML_TO_IMAGE(self):
        return f'{self.BASE_URL}/html-to-img/convert'

    @property
    def NUMERO_TESTE(self):
        return os.getenv('NUMERO_TESTE')

    @property
    def URL_EVENTS_API(self):
        return os.getenv('URL_EVENTS_API')

    @property
    def API_PROSPEC_USERNAME(self):
        return os.getenv('API_PROSPEC_USERNAME')

    @property
    def API_PROSPEC_PASSWORD(self):
        return os.getenv('API_PROSPEC_PASSWORD')

    @property
    def SERVER_DEFLATE_PROSPEC(self):
        return 'm6i.24xlarge'

    @property
    def API_PLUVIA_USERNAME(self):
        return os.getenv('API_PLUVIA_USERNAME')

    @property
    def API_PLUVIA_PASSWORD(self):
        return os.getenv('API_PLUVIA_PASSWORD')
    
    
    # WHATSAPP
    #==============================================================================================================================================================
    @property
    def WHATSAPP_GILSEU(self):
        return '5481442398'
    
    @property
    def WHATSAPP_DECKS(self):
        return 'decks'
    
    @property
    def WHATSAPP_TESTE(self):
        return os.getenv('NUM_TESTE')

    @property
    def WHATSAPP_PMO(self):
        return 'pmo'

    @property
    def WHATSAPP_METEOROLOGIA(self):
        return 'wx - meteorologia'

    @property
    def WHATSAPP_MODELOS(self):
        return 'modelos'

    @property
    def WHATSAPP_PRECO(self):
        return 'preco'

    @property
    def WHATSAPP_CONDICAO_HIDRICA(self):
        return 'condicao hidrica'

    @property
    def WHATSAPP_PREMISSAS_PRECO(self):
        return 'premissas preco'

    @property
    def WHATSAPP_AIRFLOW(self):
        return 'airflow'

    @property
    def WHATSAPP_AIRFLOW_METEOROLOGIA(self):
        return 'airflow - meteorologia'

    @property
    def WHATSAPP_NOTIFICACOES_PRODUTOS(self):
        return 'notificacoes produtos'

    @property
    def WHATSAPP_FSARH(self):
        return 'fsarh'

    @property
    def WHATSAPP_DEBUG(self):
        return 'debug'

    @property
    def WHATSAPP_DESSEM(self):
        return 'rz - dessem'

    @property
    def WHATSAPP_BBCE(self):
        return 'bbce'

    @property
    def WHATSAPP_CONDICOES_SST(self):
        return 'rz - condicoes sst'

    @property
    def WHATSAPP_MIDDLE(self):
        return 'rz - middle'
     
     
     
    # E-MAIL
    #==============================================================================================================================================================
    @property
    def EMAIL_CLIME(self):
        return 'climenergy'
    
    @property
    def EMAIL_MIDDLE(self):
        return 'middle@wxe.com.br'

    @property
    def EMAIL_FRONT(self):
        return 'front@wxe.com.br'

    @property
    def EMAIL_GILSEU(self):
        return 'gilseu.muhlen@raizen.com'

    @property
    def USER_EMAIL_CELSO(self):
        return 'celso.trombetta@raizen.com'

    @property
    def EMAIL_SST(self):
        return "sst"

    @property
    def EMAIL_RDH(self):
        return "rdh"

    @property
    def EMAIL_CMO(self):
        return "cmo"

    @property
    def EMAIL_IPDO(self):
        return "ipdo"

    @property
    def EMAIL_MAPAS(self):
        return "mapas"

    @property
    def EMAIL_ACOMPH(self):
        return "acomph"

    @property
    def EMAIL_DESSEM(self):
        return "dessem"

    @property
    def EMAIL_RODADAS(self):
        return "rodadas"

    @property
    def EMAIL_REV_ENA(self):
        return "rev_ena"

    @property
    def EMAIL_PROCESSOS(self):
        return "processos"

    @property
    def EMAIL_INFO_BBCE(self):
        return "info_bbce"

    @property
    def EMAIL_REV_CARGA(self):
        return "rev_carga"

    @property
    def EMAIL_PAUTA_ANEEL(self):
        return "pauta_aneel"

    @property
    def EMAIL_DIFERENCA_CV(self):
        return "diferenca_cv"

    @property
    def EMAIL_INTERVENCOES(self):
        return "intervencoes"
 
 
 
    # PATH MIDDLE
    #==============================================================================================================================================================
    @property
    def PATH_ARQUIVOS(self):
        return self.PATH_PROJETOS + '/arquivos'
    
    @property
    def PATH_TMP(self):
        return self.PATH_ARQUIVOS + '/tmp'
    
    @property 
    def PATH_ARQUIVOS_TEMP(self):
        return self.PATH_ARQUIVOS + '/tmp'
    
    @property
    def PATH_PROJETO(self):
        return "/WX2TB/Documentos/fontes/PMO"

    @property
    def PATH_PROJETOS(self):
        return os.getenv('PATH_PROJETOS', '/projetos')

    @property
    def PATH_PREVS_PROSPEC(self):
        return self.PATH_PROJETOS + '/arquivos/prospec/prevs'

    @property
    def PATH_RESULTS_PROSPEC(self):
        return self.PATH_PROJETOS + '/arquivos/prospec/resultados'

    @property
    def PATH_PREVS_INTERNO(self):
        return self.PATH_PROJETOS +'/arquivos/prospec/prevs/raizen'
    
    @property
    def PATH_INFO_VAZOES_OBS_JSON(self):
        return self.PATH_PROJETOS + '/arquivos/smap/infos_vazoes/info_vazao_obs.json'
    
    @property
    def PATH_TOKEN(self):
        return os.path.expanduser("~")

    @property
    def ATIVAR_ENV(self):
        return " . /projetos/env/bin/activate;"
        
    # WEBHOOK
    #==============================================================================================================================================================
    @property
    def WEBHOOK_DECK_DECOMP_PRELIMINAR(self):
        return 'Deck Preliminar DECOMP - Valor Esperado'
    
    @property
    def WEBHOOK_DECK_NEWAVE_PRELIMINAR(self):
        return 'Deck NEWAVE Preliminar'
    
    @property
    def WEBHOOK_DECK_NEWAVE_DEFINITIVO(self):
        return 'DECK NEWAVE DEFINITIVO'
    
    @property
    def WEBHOOK_NOTAS_TECNICAS(self):
        return "Notas Técnicas - Medio Prazo"

    @property
    def WEBHOOK_NAO_CONSISTIDO(self):
        return "Resultados preliminares não consistidos  (vazões semanais - PMO)"

    @property
    def WEBHOOK_CONSISTIDO(self):
        return "Resultados preliminares consistidos (vazões semanais - PMO)"
    
    @property 
    def WEBHOOK_CARGA_DECOMP(self):
        return "Carga por patamar - DECOMP"
    
    @property 
    def WEBHOOK_RDH(self):
        return "RDH"
    
    @property 
    def WEBHOOK_CARGA_PATAMAR_NEWAVE(self):
        return "Previsões de carga mensal e por patamar - NEWAVE"
    
    @property
    def WEBHOOK_ECMWF(self):
        return "Modelo ECMWF"
    
    @property
    def WEBHOOK_ETA(self):
        return "Modelo ETA"
    
    @property
    def WEBHOOK_GEFS(self):
        return "Modelo GEFS"
    
      
    #ENDPOINTS API
    #==============================================================================================================================================================
    @property
    def GET_RODADAS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/"

    @property
    def GET_RODADAS_POR_ID(self):
        return f"{self.BASE_URL}/api/v2/rodadas/por-id/{{}}"

    @property
    def GET_RODADAS_HISTORICO(self):
        return f"{self.BASE_URL}/api/v2/rodadas/historico"

    @property
    def GET_RODADAS_SUBBACIAS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/subbacias"

    @property
    def GET_RODADAS_CHUVA_PREVISAO(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/previsao"

    @property
    def POST_RODADAS_CHUVA_PREVISAO_PESQUISA(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/previsao/pesquisa/{{}}"

    @property
    def POST_RODADAS_CHUVA_PREVISAO_MODELOS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/previsao/modelos"

    @property
    def POST_RODADAS_CHUVA_PREVISAO_MEMBROS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/previsao/membros"

    @property
    def GET_RODADAS_CHUVA_PREVISAO_MEMBROS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/previsao/membros"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada"

    @property
    def POST_RODADAS_CHUVA_OBSERVADA(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA_MERGE_CPTEC_DATA_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/merge-cptec/data-entre"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA_CPC(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/cpc"

    @property
    def POST_RODADAS_CHUVA_OBSERVADA_CPC(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/cpc"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA_CPC_RANGE_DATAS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/cpc-range-datas"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA_PSAT(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/psat"

    @property
    def POST_RODADAS_CHUVA_OBSERVADA_PSAT(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/psat"

    @property
    def GET_RODADAS_CHUVA_OBSERVADA_PSAT_DATA_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/observada/psat/data-entre"

    @property
    def POST_RODADAS_SMAP_TRIGGER_DAG(self):
        return f"{self.BASE_URL}/api/v2/rodadas/smap/trigger-dag"

    @property
    def POST_RODADAS_SMAP(self):
        return f"{self.BASE_URL}/api/v2/rodadas/smap"

    @property
    def GET_RODADAS_SMAP(self):
        return f"{self.BASE_URL}/api/v2/rodadas/smap"

    @property
    def GET_RODADAS_EXPORT_RAIN(self):
        return f"{self.BASE_URL}/api/v2/rodadas/export-rain"

    @property
    def GET_RODADAS_EXPORT_RAIN_OBS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/export-rain-obs"

    @property
    def GET_RODADAS_CHUVA_MERGE(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/merge"

    @property
    def GET_RODADAS_CHUVA_SMAP_SUBMERCADO(self):
        return f"{self.BASE_URL}/api/v2/rodadas/chuva/smap/submercado"

    @property
    def GET_RODADAS_VAZAO_OBSERVADA_PDP(self):
        return f"{self.BASE_URL}/api/v2/rodadas/vazao-observada-pdp"
    
    @property
    def POST_RODADAS_VAZAO_OBSERVADA_PDP(self):
        return f"{self.BASE_URL}/api/v2/rodadas/vazao-observada-pdp"

    @property
    def GET_RODADAS_POSTOS_PLUVIOMETRICOS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/postos-pluviometricos"

    @property
    def POST_RODADAS_POSTOS_PLUVIOMETRICOS(self):
        return f"{self.BASE_URL}/api/v2/rodadas/postos-pluviometricos"

    # ONS Endpoints
    @property
    def GET_ONS_BACIAS(self):
        return f"{self.BASE_URL}/api/v2/ons/bacias"

    @property
    def GET_ONS_SUBMERCADOS(self):
        return f"{self.BASE_URL}/api/v2/ons/submercados"

    @property
    def GET_ONS_BACIAS_SEGMENTADAS(self):
        return f"{self.BASE_URL}/api/v2/ons/bacias-segmentadas"

    @property
    def GET_ONS_ACOMPH(self):
        return f"{self.BASE_URL}/api/v2/ons/acomph"

    @property
    def POST_ONS_ACOMPH(self):
        return f"{self.BASE_URL}/api/v2/ons/acomph"

    @property
    def GET_ONS_ACOMPH_DATA_ACOMPH(self):
        return f"{self.BASE_URL}/api/v2/ons/acomph/data-acomph"

    @property
    def GET_ONS_ACOMPH_PRODUCTS_AVAILABLE(self):
        return f"{self.BASE_URL}/api/v2/ons/acomph/products-available"

    @property
    def POST_ONS_ENA_ACOMPH(self):
        return f"{self.BASE_URL}/api/v2/ons/ena-acomph"

    @property
    def GET_ONS_ENA_ACOMPH_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/ons/ena-acomph/entre"

    @property
    def GET_ONS_GERACAO_HORARIA(self):
        return f"{self.BASE_URL}/api/v2/ons/geracao-horaria"

    @property
    def GET_ONS_CARGA_HORARIA(self):
        return f"{self.BASE_URL}/api/v2/ons/carga-horaria"

    @property
    def GET_ONS_GERACAO_HORARIA_DATA_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/ons/geracao-horaria/data-entre"

    @property
    def GET_ONS_CARGA_HORARIA_DATA_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/ons/carga-horaria/data-entre"

    @property
    def ENDPOINT_IPDO(self):
        return f"{self.BASE_URL}/api/v2/ons/ipdo"
    
    @property
    def ENDPOINT_WEOL_PONDERADO(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/weighted-average"
    
    @property
    def ENDPOINT_PRODUTIBILIDADE(self):
        return f"{self.BASE_URL}/api/v2/ons/produtibilidade"

    @property
    def GET_NOME_UTE(self):
        return f"{self.BASE_URL}/api/v2/decks/siglas-cvu"

    @property
    def GET_ONS_RDH(self):
        return f"{self.BASE_URL}/api/v2/ons/rdh"

    @property
    def POST_ONS_RDH(self):
        return f"{self.BASE_URL}/api/v2/ons/rdh"
    
    @property
    def GET_PREV_ENA(self):
        return f"{self.BASE_URL}/api/v2/ons/prev/ena"
    
    @property
    def POST_PREV_ENA(self):
        return f"{self.BASE_URL}/api/v2/ons/prev/ena"

    # BBCE Endpoints
    @property
    def GET_BBCE_PRODUTOS_INTERESSE(self):
        return f"{self.BASE_URL}/api/v2/bbce/produtos-interesse"

    @property
    def POST_BBCE_PRODUTOS_INTERESSE(self):
        return f"{self.BASE_URL}/api/v2/bbce/produtos-interesse"

    @property
    def GET_BBCE_PRODUTOS_INTERESSE_HTML(self):
        return f"{self.BASE_URL}/api/v2/bbce/produtos-interesse/html"

    @property
    def GET_BBCE_NEGOCIACOES_CATEGORIAS(self):
        return f"{self.BASE_URL}/api/v2/bbce/negociacoes/categorias"

    @property
    def GET_BBCE_RESUMOS_NEGOCIACOES(self):
        return f"{self.BASE_URL}/api/v2/bbce/resumos-negociacoes"

    @property
    def GET_BBCE_RESUMOS_NEGOCIACOES_INTERESSE(self):
        return f"{self.BASE_URL}/api/v2/bbce/resumos-negociacoes/negociacoes-de-interesse"

    @property
    def GET_BBCE_RESUMOS_NEGOCIACOES_INTERESSE_FECHAMENTO(self):
        return f"{self.BASE_URL}/api/v2/bbce/resumos-negociacoes/negociacoes-de-interesse/fechamento"

    @property
    def GET_BBCE_RESUMOS_NEGOCIACOES_ULTIMA_ATUALIZACAO(self):
        return f"{self.BASE_URL}/api/v2/bbce/resumos-negociacoes/ultima-atualizacao"

    @property
    def GET_BBCE_RESUMOS_NEGOCIACOES_SPREAD_PRECO_MEDIO(self):
        return f"{self.BASE_URL}/api/v2/bbce/resumos-negociacoes/spread/preco-medio"

    # Decomp Endpoints
    @property
    def POST_DECOMP_WEOL(self):
        return f"{self.BASE_URL}/api/v2/decks/weol"

    @property
    def GET_DECOMP_WEOL(self):
        return f"{self.BASE_URL}/api/v2/decks/weol"

    @property
    def GET_DECOMP_WEOL_LAST_DECK_DATE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/last-deck-date"

    @property
    def GET_DECOMP_WEOL_PRODUCT_DATE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/product-date"

    @property
    def GET_DECOMP_WEOL_START_WEEK_DATE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/start-week-date"

    @property
    def POST_DECOMP_PATAMARES(self):
        return f"{self.BASE_URL}/api/v2/decks/patamares"

    @property
    def GET_DECOMP_PATAMARES(self):
        return f"{self.BASE_URL}/api/v2/decks/patamares"

    @property
    def GET_DECOMP_WEOL_WEIGHTED_AVERAGE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/weighted-average"

    @property
    def GET_DECOMP_WEOL_DIFF_TABLE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/diff-table"

    @property
    def GET_DECOMP_WEOL_WEIGHTED_AVERAGE_MONTH_TABLE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/weighted-average/month/table"

    @property
    def GET_DECOMP_WEOL_WEIGHTED_AVERAGE_WEEK_TABLE(self):
        return f"{self.BASE_URL}/api/v2/decks/weol/weighted-average/week/table"

    @property
    def POST_DECOMP_CARGA_DECOMP(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-decomp"

    @property
    def GET_DECOMP_CARGA_DECOMP(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-decomp"
    
    @property
    def POST_DECOMP_CARGA_PMO(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-pmo-decomp"

    @property
    def GET_DECOMP_CARGA_PMO(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-pmo-decomp"

    # CVU Endpoints
    @property
    def GET_CVU_USINAS(self):
        return f"{self.BASE_URL}/api/v2/decks/cvu/usinas"

    @property
    def GET_CVU(self):
        return f"{self.BASE_URL}/api/v2/decks/cvu"

    @property
    def POST_CVU(self):
        return f"{self.BASE_URL}/api/v2/decks/cvu"

    @property
    def POST_CVU_MERCHANT(self):
        return f"{self.BASE_URL}/api/v2/decks/cvu/merchant"

    @property
    def POST_CHECK_CVU(self):
        return f"{self.BASE_URL}/api/v2/decks/check-cvu"

    @property
    def GET_CHECK_CVU(self):
        return f"{self.BASE_URL}/api/v2/decks/check-cvu"

    @property
    def GET_CHECK_CVU_BY_ID(self):
        return f"{self.BASE_URL}/api/v2/decks/check-cvu/{{}}"

    @property
    def GET_HISTORICO_CVU(self):
        return f"{self.BASE_URL}/api/v2/decks/historico-cvu"

    # PMO Endpoints
    @property
    def GET_CARGA_PMO(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-pmo"

    @property
    def POST_CARGA_PMO(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-pmo"

    @property
    def GET_CARGA_PMO_HISTORICO_PREVISAO(self):
        return f"{self.BASE_URL}/api/v2/decks/carga-pmo/historico-previsao"

    # Newave Endpoints
    @property
    def GET_NEWAVE_PREVISOES_CARGAS(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/previsoes-cargas"

    @property
    def POST_NEWAVE_PREVISOES_CARGAS(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/previsoes-cargas"

    @property
    def POST_NEWAVE_SISTEMA(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema"

    @property
    def GET_NEWAVE_SISTEMA_LAST_DECK(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/last_deck"

    @property
    def GET_NEWAVE_SISTEMA_TOTAL_UNSI(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/total_unsi"

    @property
    def GET_NEWAVE_SISTEMA_MMGD_TOTAL(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/mmgd_total"
    
    @property
    def PUT_NEWAVE_SISTEMA_MMGD_TOTAL(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/mmgd_total"

    @property
    def GET_NEWAVE_SISTEMA_CARGAS_TOTAL_CARGA_GLOBAL(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/cargas/total_carga_global"

    @property
    def GET_NEWAVE_SISTEMA_CARGAS_TOTAL_CARGA_LIQUIDA(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/sistema/cargas/total_carga_liquida"

    @property
    def POST_NEWAVE_CADIC(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/cadic"

    @property
    def GET_NEWAVE_CADIC_LAST_DECK(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/cadic/last_deck"

    @property
    def GET_NEWAVE_CADIC_TOTAL_MMGD_BASE(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/cadic/total_mmgd_base"
    
    @property
    def PUT_NEWAVE_CADIC_TOTAL_MMGD_BASE(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/cadic/total_mmgd_base"

    @property
    def GET_NEWAVE_CADIC_TOTAL_ANDE(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/cadic/total_ande"

    @property
    def POST_NEWAVE_PATAMAR_CARGA_USINAS(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/patamar/carga_usinas"

    @property
    def GET_NEWAVE_PATAMAR_CARGA_USINAS_DT_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/patamar/carga_usinas/dt_entre"

    @property
    def POST_NEWAVE_PATAMAR_INTERCAMBIO(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/patamar/intercambio"

    @property
    def GET_NEWAVE_PATAMAR_INTERCAMBIO_DT_ENTRE(self):
        return f"{self.BASE_URL}/api/v2/decks/newave/patamar/intercambio/dt_entre"

    # Dessem Endpoints
    @property
    def GET_DESSEM_PREVISAO(self):
        return f"{self.BASE_URL}/api/v2/decks/dessem/previsao"

    # Restricoes Eletricas Endpoints
    @property
    def POST_RESTRICOES_ELETRICAS(self):
        return f"{self.BASE_URL}/api/v2/decks/restricoes-eletricas"

    @property
    def GET_RESTRICOES_ELETRICAS(self):
        return f"{self.BASE_URL}/api/v2/decks/restricoes-eletricas"

    @property
    def GET_RESTRICOES_ELETRICAS_HISTORICO(self):
        return f"{self.BASE_URL}/api/v2/decks/restricoes-eletricas/historico"
    
    # Dados Hidraulicos Endpoints
    @property
    def POST_DADOS_HIDRAULICOS_UHE(self):
        return f"{self.BASE_URL}/api/v2/ons-dados-abertos/dados-hidraulicos-uhe"

    @property
    def GET_DADOS_HIDRAULICOS_UHE(self):
        return f"{self.BASE_URL}/api/v2/ons-dados-abertos/dados-hidraulicos-uhe"
    
    @property
    def POST_DADOS_HIDRAULICOS_SUBSISTEMA(self):
        return f"{self.BASE_URL}/api/v2/ons-dados-abertos/dados-hidraulicos-subsistema"

    @property
    def GET_DADOS_HIDRAULICOS_SUBSISTEMA(self):
        return f"{self.BASE_URL}/api/v2/ons-dados-abertos/dados-hidraulicos-subsistema"
    
    # Meteorologia Endpoints
    @property
    def GET_METEOROLOGIA_ESTACAO_CHUVOSA(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/estacao-chuvosa"

    @property
    def POST_METEOROLOGIA_ESTACAO_CHUVOSA(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/estacao-chuvosa"

    @property
    def GET_METEOROLOGIA_ESTACAO_CHUVOSA_PREV(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/estacao-chuvosa-prev"

    @property
    def POST_METEOROLOGIA_ESTACAO_CHUVOSA_PREV(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/estacao-chuvosa-prev"

    @property
    def GET_METEOROLOGIA_CLIMATOLOGIA_BACIAS(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/climatologia-bacias"

    @property
    def POST_METEOROLOGIA_VENTO_PREVISTO(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/vento-previsto"

    @property
    def GET_METEOROLOGIA_VENTO_PREVISTO(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/vento-previsto"

    @property
    def GET_METEOROLOGIA_VENTO_PREVISTO_RODADAS(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/vento-previsto-rodadas"

    @property
    def GET_METEOROLOGIA_INDICES_DIARIOS_SST(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/indices-diarios-sst"

    @property
    def POST_METEOROLOGIA_INDICES_DIARIOS_SST(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/indices-diarios-sst"

    @property
    def POST_METEOROLOGIA_ESTACOES_METEOROLOGICAS(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/estacoes-meteorologicas"

    @property
    def GET_METEOROLOGIA_INFOS_ESTACOES_METEOROLOGICAS(self):
        return f"{self.BASE_URL}/api/v2/meteorologia/infos-estacoes-meteorologicas"

    # Pluvia Endpoints
    @property
    def GET_PLUVIA_BACIAS(self):
        return f"{self.BASE_URL}/api/v2/pluvia/bacias"

    # Utils Endpoints
    @property
    def GET_UTILS_DATA_ELETRICA(self):
        return f"{self.BASE_URL}/api/v2/utils/data-eletrica"
   
    
    #METEOROLOGIA
    #==============================================================================================================================================================
    @property 
    def LOGO_RAIZEN(self):
        return '/projetos/arquivos/meteorologia/raizen-logo.png'

    @property 
    def PATH_SUBBACIAS_JSON(self):
        return '/projetos/arquivos/meteorologia/subbacias.json'
    
    @property 
    def PATH_HINDCAST_ECMWF_EST(self):
        return '/WX4TB/Documentos/saidas-modelos/ecmwf-estendido/data-netcdf'

    @property 
    def PATH_HINDCAST_GEFS_EST(self):
        return '/WX4TB/Documentos/reforecast_gefs/dados'
    
    @property 
    def PATH_FTP_ECMWF(self):
        return '/ftp/files_sftp/ECMWF'
    
    @property 
    def PATH_CLIMATOLOGIA_MERGE(self):
        return '/WX2TB/Documentos/dados/merge-climatologia'
    
    @property 
    def PATH_CLIMATOLOGIA_CPC(self):
        return '/WX2TB/Documentos/dados/cpc-climatol'
    
    @property 
    def PATH_SAVE_FIGS_METEOROLOGIA(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS' # './tmp/plots'

    @property 
    def PATH_DOWNLOAD_ARQUIVOS_METEOROLOGIA(self):
        return '/projetos/arquivos/meteorologia/dados_modelos/brutos'

    @property 
    def PATH_DOWNLOAD_ARQUIVOS_MERGE(self):
        return '/WX2TB/Documentos/saidas-modelos-novo/mergegpm/data/mergegpm'

    @property 
    def PATH_DOWNLOAD_ARQUIVOS_CPC(self):
        return '/WX2TB/Documentos/dados/cpc'

    @property 
    def PATH_DOWNLOAD_ARQUIVOS_DIFGPM(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/dif_gpm'

    @property 
    def PATH_DOWNLOAD_ARQUIVOS_SAMET(self):
        return '/WX2TB/Documentos/dados/temp_samet'
    
    @property 
    def PATH_CLIMATOLOGIA_SAMET(self):
        return '/WX2TB/Documentos/dados/temp_samet/climatologia'

    @property 
    def PATH_COORDENADAS_CIDADES(self):
        return '/projetos/arquivos/meteorologia'
    
    @property 
    def PATH_TO_SAVE_TXT_SAMET(self):
        return '/WX2TB/Documentos/dados/temp_samet'
    
    @property 
    def PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL(self):
        return '/projetos/arquivos/meteorologia'
    
    @property 
    def PATH_CLIMATOLOGIA_UV100(self):
        return '/projetos/arquivos/meteorologia'
    
    @property 
    def PATH_ARQUIVOS_TEMP_METEOROLOGIA(self):
        return '/projetos/arquivos/meteorologia/dados_modelos/arquivos_temp'
    
    @property 
    def PATH_ARQUIVOS_UTILS(self):
        return '/projetos/arquivos/meteorologia/dados_modelos/arquivos_utils'

    @property 
    def PATH_ARQUIVOS_WEOL(self):
        return '/projetos/arquivos/meteorologia'

    @property 
    def PATH_FIGURAS_MERGEDAILY(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/mergegpm/gpm_diario'

    @property 
    def PATH_FIGURAS_MERGE_CLIM(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/mergegpm/gpm_clim'
    
    @property 
    def PATH_FIGURAS_CPC(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/cpc/cpc_diario'
    
    @property 
    def PATH_FIGURAS_CPC_CLIM(self):
        return '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS/cpc/cpc_clim'
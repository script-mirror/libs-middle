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
    logger.warning(".env nao encontrado no path home, usando load_dotenv() default")

class Constants:
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
        return os.getenv('URL_HTML_TO_IMAGE')

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
    def BASE_URL(self):
        return "https://tradingenergiarz.com"

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
    
    @property
    def PATH_ARQUIVOS(self):
        return '/projetos/arquivos'
    
    @property
    def PATH_ARQUIVOS_TEMP(self):
        return self.PATH_ARQUIVOS + '/temp'

    @property
    def PATH_PROJETO(self):
        return "/WX2TB/Documentos/fontes/PMO"

    @property
    def PATH_PROJETOS(self):
        return os.getenv('PATH_PROJETOS', '/projetos')

    @property
    def PATH_PREVS_PROSPEC(self):
        return '/projetos/arquivos/prospec/prevs'

    @property
    def PATH_RESULTS_PROSPEC(self):
        return '/projetos/arquivos/prospec/resultados'

    @property
    def PATH_PREVS_INTERNO(self):
        return '/projetos/arquivos/prospec/prevs/raizen'
    
    @property
    def PATH_TOKEN(self):
        return os.path.expanduser("~")

    @property
    def ATIVAR_ENV(self):
        return " . /projetos/env/bin/activate;"
    
    @property
    def RUN_STUDY_PROSPEC(self):
        return ' . /WX/WX2TB/Documentos/fontes/PMO/scripts_unificados/env/bin/activate; python /projetos/estudos-middle/estudos_prospec/rodada_automatica_prospec/main_roda_estudos.py '
    
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
    def LOGO_RAIZEN(self):
        return '/projetos/arquivos/meteorologia/raizen-logo.png' # './tmp/raizen-logo.png'

    @property 
    def PATH_SUBBACIAS_JSON(self):
        return '/projetos/arquivos/meteorologia/subbacias.json'
    
    @property 
    def PATH_HINDCAST_ECMWF_EST(self):
        return './tmp/data'

    @property 
    def PATH_HINDCAST_GEFS_EST(self):
        return './tmp/data'
    
    @property 
    def PATH_FTP_ECMWF(self):
        return '/ftp/files_sftp/ECMWF'
    
    @property 
    def PATH_CLIMATOLOGIA_MERGE(self):
        return '/WX2TB/Documentos/dados/merge-climatologia'
    
    @property 
    def PATH_SAVE_FIGS_METEOROLOGIA(self):
        return './tmp/plots' # '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS'
    
    @property 
    def PATH_DOWNLOAD_ARQUIVOS_METEOROLOGIA(self):
        return './tmp/downloads' # '/WX2TB/Documentos/saidas-modelos/NOVAS_FIGURAS'
    
    @property 
    def PATH_CLIMATOLOGIA_SAMET(self):
        return '/WX2TB/Documentos/dados/temp_samet/climatologia/'

    @property 
    def PATH_COORDENADAS_CIDADES(self):
        return '/projetos/arquivos/meteorologia/' # '/WX2TB/Documentos/fontes/tempo/novos_produtos/COORDENADAS_CIDADES/'
    
    @property 
    def PATH_TO_SAVE_TXT_SAMET(self):
        return './tmp/plots' # '/WX2TB/Documentos/saidas-modelos-novo/samet'
    
    @property 
    def PATH_CLIMATOLOGIA_TEMPERATURA_PONTUAL(self):
        return '/projetos/arquivos/meteorologia/' # '/WX2TB/Documentos/saidas-modelos-novo/samet/WX/WX2TB/Documentos/fontes/tempo/novos_produtos/CLIMATOLOGIA_TEMPERATURAS'
    
    @property 
    def PATH_CLIMATOLOGIA_UV100(self):
        return '/projetos/arquivos/meteorologia/' # '/WX2TB/Documentos/dados/UVCLIM/'
     

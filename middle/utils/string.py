"""Utility functions for text processing and data sanitization."""

import re
import unicodedata
from .logger import setup_logger
import datetime

logger = setup_logger()
MESES = {
    'janeiro': 1,
    'fevereiro': 2,
    'marco': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12
}

def sanitize_string(text: str, custom_chars:str="", space_char: str = " ") -> str:
    """
    Sanitiza uma string removendo caracteres especiais e normalizando o texto.

    Args:
        text (str): Texto a ser sanitizado
        custom_chars (str): Caracteres adicionais permitidos

    Returns:
        str: String sanitizada
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()

    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    text = text.lower()

    allowed_chars = r'a-zA-Z0-9'
    allowed_chars += r'\s'
    if custom_chars:
        allowed_chars += re.escape(custom_chars)

    text = re.sub(f'[^{allowed_chars}]', '', text)
    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'_+', '_', text)

    text = text.strip('_')
    text= text.replace(' ', space_char)

    return text



def remover_acentos_e_caracteres_especiais(texto: str):
    texto_norm = unicodedata.normalize('NFD', texto)
    texto_limpo = re.sub(r'[^\w\s]', '', texto_norm)
    texto_limpo = re.sub(r'\W+', '_', texto_limpo)
    return texto_limpo


def extrair_mes_ano(texto: str) -> datetime.date:
    """
    Extrai padrão mês/ano de uma string
    """
    pattern = r'(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\/\d{4}'
    
    match = re.search(pattern, texto.replace('ç', 'c'), re.IGNORECASE)
    
    if match:
        MESES
        mes_ano = match.group(0).split('/')
        return datetime.date(
            year=int(mes_ano[1]),
            month=MESES[mes_ano[0].lower()],
            day=1
        )
        
    return None

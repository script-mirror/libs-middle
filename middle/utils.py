"""Utility functions for text processing and data sanitization."""

import re
import unicodedata


def sanitize_string(text, custom_chars=""):
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

    return text.upper()

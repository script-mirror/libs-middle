import logging
import os
import sys
class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[37m',    # Branco
        'INFO': '\033[36m',     # Ciano
        'WARNING': '\033[33m',  # Amarelo
        'ERROR': '\033[31m',    # Vermelho
        'CRITICAL': '\033[41m', # Fundo vermelho
    }
    RESET = '\033[0m'

    def format(self, record):
        message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        colored_level = f"{color}{record.levelname}{self.RESET}"
        return message.replace(record.levelname, colored_level, 1)


def setup_logger(log_path: str = None, external_logger=None):
    if external_logger:
        return external_logger

    logger_name = log_path.replace("\\", "/").split("/")[-1] if log_path else "default_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    base_format = '%(levelname)s:\t%(asctime)s\t %(message)s'
    plain_formatter = logging.Formatter(base_format)
    color_formatter = ColorFormatter(base_format)

    if logger.hasHandlers():
        logger.handlers.clear()
    if not logger.handlers:
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            fh = logging.FileHandler(log_path, mode='w')
            fh.setFormatter(plain_formatter)
            logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(color_formatter)
        logger.addHandler(sh)

    return logger

# criar logging sem propagar para o log raiz
def criar_logger(nome_logger, caminho_arquivo):
    nivel = logging.INFO
    console = True
    diretorio = os.path.dirname(caminho_arquivo) or '.'
    os.makedirs(diretorio, exist_ok=True)
    logger = logging.getLogger(nome_logger)
    logger.setLevel(nivel)
    logger.handlers.clear()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(caminho_arquivo, mode='w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    
    # não propaga para o log raiz
    logger.propagate = False   
    
    return logger
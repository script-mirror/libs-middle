import logging
import os


def setup_logger(log_path: str = None):
    # Use um nome fixo para o logger ao invés do caminho do arquivo
    logger_name = "app_logger" if log_path else "default_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Desabilita propagação para evitar duplicação com loggers pais
    logger.propagate = False
    
    formatter = logging.Formatter('%(levelname)s:\t%(asctime)s\t %(message)s')
    # Remove handlers duplicados
    if logger.hasHandlers():
        logger.handlers.clear()
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = logging.FileHandler(log_path, mode='w')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger

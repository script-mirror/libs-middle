import logging
import os

logger = None

def setup_logger(log_path: str = None):
    global logger
    logger = logging.getLogger(log_path if log_path else "default_logger")
    logger.setLevel(logging.INFO)
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

import logging
import os


def setup_logger(log_path: str):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger(log_path)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # Remove handlers duplicados
    if logger.hasHandlers():
        logger.handlers.clear()
    fh = logging.FileHandler(log_path, mode='w')
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

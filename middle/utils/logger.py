import logging
import os


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
        return f"{color}{message}{self.RESET}"


def setup_logger(log_path: str = None):
    logger_name = "app_logger" if log_path else "default_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    base_format = '%(levelname)s:\t%(asctime)s\t %(message)s'
    plain_formatter = logging.Formatter(base_format)
    color_formatter = ColorFormatter(base_format)

    if logger.hasHandlers():
        logger.handlers.clear()

    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = logging.FileHandler(log_path, mode='w')
        fh.setFormatter(plain_formatter)
        logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(color_formatter)
    logger.addHandler(sh)

    return logger

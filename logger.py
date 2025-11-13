import sys
import logging
import colorlog

def setup_logger(level=logging.ERROR):

    logger = logging.getLogger()

    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger.setLevel(level)
    if logger.hasHandlers():
        return logger
    handler = colorlog.StreamHandler(sys.stdout)

    log_format = (
        '%(log_color)s%(levelname)-8s '
        '%(asctime)s | '
        '%(module)s:%(funcName)s:%(lineno)d - '
        '%(message)s'
    )
    formatter = colorlog.ColoredFormatter(
        log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()

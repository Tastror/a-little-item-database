import sys
import logging
import colorlog

def setup_logger(level=logging.ERROR):

    logger = logging.getLogger()

    # logging.DEBUG,
    # logging.INFO,
    # logging.WARNING,
    # logging.ERROR,
    # logging.CRITICAL
    logger.setLevel(level)
    if logger.hasHandlers():
        return logger
    handler = colorlog.StreamHandler(sys.stdout)

    # %(log_color)s 是 colorlog 特有的，用来添加颜色
    # %(levelname)-8s: 级别名，左对齐，占8个字符
    # %(asctime)s: 时间
    # %(module)s: 模块名
    # %(funcName)s: 函数名
    # %(lineno)d: 行号
    # %(message)s: 日志信息
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

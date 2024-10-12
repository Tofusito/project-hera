# app/utils/logger.py

import logging

def setup_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

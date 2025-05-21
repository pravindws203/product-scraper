# logger_config.py
import logging
import os

def setup_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    os.makedirs('logs', exist_ok=True)
    if not logger.handlers:  # Avoid duplicate handlers
        handler = logging.FileHandler(f"logs/{filename}", mode="a")
        formatter = logging.Formatter('%(asctime)s --|-- %(name)s --|-- %(levelname)s --|--  %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

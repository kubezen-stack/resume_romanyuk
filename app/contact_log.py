import json
import logging
import os


class StrictFileHandler(logging.FileHandler):
    def handleError(self, record):
        raise


def _get_logger(path):
    logger = logging.getLogger(f"contact_form:{path}")
    if not logger.handlers:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = StrictFileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_contact(path, data):
    _get_logger(path).info(json.dumps(data, ensure_ascii=False))

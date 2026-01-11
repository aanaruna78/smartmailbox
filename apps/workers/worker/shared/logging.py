import logging
import sys
from pythonjsonlogger import jsonlogger
from worker.config import settings

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"}
    )
    handler.setFormatter(formatter)
    
    logger.handlers = []
    logger.addHandler(handler)

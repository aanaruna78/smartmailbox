import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"}
    )
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplication
    logger.handlers = []
    logger.addHandler(handler)
    
    # Set level for specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

import logging
import sys
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from config.settings import config

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'extra'):
            log_object.update(record.extra)
        
        if record.exc_info:
            log_object['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_object)

def setup_logger(name: str = __name__) -> logging.Logger:
    """Setup logger with console and file handlers"""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.LOG_FILE:
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Global logger instance
logger = setup_logger("self_healing_agent")
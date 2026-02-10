import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class Logger:
    """Production-grade structured logger"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        
        file_handler = RotatingFileHandler(
            self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        
        error_handler = RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, **kwargs: Any):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any):
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs: Any):
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs: Any):
        self.logger.critical(message, extra=kwargs)


logger = Logger("telegram_saas")

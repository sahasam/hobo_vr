"""Server lol."""
import logging
import os
from . import server

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_path = os.path.join(os.path.dirname(__file__), "../logs/server.log")
logger_handler = logging.FileHandler(log_path)
logger_handler.setLevel(logging.DEBUG)

console_logger_handler = logging.StreamHandler()
console_logger_handler.setLevel(logging.INFO)

logger_formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s - %(message)s')

logger_handler.setFormatter(logger_formatter)
console_logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)
logger.addHandler(console_logger_handler)

__version__ = "0.1"

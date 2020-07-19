"""Server lol."""
import logging
from . import server

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger_handler = logging.FileHandler(filename="./virtualreality/logs/server.log")
logger_handler.setLevel(logging.DEBUG)

logger_formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s - %(message)s')

logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)


__version__ = "0.1"

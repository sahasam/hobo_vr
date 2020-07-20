"""Virtual reality tools and drivers for python."""
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
 
#logfile
log_file = os.path.join(os.path.dirname(__file__), "../logs/app.log")
logger_handler = logging.FileHandler(log_file)
logger_handler.setLevel(logging.DEBUG)

#logging entry format
logger_formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s - %(message)s')

logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)


from . import util
from . import templates

__version__ = "0.1"

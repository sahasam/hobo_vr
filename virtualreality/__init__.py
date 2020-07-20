"""Virtual reality tools and drivers for python."""
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger_handler = logging.FileHandler(os.path.join(__file__, "../logs/app.log"))
logger_handler.setLevel(logging.DEBUG)

logger_formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s - %(message)s')

logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)


from . import util
from . import templates

__version__ = "0.1"

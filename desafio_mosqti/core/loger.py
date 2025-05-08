import sys
import time

import loguru

logger = loguru.logger
logger.remove()


logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <level>{extra}</level>",
    level="DEBUG",
    colorize=True,
)

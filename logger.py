from logging.config import dictConfig
from pathlib import Path

from yaml import safe_load


def setup_logger():
    here = Path(__file__).parent
    with open(here / 'logger.yaml', 'r') as f:
        config = safe_load(f.read())
        dictConfig(config)


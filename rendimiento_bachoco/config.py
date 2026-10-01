from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

import os

# Load environment variables from .env file if it exists
load_dotenv()

INEGI_API_KEY = os.getenv('INEGI_API_KEY')

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"La ruta de PROJ_ROOT es: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

REFERENCES_DIR = PROJ_ROOT / "references"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

TICKERS_YAHOO = ["MINSAB.MX", "GRUMAB.MX"]
INDICATORS_INEGI = ['6207077700', '6207077710', '6207077719', '6207077733',
                          '6207077741', '6207077743', '6207077748', '6207129563',
                          '6207129580', '6207129584', '6207129594','6207129595',
                          '6207129600','6207129608','6207129609', '6207095692',
                          '6207095711','6207095719','6207129821']

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass

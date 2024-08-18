from utils import load_tomldata
from pathlib import Path
from loguru import logger

CONFIG_PATH = Path(".github/configs/versions.tomls")

def main():
    config_data = load_tomldata(CONFIG_PATH)
    logger.debug(config_data)

main()

import os
from utils import setup_dir, paratranz_get_artifact_info
from pathlib import Path
from loguru import logger

# GH Action
CI = os.environ.get("CI")
# ParaTranz ENVs
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")
# Path ENVs
CACHE_FOLDER_PATH = Path(".cache")
CACHE_FILE_PATH = CACHE_FOLDER_PATH.joinpath("paratranz_cache.txt")

def paratranz_write_cache(artifact_data: dict):
    data_value = artifact_data["id"]
    if not CACHE_FILE_PATH.exists():
        logger.info("Cache file is missing, create one.")
        CACHE_FILE_PATH.write_text(str(data_value))
        return False
    else:
        cache_value = int(CACHE_FILE_PATH.read_text().strip())
        if cache_value == data_value:
            logger.info("Cache file is same as data!")
        else:
            logger.info("Cache file is not same as data, overwrite!")
            CACHE_FILE_PATH.write_text(str(data_value))

def main():
    setup_dir(CACHE_FOLDER_PATH, "Cache")
    artifact_info = paratranz_get_artifact_info(API_TOKEN, PROJECT_ID)
    paratranz_write_cache(artifact_info)

main()
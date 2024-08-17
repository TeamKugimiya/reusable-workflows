import os
import sys
import json
import shutil
import requests
from pathlib import Path
from loguru import logger

# GH Action
CI = os.environ.get("CI")
# ParaTranz ENVs
API_URL = "https://paratranz.cn/api"
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")
# Path ENVs
WORKDIR_PATH = Path(".workdir")
CACHE_FOLDER_PATH = Path(".cache")
CACHE_FILE_PATH = CACHE_FOLDER_PATH.joinpath("paratranz_cache.txt")

def setup_dirs():
    if not CACHE_FOLDER_PATH.exists():
        logger.debug("Create cache folder")
        CACHE_FOLDER_PATH.mkdir()
    else:
        logger.debug("Cache folder exists!")
    if not WORKDIR_PATH.exists():
        logger.debug("Create workdir folder")
        WORKDIR_PATH.mkdir()
    else:
        logger.debug("Workdir folder exists!")

def paratranz_get_artifact_info():
    headers = {
        "Authorization": f"{API_TOKEN}",
        "User-Agent": "ParaTranslationPack GitHub Action Script | Made by Efina"
    }
    response = requests.get(f"{API_URL}/projects/{PROJECT_ID}/artifacts", headers=headers)

    if response.ok:
        data = json.loads(response.content)
        logger.debug(data)
        return data
    else:
        logger.warning("Response error: " + str(response.status_code))
        sys.exit(1)

def paratranz_check_artifact(artifact_data: dict):
    data_value = artifact_data["id"]
    if not CACHE_FILE_PATH.exists():
        CACHE_FILE_PATH.write_text(str(data_value))
        return False
    else:
        cache_value = int(CACHE_FILE_PATH.read_text().strip())
        if cache_value == data_value:
            return True
        else:
            CACHE_FILE_PATH.write_text(str(data_value))
            return False

def main():
    setup_dirs()
    artifact_info = paratranz_get_artifact_info()
    aritfact_same = paratranz_check_artifact(artifact_info)
    if CI:
        with open(os.environ["GITHUB_OUTPUT"], "a") as out_file:
            out_file.write(f"ARITFACT_SAME={aritfact_same}\n")
            out_file.close()

main()
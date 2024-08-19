import os
import sys
import requests
from utils import setup_dir
from pathlib import Path
from loguru import logger

# ParaTranz ENVs
API_URL = "https://paratranz.cn/api"
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")
# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")
WORKDIR_FILE_PATH = WORKDIR_FOLDER_PATH.joinpath("para_translation_artifact.zip")

def paratranz_artifact_download():
    headers = {
        "Authorization": f"{API_TOKEN}",
        "User-Agent": "ModsTranslationPack GitHub Action Script | Made by @xMikux"
    }
    response = requests.get(f"{API_URL}/projects/{PROJECT_ID}/artifacts/download", headers=headers)

    if response.ok:
        logger.info("Downloading artifact...")

        with open(WORKDIR_FILE_PATH, "wb") as file:
            file.write(response.content)
        logger.success("Download Success!")
    else:
        logger.error(f"Download Failed! Error: {str(response.status_code)}")
        sys.exit(1)

def main():
    setup_dir(WORKDIR_FOLDER_PATH, "workdir")
    paratranz_artifact_download()

main()

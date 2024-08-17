import os
import sys
import requests
from pathlib import Path
from loguru import logger
from datetime import datetime

# ParaTranz ENVs
API_URL = "https://paratranz.cn/api"
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")

def paratranz_get_artifact_info():
    headers = {
        "Authorization": f"{API_TOKEN}",
        "User-Agent": "ParaTranslationPack GitHub Action Script | Made by Efina"
    }
    response = requests.get(f"{API_URL}/projects/{PROJECT_ID}/artifacts", headers=headers)

    if response.ok:
        data = response.json()
        logger.debug(data)
        return data
    else:
        logger.error("Response error: " + str(response.status_code))
        sys.exit(1)

def convert_epoch(artifact_data: dict) -> int:
    iso_timestamp = artifact_data["createdAt"]
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    epoch_time = dt.timestamp()
    return epoch_time

def fix_file_date(artifact_data: dict):
    generate_time_epoch = (int(convert_epoch(artifact_data)), int(convert_epoch(artifact_data)))
    workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

    for i in workdir_path:
        logger.debug(i.stat())
        os.utime(i, generate_time_epoch)
        logger.debug(i.stat())
        logger.info(f"Fixed {i.parts[4]}.")

def main():
    artifact_info = paratranz_get_artifact_info()
    fix_file_date(artifact_info)

main()

import sys
import json
import tomllib
import requests
from pathlib import Path
from loguru import logger

# ParaTranz ENVs
API_URL = "https://paratranz.cn/api"

## Common Utility ##
def setup_dir(path: Path, path_name: str):
    if not path.exists():
        logger.info(f"Create {path_name} folder")
        path.mkdir()
    else:
        logger.info(f"{path_name} folder exists!")

def load_tomldata(path: Path) -> dict:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            return data
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        logger.error(f"Reading toml cause error: {e}")
        sys.exit(1)

## ParaTranz Utility ##
def paratranz_get_artifact_info(api_token: str, project_id: int) -> dict:
    headers = {
        "Authorization": f"{api_token}",
        "User-Agent": "ParaTranslationPack GitHub Action Script | Made by Efina"
    }
    response = requests.get(f"{API_URL}/projects/{project_id}/artifacts", headers=headers)

    if response.ok:
        data = json.loads(response.content)
        logger.debug(data)
        return data
    else:
        logger.error("Response error: " + str(response.status_code))
        sys.exit(1)

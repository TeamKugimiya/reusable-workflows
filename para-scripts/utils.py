import os
import sys
import json
import tomllib
import requests
from pathlib import Path
from loguru import logger

## ParaTranz ENVs
API_URL = "https://paratranz.cn/api"

### Common Utility ###
def setup_dir(path: Path, path_name: str):
    if not path.exists():
        logger.info(f"Create {path_name} folder")
        path.mkdir(parents=True)
    else:
        logger.info(f"{path_name} folder exists!")

def load_tomldata(path: Path) -> dict:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            logger.debug(data)
            return data
    except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
        logger.error(f"Reading toml cause error: {e}")
        sys.exit(1)

def load_jsondata(path: Path) -> dict:
    try:
        with open(path, "rb") as f:
            data = json.load(f)
            logger.debug(data)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Reading json cause error: {e}")
        sys.exit(1)

### ParaTranz Utility ###
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

### GitHub Utility ###
def github_write_step_output(step_output_name: str, data: str):
    github_step_output_env = os.environ.get("GITHUB_OUTPUT")

    if github_step_output_env is None:
        logger.error("GITHUB_OUTPUT environment variable is not set!")
        sys.exit(1)

    github_step_output_path = Path(github_step_output_env)

    try:
        with github_step_output_path.open("a") as output_file:
            output_file.write(f"{step_output_name}={data}")
            output_file.close()
    except Exception as e:
        logger.error(f"Failed to write to GITHUB_OUTPUT: {e}")
        sys.exit(1)

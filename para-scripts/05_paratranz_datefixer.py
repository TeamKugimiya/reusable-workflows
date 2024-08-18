import os
import json
import hashlib
from utils import setup_dir, load_jsondata, paratranz_get_artifact_info
from pathlib import Path
from loguru import logger
from datetime import datetime

# ParaTranz ENVs
API_URL = "https://paratranz.cn/api"
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")
FILE_CACHE_PATH = Path(".cache/paratranz_files_cache.json")

def convert_epoch(timestamp: str) -> int:
    iso_timestamp = timestamp
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    epoch_time = dt.timestamp()
    return epoch_time

def calculate_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clean_cache(cache: dict) -> dict:
    keys_to_delete = [i for i in cache["hashes"] if not Path(i).exists()]
    for key in keys_to_delete:
        del cache["hashes"][key]
    logger.debug(cache)
    return cache

def save_cache(cache: dict):
    json_data = json.dump(cache, f, sort_keys=True)
    logger.debug(json_data)
    with FILE_CACHE_PATH.open("w") as f:
        json.dump(cache, f, sort_keys=True)

def fix_file_date(artifact_data: str):
    generate_time_epoch = (int(convert_epoch(artifact_data)), int(convert_epoch(artifact_data)))
    workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

    if FILE_CACHE_PATH.exists():
        cache_data = clean_cache(load_jsondata(FILE_CACHE_PATH))
    else:
        cache_data = {"hashes": {}}

    for file_path in workdir_path:
        file_hash = calculate_hash(file_path)
        cached_info = cache_data["hashes"].get(str(file_path))

        if cached_info and cached_info["hash"] == file_hash:
            os.utime(file_path, (cached_info["utime"], cached_info["utime"]))
            logger.success(f"Used cached utime for {file_path.parts[4]}.")
        else:
            os.utime(file_path, generate_time_epoch)
            cache_data["hashes"][str(file_path)] = {
                "hash": file_hash,
                "utime": generate_time_epoch[0]
            }
            logger.success(f"Updated utime for {file_path.parts[4]}.")
        logger.debug(file_path.stat())

    save_cache(cache_data)

def main():
    setup_dir(FILE_CACHE_PATH.parents[0], "Cache")
    artifact_info = paratranz_get_artifact_info(API_TOKEN, PROJECT_ID)
    fix_file_date(artifact_info["createdAt"])

main()

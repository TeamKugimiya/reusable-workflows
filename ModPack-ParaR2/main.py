import os
import sys
import shutil
from pathlib import Path
from loguru import logger
from pooch import retrieve, HTTPDownloader, Unzip

PROJECT_ID = os.getenv("PROJECT_ID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
API_URL = f"https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts/download"
HEADERS = {
    "Authorization": f"{AUTH_TOKEN}",
    "User-Agent": "GitHub Action Script | Made by @xMikux"
}

### 下載並解壓縮資料
DATA_PATH = Path("data")

logger.info("Checking environment variables...")
if not PROJECT_ID or not AUTH_TOKEN:
    logger.error("PROJECT_ID or AUTH_TOKEN environment variable is not set.")
    sys.exit(1)

try:
    logger.info(f"Downloading artifact and extract to {DATA_PATH.absolute()}...")
    retrieve(
        API_URL,
        known_hash=None,
        processor=Unzip(extract_dir=DATA_PATH.absolute()),
        downloader=HTTPDownloader(headers=HEADERS)
    )
    logger.success("Download Success!")
except Exception as e:
    logger.error(f"Download Failed! Error: {str(e)}")
    sys.exit(1)

### 移動資料夾
PACK_FORMAT = int(os.getenv("PACK_FORMAT"))
PACK_DESCRIPTION = os.getenv("PACK_DESCRIPTION")

if not PACK_FORMAT:
    logger.error("PACK_FORMAT environment variable is not set.")
    sys.exit(1)

WORKDIR = Path("workdir")
logger.info("Creating workdir...")
WORKDIR.mkdir()

logger.info("Moving assets to workdir...")
DATA_ASSETS_PATH = DATA_PATH.joinpath("utf8/assets")
shutil.move(DATA_ASSETS_PATH, WORKDIR)

logger.info("Deleting data folder...")
shutil.rmtree(DATA_PATH)

### 生成 pack.mcmeta
logger.info("Creating pack.mcmeta...")
PACK_PATH = WORKDIR.joinpath("pack.mcmeta")
data_mcmeta = {
  "pack": {
    "pack_format": PACK_FORMAT,
    "description": PACK_DESCRIPTION
  }
}
PACK_PATH.write_text(str(data_mcmeta))
